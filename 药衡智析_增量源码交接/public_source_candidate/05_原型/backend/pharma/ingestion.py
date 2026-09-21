"""Immutable CSV snapshots. Validation precedes an atomic current-manifest swap."""
from __future__ import annotations
import csv
import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

from .config import ROOT, RUNTIME, PACKAGE

VERSION = 'data-contract-2-finite'
ORIGINAL = PACKAGE if os.environ.get('PHARMA_DATA_PACKAGE') else ROOT / '01_数据/00_原始'
SNAPSHOTS = RUNTIME / 'data'
D = Decimal
def _competition_configuration():
    """赛题正式配置目录在仓库内的位置（可被环境变量整体重定向）。"""
    return Path(os.environ.get('PHARMA_COMPETITION_CONFIG_DIR', str(ROOT / 'competition_configuration')))

def source_contract():
    """Public schema stays fixed; only trusted local enterprise masterdata varies."""
    value=json.loads((ROOT / '05_原型/industry_packs/pharmaceutical/source_contract.json').read_text())
    # 默认解析仓库内赛题主数据（中药一厂/二厂口径）：没有环境变量时正式
    # 制药管线同样可用，部署不再依赖外部绝对路径（配置生效修复）。
    configured=os.getenv('PHARMA_PRIVATE_MASTERDATA_FILE') or ''
    if not configured:
        default=_competition_configuration()/'pharmaceutical_masterdata.json'
        configured=str(default) if default.is_file() else ''
    if configured:
        path=Path(configured)
        if path.suffix.lower()!='.json' or path.stat().st_size>1_000_000:raise ValueError('INVALID_MASTERDATA_FILE')
        master=json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(master,dict) or set(master)!={'specifications','factories'}:raise ValueError('INVALID_MASTERDATA_SHAPE')
        value={**value,**master}
    factories=value['factories'];specs=value['specifications']
    if not isinstance(factories,list) or not factories or any(not isinstance(x,str) or not x.strip() for x in factories) or len(set(factories))!=len(factories):
        raise ValueError('INVALID_MASTERDATA_FACTORIES')
    if not isinstance(specs,dict) or not specs:raise ValueError('INVALID_MASTERDATA_SPECIFICATIONS')
    for product,spec in specs.items():
        if not isinstance(product,str) or not product.strip() or not isinstance(spec,list) or len(spec)!=4:
            raise ValueError('INVALID_MASTERDATA_SPECIFICATION')
        if any(not isinstance(spec[i],str) or not spec[i].strip() for i in (0,2,3)) or type(spec[1]) is not int or spec[1]<=0:
            raise ValueError('INVALID_MASTERDATA_SPECIFICATION')
    return value


def source_contract_hash():
    return hashlib.sha256(json.dumps(source_contract(),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


_CONTRACT = source_contract()
COMMON = _CONTRACT['common']
FIELDS = _CONTRACT['fields']


def _hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect_zip(path):
    """Inspect repaired names without extracting or modifying the original archive."""
    names, entries, total = set(), [], 0
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            original = info.filename
            try:
                repaired = original.encode('cp437').decode('utf-8') if not info.flag_bits & 0x800 else original
            except (UnicodeError, ValueError):
                repaired = original
            parts = PurePosixPath(repaired.replace('\\', '/')).parts
            excluded = any(p in ('__MACOSX', '.DS_Store') or p.startswith('._') for p in parts)
            total += info.file_size
            if (repaired.startswith(('/', '\\')) or '..' in parts or any(':' in p for p in parts)
                    or stat.S_ISLNK(info.external_attr >> 16) or repaired in names
                    or info.file_size > 100_000_000 or total > 500_000_000
                    or info.file_size / max(1, info.compress_size) > 1000):
                raise ValueError('UNSAFE_ARCHIVE_ENTRY')
            names.add(repaired)
            entries.append({'original': original, 'repaired': repaired, 'excluded': excluded,
                            'size': info.file_size, 'crc': info.CRC})
    return {'file': str(path), 'sha256': _hash(path), 'entries': entries, 'uncompressed_bytes': total}


def _kind(name):
    for word, kind in [('成本汇总', 'cost'), ('预算数据', 'budget'), ('原材料消耗', 'materials'),
                       ('制造费用明细', 'expenses'), ('人工工时', 'labor'), ('行业成本', 'industry'),
                       ('药材市场', 'market')]:
        if word in name:
            return kind
    raise ValueError('UNKNOWN_DATA_FILE: ' + name)


def _read(source):
    records, files, errors = [], [], []
    for path in sorted(Path(source).rglob('*.csv')):
        raw_hash = _hash(path)
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            if not fields or len(fields) != len(set(fields)):
                errors.append({'file': path.name, 'error': 'INVALID_HEADERS'})
            kind = _kind(path.name)
            if set(fields or []) != set(FIELDS[kind]):
                errors.append({'file':path.name,'error':'SCHEMA_CONFLICT','expected':FIELDS[kind],'actual':fields})
            count = 0
            for i, row in enumerate(reader, 2):
                count += 1
                if None in row or any(v is None or not v.strip() for v in row.values()):
                    errors.append({'file': path.name, 'line': i, 'error': 'MISSING_OR_EXTRA_FIELDS'})
                records.append({'kind': kind, 'factory': row.get('工厂', ''), 'product': row.get('产品名称', ''),
                                'month': row.get('月份', ''), 'row_key': f'{path.name}:{i}',
                                'source_hash': raw_hash, 'data': row})
        files.append({'path': str(path.relative_to(source)), 'sha256': raw_hash, 'rows': count,
                      'encoding': 'UTF-8 BOM' if path.read_bytes().startswith(b'\xef\xbb\xbf') else 'UTF-8', 'fields': fields})
    return records, files, errors


def audit(records, errors=None):
    contract=source_contract()
    errors = list(errors or [])
    groups = defaultdict(lambda: {'observations': 0, 'failures': []})
    def check(group, actual, expected, row, tolerance=D('0.000001')):
        groups[group]['observations'] += 1
        if abs(actual - expected) > tolerance:
            failure = {'row_key': row['row_key'], 'actual': str(actual), 'expected': str(expected), 'tolerance': str(tolerance)}
            groups[group]['failures'].append(failure)
            errors.append({'group': group, **failure})
    # Validate every numeric source value before Decimal arithmetic. Infinity is
    # ordered and previously passed the non-negative check; NaN can raise.
    for row in records:
        for field, raw in row['data'].items():
            numeric = ('(' in field or field.endswith('月价格') or field in
                       ('行业P25', '行业P50', '行业P75', '占总材料成本比例'))
            if not numeric:
                continue
            try:
                value = D(str(raw).rstrip('%'))
                if not value.is_finite():
                    errors.append({'row_key': row['row_key'], 'field': field, 'error': 'NON_FINITE_NUMBER'})
                elif value < 0 and row['kind'] != 'industry':
                    errors.append({'row_key': row['row_key'], 'field': field, 'error': 'NEGATIVE_INPUT'})
            except (ValueError, ArithmeticError):
                errors.append({'row_key': row['row_key'], 'field': field, 'error': 'INVALID_NUMBER'})
    if errors:
        return {'status': 'INVALID', 'errors': errors, 'arithmetic_groups': {},
                'arithmetic_observations': 0, 'continuity_groups': 0, 'continuity_failures': []}
    costs = {(r['factory'], r['product'], r['month']): r for r in records if r['kind'] == 'cost'}
    keys = set()
    continuity = defaultdict(set)
    for r in records:
        x, kind = r['data'], r['kind']
        specs = {product: values[0] for product, values in contract['specifications'].items()}
        if kind in ('cost','budget','materials','expenses','labor') and (r['factory'] not in contract['factories'] or x.get('产品规格') != specs.get(r['product'])):
            errors.append({'row_key':r['row_key'],'error':'UNKNOWN_FACTORY_PRODUCT_OR_SPECIFICATION'})
        extra = x.get('原材料名称', x.get('费用类别', x.get('指标', x.get('药材名称', ''))))
        key = (kind, r['factory'], r['product'], r['month'], x.get('产品类别', ''), extra)
        if key in keys:
            errors.append({'row_key': r['row_key'], 'error': 'DUPLICATE_PRIMARY_KEY'})
        keys.add(key)
        if r['month']:
            try:
                dt = datetime.strptime(r['month'], '%Y-%m')
                continuity[(kind, r['factory'], r['product'], dt.year, extra)].add(dt.month)
            except ValueError:
                errors.append({'row_key': r['row_key'], 'error': 'INVALID_MONTH'})
        numeric = [k for k in x if '(' in k and k not in ('本厂水平(中药一厂)',) or k.endswith('月价格')]
        for k in numeric:
            try:
                if D(x[k]) < 0:
                    errors.append({'row_key': r['row_key'], 'error': 'NEGATIVE_INPUT', 'field': k})
            except Exception:
                errors.append({'row_key': r['row_key'], 'error': 'INVALID_NUMBER', 'field': k})
        if kind == 'industry':
            try:
                quantiles = [D(x[k].rstrip('%')) for k in ('行业P25','行业P50','行业P75')]
                company = D(x['本厂水平(中药一厂)'].rstrip('%'))
                if not all(v.is_finite() for v in quantiles + [company]) or quantiles != sorted(quantiles):
                    errors.append({'row_key':r['row_key'],'error':'INVALID_INDUSTRY_QUANTILES'})
            except Exception:
                errors.append({'row_key':r['row_key'],'error':'INVALID_INDUSTRY_NUMBER'})
        if kind in ('cost', 'budget'):
            prefix = '预算' if kind == 'budget' else ''
            check(kind + '_unit_sum', sum(D(x[prefix + e + '(元/盒)']) for e in ('直接材料','直接人工','制造费用')), D(x[prefix+'单位成本(元/盒)']), r)
            check(kind + '_total', D(x[prefix+'产量(盒)']) * D(x[prefix+'单位成本(元/盒)']), D(x[prefix+'总成本(元)']), r)
        if kind in ('materials', 'expenses', 'labor'):
            parent = costs.get((r['factory'], r['product'], r['month']))
            if not parent:
                errors.append({'row_key': r['row_key'], 'error': 'MISSING_PARENT'})
                continue
            p = parent['data']
            check(kind+'_quantity_join', D(x['产量(盒)']), D(p['产量(盒)']), r)
            if kind == 'materials':
                check('materials_total', D(x['单位消耗成本(元/盒)'])*D(x['产量(盒)']), D(x['原材料总成本(元)']), r)
                share = D(x['占总材料成本比例'].rstrip('%'))
                precision = max(0, -share.as_tuple().exponent)
                check('materials_share', D(x['单位消耗成本(元/盒)']) / D(p['直接材料(元/盒)'])*100, share, r, D(5).scaleb(-precision-1))
            elif kind == 'expenses':
                check('expenses_total', D(x['单位费用(元/盒)'])*D(x['产量(盒)']), D(x['费用总额(元)']), r)
            else:
                check('labor_total', D(x['直接人工总额(元)']), D(p['直接人工(元/盒)'])*D(p['产量(盒)']), r)
    for kind, unit_field, total_field, parent_field in [('materials','单位消耗成本(元/盒)','原材料总成本(元)','直接材料(元/盒)'), ('expenses','单位费用(元/盒)','费用总额(元)','制造费用(元/盒)')]:
        grouped = defaultdict(list)
        for r in records:
            if r['kind'] == kind:
                grouped[(r['factory'],r['product'],r['month'])].append(r)
        for key, rows in grouped.items():
            if key not in costs:
                continue
            p = costs[key]['data']
            if kind == 'materials':
                shares = [D(r['data']['占总材料成本比例'].rstrip('%')) for r in rows]
                tolerance = sum(D(5).scaleb(min(0, x.as_tuple().exponent)-1) for x in shares)
                check('materials_share_rollup', sum(shares), D(100), rows[0], tolerance)
            check(kind+'_unit_rollup', sum(D(r['data'][unit_field]) for r in rows), D(p[parent_field]), rows[0])
            check(kind+'_total_rollup', sum(D(r['data'][total_field]) for r in rows), D(p[parent_field])*D(p['产量(盒)']), rows[0])
    continuity_failures = []
    for key, months in continuity.items():
        if sorted(months) != list(range(min(months), max(months)+1)):
            continuity_failures.append({'group': list(key), 'months': sorted(months)})
    errors.extend(continuity_failures)
    return {'status': 'VALID' if not errors else 'INVALID', 'errors': errors, 'arithmetic_groups': dict(groups),
            'arithmetic_observations': sum(g['observations'] for g in groups.values()),
            'continuity_groups': len(continuity), 'continuity_failures': continuity_failures,
            'notes': ['8小时工时关系仅诊断假设，未作为失败规则', '金额Decimal；比例容差为该行展示最小精度的一半百分点']}


def ingest(source=None, destination=None):
    import duckdb
    source, destination = Path(source or ORIGINAL), Path(destination or SNAPSHOTS)
    contract_hash=source_contract_hash()
    records, files, errors = _read(source)
    # 二厂合成明细覆盖目录（2026-09-21 修复 #19）：题包只读不动，合成 CSV 并入
    # 同一数据管线（audit 精确校验），manifest 标注 synthetic，快照指纹随之变化。
    from .config import SYNTHETIC_DETAIL_DIR
    if SYNTHETIC_DETAIL_DIR is not None and Path(SYNTHETIC_DETAIL_DIR).is_dir():
        s_records, s_files, s_errors = _read(SYNTHETIC_DETAIL_DIR)
        records += s_records
        errors += s_errors
        files += [{**f, 'path': '合成明细/' + f['path'], 'synthetic': True} for f in s_files]
    if not records: errors.append({'error':'EMPTY_SOURCE_DATA'})
    version = hashlib.sha256(json.dumps([VERSION, files, contract_hash], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    destination.mkdir(parents=True, exist_ok=True)
    current = destination / 'current.json'
    if current.exists():
        existing = json.loads(current.read_text())
        if existing['snapshot_id'] == version and (destination / existing['parquet']).exists() and existing.get('parquet_hash') == _hash(destination / existing['parquet']):
            return existing
    try:
        result = audit(records, errors) if not errors else {'status':'INVALID','errors':errors}
    except (KeyError, ArithmeticError, ValueError) as exc:
        result = {'status':'INVALID','errors':[{'error':'INVALID_TYPED_DATA','detail':str(exc)}]}
    if source_contract_hash()!=contract_hash:raise ValueError('MASTERDATA_CHANGED_DURING_INGESTION')
    manifest = {**result, 'snapshot_id': version, 'contract_version': VERSION, 'masterdata_hash':contract_hash, 'row_count': len(records),
                'files': files, 'created_at': datetime.now(timezone.utc).isoformat(), 'parquet': version + '.parquet'}
    if result['status'] != 'VALID':
        (destination / ('rejected-' + version + '.json')).write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        raise ValueError('DATA_VALIDATION_FAILED: ' + str(len(result['errors'])))
    with tempfile.TemporaryDirectory(prefix='staging-', dir=destination) as temporary:
        temp = Path(temporary)
        rows = [{**{k:v for k,v in r.items() if k != 'data'}, 'data_json': json.dumps(r['data'], ensure_ascii=False)} for r in records]
        json_path = temp / 'rows.json'
        json_path.write_text(json.dumps(rows, ensure_ascii=False))
        con = duckdb.connect(':memory:')
        try:
            con.execute('CREATE TABLE staging AS SELECT * FROM read_json_auto(?)', [str(json_path)])
            # Output is generated internally, never supplied by an API caller.
            con.execute('COPY staging TO ? (FORMAT PARQUET)', [str(temp/'rows.parquet')])
        finally:
            con.close()
        manifest['parquet_hash'] = _hash(temp/'rows.parquet')
        os.replace(temp/'rows.parquet', destination / manifest['parquet'])
        (temp/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        os.replace(temp/'manifest.json', current)
    return manifest


def load_rows(destination=None):
    import duckdb
    destination = Path(destination or SNAPSHOTS)
    manifest = json.loads((destination/'current.json').read_text())
    path = destination / manifest['parquet']
    if path.resolve().parent != destination.resolve():
        raise ValueError('INVALID_SNAPSHOT_PATH')
    con = duckdb.connect(':memory:')
    try:
        rows = con.execute('SELECT kind,factory,product,month,row_key,source_hash,data_json FROM read_parquet(?)', [str(path)]).fetchall()
    finally:
        con.close()
    return [dict(zip(('kind','factory','product','month','row_key','source_hash'), row[:6]), data=json.loads(row[6])) for row in rows]
