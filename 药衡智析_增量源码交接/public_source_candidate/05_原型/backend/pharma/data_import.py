"""数据中心：用户自助数据接入（业务数据 / 知识资料 / 报告模板）。

设计约束（对应交付要求）：
- 原始文件永远保留（original.* 字节不动），仅按检测出的编码解码预览；
- 错误行必须定位到 文件/工作表/行号/原因（中文）；
- 映射方案可复用（按表头指纹保存；赛题宽表提供预设方案）；
- 产量与成本独立采集，宽表按列映射，长表按要素列去重，防止错误聚合；
- 校验通过才发布；发布走 industry.register_enterprise 完整合同，
  失败不破坏现有可用数据（注册表在写入前完成全部校验）；
- 能力预览由数据决定：缺产量只给总成本分析，缺基期不给同比。
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from .config import RUNTIME

IMPORTS_ROOT = RUNTIME / 'imports'
MAPPINGS_ROOT = IMPORTS_ROOT / 'mappings'
IMPORT_DB = IMPORTS_ROOT / 'imports.sqlite3'
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
KINDS = ('business', 'knowledge', 'template')
TEXT_ENCODINGS = ('utf-8-sig', 'utf-8', 'gb18030', 'big5')

# 赛题成本宽表预设映射：字段名 → 目标角色
PRESET_WIDE_MAPPING = {
    '工厂': 'factory_id', '车间': 'factory_id', '工厂/车间': 'factory_id',
    '产品': 'product_id', '产品名称': 'product_id', '产品编号': 'product_id',
    '月份': 'period', '期间': 'period', '核算期间': 'period', '年月': 'period',
    '产量': 'quantity', '完工数量': 'quantity', '合格产量': 'quantity', '产量(盒)': 'quantity',
    '直接材料': 'element:material', '材料成本': 'element:material', '直接材料(元)': 'element:material',
    '直接人工': 'element:labor', '人工成本': 'element:labor', '直接人工(元)': 'element:labor',
    '制造费用': 'element:overhead', '制造费用(元)': 'element:overhead',
    '总成本': 'total_cost', '总成本(元)': 'total_cost', '成本合计': 'total_cost',
}
DIMENSION_ROLES = ('factory_id', 'product_id', 'period')
MEASURE_ROLES = ('quantity', 'total_cost')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_encoding(raw: bytes) -> str:
    if raw.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    for enc in TEXT_ENCODINGS:
        try:
            raw.decode(enc)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError('UNSUPPORTED_FILE_ENCODING')


def normalize_period(value: str) -> str | None:
    """把 2026年3月 / 2026-03 / 2026/3 / 202603 / 2026-3 规范为 YYYY-MM。"""
    text = str(value).strip()
    m = re.match(r'^(20\d{2})\s*[年\-/.\s]\s*(\d{1,2})\s*月?$', text) or \
        re.match(r'^(20\d{2})(0[1-9]|1[0-2])$', text)
    if not m:
        return None
    year, month = int(m.group(1)), int(m.group(2))
    if not 1 <= month <= 12:
        return None
    return f'{year:04d}-{month:02d}'


def parse_number(value: str) -> Decimal | None:
    text = str(value).strip().replace(',', '').replace('，', '')
    if not text or text in {'-', '—', 'N/A', 'n/a'}:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _connect():
    IMPORTS_ROOT.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(IMPORT_DB)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS imports(id TEXT PRIMARY KEY,kind TEXT,status TEXT,'
               'filename TEXT,encoding TEXT,size INTEGER,sha256 TEXT,created TEXT,updated TEXT,'
               'meta TEXT NOT NULL)')
    return db


def _row(id_: str) -> dict[str, Any]:
    with _connect() as db:
        row = db.execute('SELECT * FROM imports WHERE id=?', (id_,)).fetchone()
    if not row:
        raise KeyError('IMPORT_NOT_FOUND')
    result = dict(row)
    result['meta'] = json.loads(result['meta'])
    return result


def _save(record: dict[str, Any], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = record['meta'] if meta is None else meta
    with _connect() as db:
        db.execute('UPDATE imports SET status=?,updated=?,meta=? WHERE id=?',
                   (record['status'], _now(), json.dumps(merged, ensure_ascii=False), record['id']))
    return _row(record['id'])


def _folder(id_: str) -> Path:
    folder = IMPORTS_ROOT / id_
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ---------- 上传与预览 ----------

def create_upload(kind: str, filename: str, payload: bytes) -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError('UNKNOWN_IMPORT_KIND')
    if not payload:
        raise ValueError('EMPTY_FILE')
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError('FILE_TOO_LARGE')
    suffix = Path(filename).suffix.lower()
    allowed = {'.csv': {'business'}, '.xlsx': {'business'},
               '.pdf': {'knowledge'}, '.docx': {'knowledge', 'template'},
               '.txt': {'knowledge'}}
    if suffix not in allowed or kind not in allowed[suffix]:
        raise ValueError('UNSUPPORTED_FILE_TYPE_FOR_KIND:' + suffix)
    import_id = hashlib.sha256(payload).hexdigest()[:16] + '-' + kind
    folder = _folder(import_id)
    original = folder / ('original' + suffix)
    if original.exists():  # 同内容重复上传：幂等返回已有记录
        return _row(import_id)
    original.write_bytes(payload)  # 原始字节保留
    meta: dict[str, Any] = {'filename': filename, 'suffix': suffix}
    if suffix in ('.csv', '.txt'):
        meta['encoding'] = detect_encoding(payload)
    preview = _build_preview(kind, suffix, payload, meta)
    meta['preview'] = preview
    record = {'id': import_id, 'kind': kind, 'status': 'UPLOADED', 'filename': filename,
              'encoding': meta.get('encoding', ''), 'size': len(payload),
              'sha256': hashlib.sha256(payload).hexdigest(), 'created': _now(), 'meta': meta}
    with _connect() as db:
        db.execute('INSERT OR REPLACE INTO imports VALUES(?,?,?,?,?,?,?,?,?,?)',
                   (record['id'], kind, record['status'], filename, record['encoding'],
                    record['size'], record['sha256'], record['created'], record['created'],
                    json.dumps(meta, ensure_ascii=False)))
    return _row(import_id)


def _read_table(suffix: str, payload: bytes, encoding: str, sheet: str | None) -> tuple[list[str], list[list[str]]]:
    """返回 (表头, 行)。XLSX 指定工作表；CSV 单表。"""
    if suffix == '.csv':
        text = payload.decode(encoding)
        rows = list(csv.reader(io.StringIO(text)))
        return ([h.strip() for h in rows[0]] if rows else []), [r for r in rows[1:] if any(c.strip() for c in r)]
    if suffix == '.xlsx':
        import openpyxl
        book = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        names = book.sheetnames
        target = sheet if sheet in names else names[0]
        grid = list(book[target].iter_rows(values_only=True))
        book.close()
        rows = [[('' if c is None else str(c)).strip() for c in r] for r in grid if any(str(c or '').strip() for c in r)]
        return ([h for h in rows[0]] if rows else []), rows[1:]
    raise ValueError('UNSUPPORTED_TABLE_SUFFIX')


def _build_preview(kind: str, suffix: str, payload: bytes, meta: dict[str, Any]) -> dict[str, Any]:
    if kind != 'business':
        return {'kind': kind, 'note': '知识/模板导入在发布阶段解析，此处仅保留原件与哈希'}
    if suffix not in ('.csv', '.xlsx'):
        raise ValueError('UNSUPPORTED_FILE_TYPE_FOR_KIND:' + suffix)
    encoding = meta.get('encoding') or 'utf-8'
    if suffix == '.xlsx':
        import openpyxl
        book = openpyxl.load_workbook(io.BytesIO(payload), read_only=True)
        meta['sheets'] = book.sheetnames
        book.close()
    headers, rows = _read_table(suffix, payload, encoding, meta.get('sheet'))
    meta.setdefault('sheet', meta.get('sheets', [''])[0] if suffix == '.xlsx' else '')
    mapping = suggest_mapping(headers)
    return {'sheet': meta.get('sheet', ''), 'headers': headers,
            'sample_rows': rows[:8], 'row_count': len(rows),
            'suggested_mapping': mapping,
            'header_fingerprint': hashlib.sha256('|'.join(headers).encode()).hexdigest()[:12]}


def suggest_mapping(headers: list[str]) -> dict[str, str]:
    """按表头指纹给出建议映射（含保存过的复用方案与内置预设）。"""
    fingerprint = hashlib.sha256('|'.join(h.strip() for h in headers).encode()).hexdigest()[:12]
    saved = MAPPINGS_ROOT / (fingerprint + '.json')
    if saved.is_file():
        cached = json.loads(saved.read_text(encoding='utf-8'))
        return {**{h: '' for h in headers}, **{k: v for k, v in cached['mapping'].items() if k in headers},
                '_saved': saved.stem, '_saved_name': cached.get('name', '')}
    return {header: PRESET_WIDE_MAPPING.get(header.strip(), '') for header in headers}


def save_mapping(headers: list[str], mapping: dict[str, str], name: str = '') -> None:
    """保存可复用映射方案（按表头指纹）。"""
    MAPPINGS_ROOT.mkdir(parents=True, exist_ok=True)
    fingerprint = hashlib.sha256('|'.join(h.strip() for h in headers).encode()).hexdigest()[:12]
    payload = {'name': name or fingerprint, 'saved_at': _now(),
               'mapping': {k: v for k, v in mapping.items() if v}}
    (MAPPINGS_ROOT / (fingerprint + '.json')).write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')


# ---------- 业务数据：映射 → 质检 → 能力预览 ----------

def validate_business(record: dict[str, Any], mapping: dict[str, str], options: dict[str, Any]) -> dict[str, Any]:
    """执行字段映射与口径检查，返回质检错误（含文件/表/行号/原因）与能力预览。"""
    folder = IMPORTS_ROOT / record['id']
    payload = (folder / ('original' + record['meta']['suffix'])).read_bytes()
    headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                record['meta'].get('sheet'))
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    scale = Decimal(str(options.get('amount_scale', '1')))  # 元=1；万元=10000
    quantity_is_independent = options.get('quantity_independent', True)
    dimension_values = {'factory_id': set(), 'product_id': set()}
    periods: set[str] = set()
    quantities: dict[tuple[str, str, str, str], Decimal] = {}
    amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
    seen_quantity_rows: set[tuple[str, str, str, str]] = set()

    role_of = {h: mapping.get(h, '') for h in headers}
    element_headers = [h for h, r in role_of.items() if r.startswith('element:')]
    for required in DIMENSION_ROLES:
        if not any(r == required for r in role_of.values()):
            errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                           'row': '', 'reason': f'缺少必需维度映射：{required}（请在映射步骤指定）'})
    if not element_headers:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': '未映射任何成本要素列（element:*）或成本列，无法构成成本数据'})
    for index, row in enumerate(rows, start=2):
        cells = dict(zip(headers, row))
        factory = product = period = ''
        for header, role in role_of.items():
            value = cells.get(header, '')
            if role == 'factory_id' and value:
                factory = value.strip()
            elif role == 'product_id' and value:
                product = value.strip()
            elif role == 'period' and value:
                period = normalize_period(value) or ''
                if value.strip() and not period:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'期间“{value}”无法识别，需形如 2026-01 / 2026年1月'})
        marker = str(options.get('budget_marker') or '')
        scenario = options.get('scenario') if options.get('scenario') in ('actual', 'budget') \
            else ('budget' if marker and marker in ' '.join(row) else 'actual')
        if not (factory and product and period):
            continue
        dimension_values['factory_id'].add(factory)
        dimension_values['product_id'].add(product)
        periods.add(period)
        key = (factory, product, period, scenario)
        for header, role in role_of.items():
            value = cells.get(header, '')
            if role == 'quantity':
                number = parse_number(value)
                if value.strip() and number is None:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'“{header}”产量“{value}”不是有效数字'})
                    continue
                if number is None:
                    continue
                if key in quantities and quantities[key] != number:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'同一 工厂/产品/期间 出现冲突产量：{quantities[key]} 与 {number}'})
                elif key not in seen_quantity_rows:
                    # 长表里产量随每条要素重复出现：只独立计一次，防止错误聚合
                    quantities[key] = number
                    seen_quantity_rows.add(key)
            elif role and (role.startswith('element:') or role == 'total_cost'):
                number = parse_number(value)
                if value.strip() and number is None:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'“{header}”金额“{value}”不是有效数字'})
                    continue
                if number is None:
                    continue
                element = role.split(':', 1)[1] if role.startswith('element:') else '__total__'
                amount_key = (factory, product, period, scenario, element)
                if amount_key in amounts:
                    warnings.append(f'第 {index} 行：{factory}/{product}/{period}/{element} 金额重复，已按明细累加（请确认不是汇总行重复导入）')
                amounts[amount_key] = amounts.get(amount_key, Decimal(0)) + number * scale
    total_by_key: dict[tuple[str, str, str, str], Decimal] = {}
    for (factory, product, period, scenario, element), amount in amounts.items():
        if element == '__total__':
            total_by_key[(factory, product, period, scenario)] = amount
        else:
            total_by_key[(factory, product, period, scenario)] = total_by_key.get(
                (factory, product, period, scenario), Decimal(0)) + amount
    for key, total in total_by_key.items():
        if key in quantities and quantities[key] <= 0:
            errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                           'reason': f'{key[0]}/{key[1]}/{key[2]} 产量为 0，单位成本无定义'})
    capabilities = _capabilities(periods, quantities, amounts)
    result = {'status': 'INVALID' if errors else 'VALID', 'errors': errors[:200],
              'error_count': len(errors), 'warnings': warnings[:100],
              'statistics': {'factories': sorted(dimension_values['factory_id']),
                             'products': sorted(dimension_values['product_id']),
                             'periods': sorted(periods),
                             'quantity_points': len(quantities), 'cost_cells': len(amounts)},
              'capabilities': capabilities,
              'quantity_independent': quantity_is_independent}
    return result


def _capabilities(periods: set[str], quantities: dict, amounts: dict) -> list[dict[str, Any]]:
    """根据数据实际开放的分析能力：缺什么就明确说什么不可用。"""
    has_quantity = bool(quantities)
    has_budget = any(key[3] == 'budget' for key in amounts) or any(key[3] == 'budget' for key in quantities)
    has_yoy = any(str(int(p[:4]) - 1) + p[4:] in periods for p in periods)
    has_mom = len(periods) >= 2
    items = [
        {'capability': 'total_cost_analysis', 'available': True, 'reason': '' if amounts else '无成本数据'},
        {'capability': 'unit_cost_analysis', 'available': has_quantity,
         'reason': '' if has_quantity else '缺少独立产量，仅提供总成本分析'},
        {'capability': 'mom_comparison', 'available': has_mom, 'reason': '' if has_mom else '只有一个期间，环比不可计算'},
        {'capability': 'yoy_comparison', 'available': has_yoy, 'reason': '' if has_yoy else '缺少去年同期数据，同比不可计算'},
        {'capability': 'budget_comparison', 'available': has_budget, 'reason': '' if has_budget else '缺少预算口径行，预算差异不可计算'},
        {'capability': 'price_volume_decomposition', 'available': False,
         'reason': '需采购数量与单价或用量明细（驱动事实），当前导入未包含，不生成严格量价分解'},
    ]
    return items


# ---------- 发布 ----------

def publish_business(record: dict[str, Any], mapping: dict[str, str], options: dict[str, Any],
                     enterprise_name: str, pack_id: str, quantity_unit: str) -> dict[str, Any]:
    """映射通过质检后发布为新企业：facts.json + enterprise.json + 注册（全部校验先于写注册表）。"""
    from .industry import register_enterprise
    validation = validate_business(record, mapping, options)
    if validation['status'] != 'VALID':
        raise ValueError('IMPORT_VALIDATION_FAILED:' + str(validation['error_count']))
    folder = IMPORTS_ROOT / record['id']
    payload = (folder / ('original' + record['meta']['suffix'])).read_bytes()
    headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                record['meta'].get('sheet'))
    role_of = {h: mapping.get(h, '') for h in headers}
    scale = Decimal(str(options.get('amount_scale', '1')))
    enterprise_id = 'imp-' + hashlib.sha256((enterprise_name + pack_id).encode()).hexdigest()[:8]
    source_snapshot = record['sha256']
    facts: list[dict[str, Any]] = []
    quantities: dict[tuple[str, str, str, str], Decimal] = {}
    amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
    periods: set[str] = set()
    products: set[str] = set()
    factories: set[str] = set()
    for index, row in enumerate(rows, start=2):
        cells = dict(zip(headers, row))
        factory = product = period = ''
        for header, role in role_of.items():
            if role == 'factory_id': factory = cells.get(header, '').strip()
            elif role == 'product_id': product = cells.get(header, '').strip()
            elif role == 'period': period = normalize_period(cells.get(header, '')) or ''
        scenario = options.get('scenario', 'actual')
        if not (factory and product and period):
            continue
        periods.add(period); products.add(product); factories.add(factory)
        base = {'enterprise_id': enterprise_id, 'factory_id': factory, 'product_id': product,
                'product_version': '1', 'period': period, 'cost_object': product,
                'policy_version': 'imported-v1', 'source_row': f'{record["filename"]}:{index}',
                'source_snapshot': source_snapshot}
        for header, role in role_of.items():
            value = cells.get(header, '')
            if role == 'quantity':
                number = parse_number(value)
                if number is not None:
                    quantities[(factory, product, period, scenario)] = number
            elif role and (role.startswith('element:') or role == 'total_cost'):
                number = parse_number(value)
                if number is not None:
                    element = role.split(':', 1)[1] if role.startswith('element:') else '__total__'
                    amounts[(factory, product, period, scenario, element)] = amounts.get(
                        (factory, product, period, scenario, element), Decimal(0)) + number * scale
    totals: dict[tuple[str, str, str, str], Decimal] = {}
    for (factory, product, period, scen, element), amount in amounts.items():
        totals.setdefault((factory, product, period, scen), Decimal(0))
        if element != '__total__':
            totals[(factory, product, period, scen)] += amount
    for key, amount in amounts.items():
        if key[4] == '__total__':
            totals[key[:4]] = amount
    def fact_id(seed: str) -> str:
        return 'f-' + hashlib.sha256(seed.encode()).hexdigest()[:16]
    facts = []
    for (factory, product, period, scen), quantity in quantities.items():
        facts.append({'fact_id': fact_id(f'q:{factory}:{product}:{period}:{scen}'),
                      'enterprise_id': enterprise_id, 'factory_id': factory, 'product_id': product,
                      'product_version': '1', 'period': period, 'cost_object': product,
                      'scenario': scen, 'policy_version': 'imported-v1',
                      'source_row': f'{record["filename"]}:quantity:{factory}:{product}:{period}',
                      'source_snapshot': source_snapshot, 'quantity': str(quantity), 'unit': quantity_unit})
    elements_present = sorted({key[4] for key in amounts if key[4] != '__total__'})
    for (factory, product, period, scen), total in totals.items():
        if scen != 'actual' and not any(k[3] == scen for k in amounts):
            continue
        for element in elements_present:
            amount = amounts.get((factory, product, period, scen, element))
            if amount is None:
                continue
            facts.append({'fact_id': fact_id(f'c:{factory}:{product}:{period}:{scen}:{element}'),
                          'enterprise_id': enterprise_id, 'factory_id': factory, 'product_id': product,
                          'product_version': '1', 'period': period, 'cost_object': product,
                          'scenario': scen, 'policy_version': 'imported-v1',
                          'source_row': f'{record["filename"]}:cost:{factory}:{product}:{period}:{element}',
                          'source_snapshot': source_snapshot,
                          'element_id': element, 'level': 'detail',
                          'amount': str(amount), 'currency': 'CNY', 'quantity_unit': quantity_unit})
    dataset = {'costs': [f for f in facts if 'element_id' in f],
               'quantities': [f for f in facts if 'quantity' in f],
               'optional': []}
    enterprise_dir = IMPORTS_ROOT / 'enterprises' / enterprise_id
    enterprise_dir.mkdir(parents=True, exist_ok=True)
    (enterprise_dir / 'facts.json').write_text(json.dumps(dataset, ensure_ascii=False), encoding='utf-8')
    (enterprise_dir / 'knowledge.json').write_text('[]', encoding='utf-8')
    config = {'id': enterprise_id, 'name': enterprise_name, 'dataset_id': record['sha256'][:16],
              'policy_version': 'imported-v1', 'quantity_unit': quantity_unit, 'currency': 'CNY',
              'products': {product: {'name': product, 'specification': options.get('specification', ''),
                                     'version': '1'} for product in sorted(products)},
              'responsibilities': {}, 'source_mode': 'imported_cost'}
    config_path = enterprise_dir / 'enterprise.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    register_enterprise(pack_id, str(config_path))
    return {'enterprise_id': enterprise_id, 'context_id': f'{pack_id}:{enterprise_id}',
            'dataset_facts': len(dataset['costs']) + len(dataset['quantities']),
            'published_at': _now()}


def publish_knowledge(record: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """知识资料解析：文本直接抽取；解析失败必须显式失败，不得标成功。"""
    folder = IMPORTS_ROOT / record['id']
    path = folder / ('original' + record['meta']['suffix'])
    suffix = record['meta']['suffix']
    title = options.get('title') or record['filename']
    pages: list[str] = []
    if suffix == '.pdf':
        import fitz
        doc = fitz.open(path)
        pages = [page.get_text() for page in doc]
        doc.close()
    elif suffix == '.docx':
        from docx import Document
        document = Document(path)
        pages = ['\n'.join(p.text for p in document.paragraphs)]
    elif suffix == '.txt':
        pages = [path.read_text(encoding=record['encoding'] or 'utf-8')]
    text = '\n'.join(pages).strip()
    if len(text) < 30:
        raise ValueError('KNOWLEDGE_PARSE_EMPTY: 解析后无有效文本（扫描件需先OCR，系统不自动宣称成功）')
    entry = {'enterprise_id': options.get('enterprise_id', ''), 'industry_id': options.get('industry_id', ''),
             'evidence_id': 'k-' + record['sha256'][:16], 'source': record['filename'], 'title': title,
             'text': text, 'location': f'共{len(pages)}页' if suffix == '.pdf' else '全文',
             'applicable_products': options.get('products', []), 'applicable_factories': options.get('factories', []),
             'effective_period': options.get('period', ''), 'version': options.get('version', '1'),
             'sha256': record['sha256'], 'parsed_at': _now()}
    (folder / 'knowledge_entry.json').write_text(json.dumps(entry, ensure_ascii=False), encoding='utf-8')
    record = _save(record, {**record['meta'], 'knowledge_entry': True,
                            'parse': {'pages': len(pages), 'characters': len(text)}})
    return {'evidence_id': entry['evidence_id'], 'pages': len(pages), 'characters': len(text),
            'entry_file': 'knowledge_entry.json'}


def check_template(record: dict[str, Any]) -> dict[str, Any]:
    """报告模板兼容性检查：章节结构与占位符契约，不自动安装。"""
    from docx import Document
    folder = IMPORTS_ROOT / record['id']
    path = folder / ('original' + record['meta']['suffix'])
    document = Document(path)
    headings = [p.text.strip() for p in document.paragraphs if p.style.name.startswith('Heading 1') and p.text.strip()]
    placeholders = sorted(set(re.findall(r'\{\{([^{}]{1,40})\}\}', '\n'.join(p.text for p in document.paragraphs))))
    required_sections = ['一、封面与基本信息', '二、总成本概览', '三、成本要素明细分析',
                         '四、重点产品专项分析', '五、对标分析', '六、总结与建议']
    missing = [s for s in required_sections if s not in headings]
    return {'sections': headings, 'section_count': len(headings),
            'compatible': len(headings) == 6 and not missing,
            'missing_sections': missing,
            'placeholders': placeholders[:80], 'placeholder_count': len(placeholders),
            'note': '模板兼容性检查仅供参考；正式模板由行业包统一管理，安装需开发流程'}


def get_import(id_: str) -> dict[str, Any]:
    return _row(id_)


def list_imports(kind: str | None = None) -> list[dict[str, Any]]:
    with _connect() as db:
        if kind:
            rows = db.execute('SELECT * FROM imports WHERE kind=? ORDER BY created DESC LIMIT 200', (kind,)).fetchall()
        else:
            rows = db.execute('SELECT * FROM imports ORDER BY created DESC LIMIT 200').fetchall()
    return [{**dict(r), 'meta': json.loads(r['meta'])} for r in rows]
