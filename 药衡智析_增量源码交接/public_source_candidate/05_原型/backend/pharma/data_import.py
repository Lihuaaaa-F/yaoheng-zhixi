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
import os
import re
import shutil
import sqlite3
import threading
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

# 数据中心三类数据的导入类型（2026-09-22 三模块改版）：上传入口按类型分流，
# 列表按类型展示；类型同时决定解析流水线（业务→数据解析，知识→知识索引，
# 模板→模板解析）。
DATA_TYPES = {
    'business': ('cost_summary', 'material_detail', 'manufacturing_detail', 'labor_detail', 'budget', 'industry_reference'),
    'knowledge': ('product', 'industry', 'enterprise'),
    'template': ('monthly', 'quarterly', 'special'),
}
DATA_TYPE_LABELS = {
    'cost_summary': '成本汇总数据', 'material_detail': '原材料消耗明细', 'manufacturing_detail': '制造费用明细',
    'labor_detail': '人工工时明细', 'budget': '预算数据', 'industry_reference': '行业参考数据',
    'product': '产品知识', 'industry': '行业知识', 'enterprise': '企业内部知识',
    'monthly': '月度成本分析', 'quarterly': '季度成本分析', 'special': '专题分析',
}
# 待解析/解析中/已解析/解析失败 状态机（UPLOADED 为上传后等待解析）。
IMPORT_STATUSES = ('UPLOADED', 'PARSING', 'PARSED', 'PARSE_FAILED')
# 用户上传的知识资料落库目录：文本化后作为默认知识上下文的补充来源。
KNOWLEDGE_INGEST_DIR = IMPORTS_ROOT / 'knowledge'

# 赛题成本宽表预设映射：字段名 → 目标角色（含题包实际表头 元/盒 变体）
PRESET_WIDE_MAPPING = {
    '工厂': 'factory_id', '车间': 'factory_id', '工厂/车间': 'factory_id',
    '产品': 'product_id', '产品名称': 'product_id', '产品编号': 'product_id',
    '月份': 'period', '期间': 'period', '核算期间': 'period', '年月': 'period',
    '产量': 'quantity', '完工数量': 'quantity', '合格产量': 'quantity', '产量(盒)': 'quantity',
    '直接材料': 'element:material', '材料成本': 'element:material', '直接材料(元)': 'element:material',
    '直接材料(元/盒)': 'element:material', '材料成本(元/盒)': 'element:material',
    '直接人工': 'element:labor', '人工成本': 'element:labor', '直接人工(元)': 'element:labor',
    '直接人工(元/盒)': 'element:labor', '人工成本(元/盒)': 'element:labor',
    '制造费用': 'element:overhead', '制造费用(元)': 'element:overhead', '制造费用(元/盒)': 'element:overhead',
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


_imports_db_lock = threading.Lock()
_imports_db_ready = False


def _init_imports_db() -> None:
    """建表 DDL 每进程只执行一次（2026-09-23 审查 SSE-18：原先 _connect 每次连接都跑一遍）。

    模块级旗标随 importlib.reload 重置（测试 isolated_runtime 换运行时目录时重建），生命周期一致。
    """
    global _imports_db_ready
    with _imports_db_lock:
        if _imports_db_ready:
            return
        IMPORTS_ROOT.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(IMPORT_DB)
        try:
            db.execute('CREATE TABLE IF NOT EXISTS imports(id TEXT PRIMARY KEY,kind TEXT,status TEXT,'
                       'filename TEXT,encoding TEXT,size INTEGER,sha256 TEXT,created TEXT,updated TEXT,'
                       'meta TEXT NOT NULL)')
            db.commit()
        finally:
            db.close()
        _imports_db_ready = True


def _connect():
    _init_imports_db()
    db = sqlite3.connect(IMPORT_DB)
    db.row_factory = sqlite3.Row
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

def create_upload(kind: str, filename: str, payload: bytes, data_type: str = '') -> dict[str, Any]:
    if kind not in KINDS:
        raise ValueError('UNKNOWN_IMPORT_KIND')
    if data_type and data_type not in DATA_TYPES.get(kind, ()):
        raise ValueError('UNKNOWN_DATA_TYPE_FOR_KIND:' + str(data_type))
    data_type = data_type or DATA_TYPES[kind][0]
    if not payload:
        raise ValueError('EMPTY_FILE')
    if len(payload) > MAX_UPLOAD_BYTES:
        raise ValueError('FILE_TOO_LARGE')
    suffix = Path(filename).suffix.lower()
    allowed = {'.csv': {'business', 'knowledge'}, '.xlsx': {'business'},
               '.pdf': {'knowledge'}, '.docx': {'knowledge', 'template'},
               '.txt': {'knowledge'}}
    if suffix not in allowed or kind not in allowed[suffix]:
        raise ValueError('UNSUPPORTED_FILE_TYPE_FOR_KIND:' + suffix)
    import_id = hashlib.sha256(payload).hexdigest()[:16] + '-' + kind
    if kind == 'business':
        # Actual and budget may legitimately contain identical bytes. Their
        # explicit role is part of identity, while old same-role IDs remain valid.
        legacy_original=IMPORTS_ROOT / import_id / ('original' + suffix)
        if legacy_original.is_file():
            existing=_row(import_id)
            if existing['meta'].get('data_type')==data_type:
                return {**existing,'dedup':True}
        import_id += '-' + data_type
    folder = _folder(import_id)
    original = folder / ('original' + suffix)
    if original.exists():  # 同内容重复上传：幂等返回已有记录
        # dedup 标记（2026-09-24 用户反馈"上传后没进待解析而是直接解析了"）：
        # 返回的是已有记录——若它早已解析完，记录会直接出现在"已处理记录"
        # 而不是"待解析"。前端据此给出明确提示，避免像被悄悄解析了一样。
        existing = _row(import_id)
        if existing['meta'].get('data_type') != data_type:
            raise ValueError('IMPORT_DATA_TYPE_CONFLICT: 同一文件已按其他资料类型上传，请核对实际或预算口径')
        return {**existing, 'dedup': True}
    original.write_bytes(payload)  # 原始字节保留
    meta: dict[str, Any] = {'filename': filename, 'suffix': suffix, 'data_type': data_type}
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


DELETABLE_IMPORT_STATUSES = ('UPLOADED', 'PARSE_FAILED')


def delete_import(import_id: str) -> None:
    """删除尚未被解析流水线消费的导入记录（2026-09-24 用户要求：传错了
    数据要能从待解析列表删掉）。PARSING/PARSED/PUBLISHED 一律拒绝——记录
    已被解析任务消费或已发布为数据集/知识/模板，删除会留下悬空引用；
    要替换已解析的数据请上传内容不同的修正文件，而不是删除记录。"""
    record = _row(import_id)  # KeyError → 404
    if record['status'] not in DELETABLE_IMPORT_STATUSES:
        raise ValueError('IMPORT_NOT_DELETABLE:' + record['status'])
    if record['meta'].get('parsed') or record['meta'].get('published'):
        raise ValueError('IMPORT_ALREADY_REFERENCED')
    if record['kind'] == 'knowledge':
        # A failed retry must not make an earlier published original deletable.
        for path in (IMPORTS_ROOT / 'knowledge' / 'scopes').glob('*/registry.json'):
            registry = json.loads(path.read_text(encoding='utf-8'))
            if any(item.get('import_id') == import_id for item in registry.get('versions', {}).values()):
                raise ValueError('IMPORT_ALREADY_REFERENCED')
    shutil.rmtree(IMPORTS_ROOT / import_id, ignore_errors=True)
    with _connect() as db:
        db.execute('DELETE FROM imports WHERE id=?', (import_id,))


def _xlsx_nonempty_sheets(payload: bytes) -> list[str]:
    """Formula-only sheets are not empty even if formula caches are absent."""
    import openpyxl
    book=openpyxl.load_workbook(io.BytesIO(payload),read_only=True,data_only=False)
    try:
        return [sheet.title for sheet in book if any(
            any(cell is not None and str(cell).strip() for cell in row)
            for row in sheet.iter_rows(values_only=True))]
    finally:book.close()


def _read_table(suffix: str, payload: bytes, encoding: str, sheet: str | None, *,
                preview_only: bool = False) -> tuple[list[str], list[list[str]]]:
    """返回 (表头, 行)。XLSX 指定工作表；CSV 单表。"""
    if suffix == '.csv':
        text = payload.decode(encoding)
        rows = list(csv.reader(io.StringIO(text)))
        return ([h.strip() for h in rows[0]] if rows else []), [r for r in rows[1:] if any(c.strip() for c in r)]
    if suffix == '.xlsx':
        import openpyxl
        populated=_xlsx_nonempty_sheets(payload)
        if len(populated)>1 and not preview_only:
            raise ValueError('MULTIPLE_WORKSHEETS_NOT_SUPPORTED: 含多个非空工作表，请拆分为单表 XLSX/CSV 后分别上传；尚未接入任何工作表')
        book = openpyxl.load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
        names = book.sheetnames
        target = sheet if sheet in populated else (populated[0] if populated else names[0])
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
        meta['nonempty_sheets']=_xlsx_nonempty_sheets(payload)
        meta['sheet']=(meta['nonempty_sheets'] or meta['sheets'])[0]
    headers, rows = _read_table(suffix, payload, encoding, meta.get('sheet'),preview_only=True)
    meta.setdefault('sheet', meta.get('sheets', [''])[0] if suffix == '.xlsx' else '')
    mapping = suggest_mapping(headers)
    return {'sheet': meta.get('sheet', ''), 'headers': headers,
            'warning':'含多个非空工作表，请拆分为单表 XLSX/CSV 后分别上传；尚未接入任何工作表'
                      if len(meta.get('nonempty_sheets',[]))>1 else None,
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

# 数值角色列（产量/要素/总成本）空值率超过该比例时判 INVALID：
# XLSX 公式单元格无缓存值（openpyxl data_only=True 读回空）会整列静默变空，
# 部分丢失此前发布成功且无任何提示（审计 AUD-DATA-01）。
EMPTY_NUMERIC_INVALID_RATIO = Decimal('0.5')


def _is_unit_cost_column(header: str) -> bool:
    """表头含"元/盒""元/件"等单位成本记法时，单元格是单位成本而非绝对金额。

    审计 AUD-IMP-01（P0）：此前题包《成本汇总》的 直接材料(元/盒) 等列被按
    绝对金额发布，总成本错 4.5 万倍且零警告。此类列必须乘以同行产量换算。
    """
    return '元/' in str(header)


def _tolerance_label(tolerance: Decimal) -> str:
    return f'{tolerance.normalize():f}'


def _row_amount(header: str, number: Decimal, row_quantity: Decimal | None,
                errors: list, warnings: list, record: dict, index: int) -> Decimal | None:
    """按表头单位语义把单元格数值换算为期间金额（单位成本×产量）。

    返回 None 表示无法换算（错误已记录）。明细长表（原材料/费用逐行）传
    accumulated=True 时由调用方处理，不在此换算——明细表头均为总额列。
    """
    if not _is_unit_cost_column(header):
        return number * Decimal(1)
    if row_quantity is None:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                       'row': index,
                       'reason': f'“{header}”是单位成本列（元/盒口径），但该行缺少可用产量，无法换算为金额'})
        return None
    if row_quantity <= 0:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                       'row': index,
                       'reason': f'“{header}”是单位成本列，但该行产量 {row_quantity} 非正数，金额无定义'})
        return None
    return number * row_quantity


def _validate_industry_reference(record: dict[str, Any]) -> dict[str, Any]:
    """行业参考数据走旁路校验：不参与成本事实建模，只要求可读出结构化行。

    行业参考是外部基准（通常为测试数据集），列结构因来源而异（如 产品类别/
    行业P25/行业P50/行业P75），不套用 工厂/产品/期间+要素 的成本合同；
    发布时原样随企业文档存储，供分析快照的“行业参考数据”区块展示。
    """
    folder = IMPORTS_ROOT / record['id']
    payload = (folder / ('original' + record['meta']['suffix'])).read_bytes()
    headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                record['meta'].get('sheet'))
    errors: list[dict[str, Any]] = []
    if len(headers) < 2:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': '行业参考数据至少需要两列（如 产品类别 与 基准值），当前未识别出足够列'})
    if not rows:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': '行业参考数据没有有效数据行'})
    empty_rows = sum(1 for row in rows if not any(str(cell).strip() for cell in row))
    if empty_rows:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': f'行业参考数据含 {empty_rows} 个全空行，请清理后重新上传'})
    return {'status': 'INVALID' if errors else 'VALID', 'errors': errors[:200],
            'error_count': len(errors), 'warnings': [],
            'statistics': {'factories': [], 'products': [], 'periods': [],
                           'quantity_points': 0, 'cost_cells': 0},
            'capabilities': [], 'quantity_independent': True}


def validate_business(record: dict[str, Any], mapping: dict[str, str], options: dict[str, Any]) -> dict[str, Any]:
    """执行字段映射与口径检查，返回质检错误（含文件/表/行号/原因）与能力预览。

    数值角色列的空单元格逐行给出警告级提示（公式无缓存值或漏填）；
    金额全空或关键数值列空值率超过 EMPTY_NUMERIC_INVALID_RATIO 时判 INVALID，
    不允许"看起来通过、数据无声消失"的发布。
    """
    if record['meta'].get('data_type') == 'industry_reference':
        return _validate_industry_reference(record)
    folder = IMPORTS_ROOT / record['id']
    payload = (folder / ('original' + record['meta']['suffix'])).read_bytes()
    headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                record['meta'].get('sheet'))
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    scale = Decimal(str(options.get('amount_scale', '1')))  # 元=1；万元=10000
    if not scale.is_finite() or scale <= 0:
        raise ValueError('INVALID_AMOUNT_SCALE: 金额倍率必须为有限正数')
    quantity_is_independent = options.get('quantity_independent', True)
    dimension_values = {'factory_id': set(), 'product_id': set()}
    periods: set[str] = set()
    quantities: dict[tuple[str, str, str, str], Decimal] = {}
    amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
    seen_quantity_rows: set[tuple[str, str, str, str]] = set()
    dimension_rows = 0
    numeric_empty: dict[str, int] = {}
    seen_detail_rows: dict[tuple[str, ...], int] = {}

    def note_empty_cell(header: str, row_index: int) -> None:
        numeric_empty[header] = numeric_empty.get(header, 0) + 1
        # 行级警告封顶交给外层 warnings[:100]，这里全部记录用于空值率判定
        warnings.append(f'第 {row_index} 行：列“{header}”为空（公式无缓存值或漏填），该单元格不参与聚合')

    role_of = {h: mapping.get(h, '') for h in headers}
    element_headers = [h for h, r in role_of.items() if r.startswith('element:')]
    numeric_roles = [h for h, r in role_of.items()
                     if r == 'quantity' or r == 'total_cost' or str(r).startswith('element:')]
    for required in DIMENSION_ROLES:
        if not any(r == required for r in role_of.values()):
            errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                           'row': '', 'reason': f'缺少必需维度映射：{required}（请在映射步骤指定）'})
    if not element_headers:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': '未映射任何成本要素列（element:*）或成本列，无法构成成本数据'})
    for index, row in enumerate(rows, start=2):
        if record['meta'].get('data_type') in ('material_detail','manufacturing_detail','labor_detail'):
            identity=tuple(str(cell).strip() for cell in row)
            if identity in seen_detail_rows:
                errors.append({'file':record['filename'],'sheet':record['meta'].get('sheet',''),
                               'row':index,'reason':f'与第 {seen_detail_rows[identity]} 行完全重复；'
                                   '缺少可区别的业务明细标识，请去重或补充标识后重新上传'})
                continue
            seen_detail_rows[identity]=index
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
            missing=[name for name,value in [('工厂',factory),('产品',product),('期间',period)] if not value]
            errors.append({'file':record['filename'],'sheet':record['meta'].get('sheet',''),
                           'row':index,'reason':'业务行缺少有效的'+ '、'.join(missing)+'，未加入分析'})
            continue
        dimension_rows += 1
        dimension_values['factory_id'].add(factory)
        dimension_values['product_id'].add(product)
        periods.add(period)
        key = (factory, product, period, scenario)
        # 先取该行产量（金额换算需要；列序不保证产量列在金额列之前）
        row_quantity: Decimal | None = None
        for header, role in role_of.items():
            if role != 'quantity':
                continue
            value = cells.get(header, '')
            if value.strip():
                parsed = parse_number(value)
                if parsed is not None:
                    row_quantity = parsed
        # 汇总/预算宽表：同一要素键重复出现视为重导汇总行（双计风险）；
        # 明细长表（原材料/费用逐行）同键累加是正常形态。
        allow_accumulation = record['meta'].get('data_type') in ('material_detail', 'manufacturing_detail', 'labor_detail')
        for header, role in role_of.items():
            value = cells.get(header, '')
            if role == 'quantity':
                if not value.strip():
                    note_empty_cell(header, index)
                    continue
                number = parse_number(value)
                if number is None:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'“{header}”产量“{value}”不是有效数字'})
                    continue
                if key in quantities and quantities[key] != number:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'同一 工厂/产品/期间 出现冲突产量：{quantities[key]} 与 {number}'})
                elif key not in seen_quantity_rows:
                    # 长表里产量随每条要素重复出现：只独立计一次，防止错误聚合
                    quantities[key] = number
                    seen_quantity_rows.add(key)
            elif role and (role.startswith('element:') or role == 'total_cost'):
                if not value.strip():
                    note_empty_cell(header, index)
                    continue
                number = parse_number(value)
                if number is None:
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index, 'reason': f'“{header}”金额“{value}”不是有效数字'})
                    continue
                converted = _row_amount(header, number, row_quantity, errors, warnings, record, index)
                if converted is None:
                    continue
                element = role.split(':', 1)[1] if role.startswith('element:') else '__total__'
                amount_key = (factory, product, period, scenario, element)
                if amount_key in amounts and not allow_accumulation:
                    # 审计 AUD-IMP-06：汇总/预算行重复导入此前仅告警累加（双计）
                    errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''),
                                   'row': index,
                                   'reason': f'{factory}/{product}/{period}/{element} 金额在汇总/预算表中重复出现'
                                             f'（{amounts[amount_key]} 与 {converted}）——请确认不是汇总行重复导入'})
                    continue
                if amount_key in amounts:
                    warnings.append(f'第 {index} 行：{factory}/{product}/{period}/{element} 明细金额累加')
                amounts[amount_key] = amounts.get(amount_key, Decimal(0)) + converted * scale
    # 金额侧硬校验：全空或关键列空值率超阈值一律 INVALID（防公式无缓存值静默丢失）
    if dimension_rows and not amounts:
        errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                       'reason': '未解析到任何金额数据：金额列全部为空（XLSX 公式单元格无缓存值或漏填）或无有效数据行'})
    for header in numeric_roles:
        empty = numeric_empty.get(header, 0)
        if dimension_rows and Decimal(empty) / Decimal(dimension_rows) > EMPTY_NUMERIC_INVALID_RATIO:
            errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                           'reason': f'“{header}”空值率 {empty}/{dimension_rows} 行（公式无缓存值或漏填）超过 '
                                     f'{int(EMPTY_NUMERIC_INVALID_RATIO * 100)}%，无法确认数据完整性，请用“值”而非公式重新导出后上传'})
    total_by_key: dict[tuple[str, str, str, str], Decimal] = {}
    declared_totals: dict[tuple[str, str, str, str], Decimal] = {}
    element_sums: dict[tuple[str, str, str, str], Decimal] = {}
    for (factory, product, period, scenario, element), amount in amounts.items():
        group = (factory, product, period, scenario)
        if element == '__total__':
            declared_totals[group] = amount
            total_by_key[group] = amount
        else:
            element_sums[group] = element_sums.get(group, Decimal(0)) + amount
            total_by_key[group] = total_by_key.get(group, Decimal(0)) + amount
    # 审计 AUD-IMP-02（数据合同不变量，与 ingestion.audit 同口径的可行子集）：
    # 总成本列与 Σ要素金额 勾稽（单位成本列经产量换算后两者必须一致）。
    # 该校验此前缺失，正是 AUD-IMP-01 量纲错误零警告通过的根源。
    for group in sorted(set(declared_totals) & set(element_sums)):
        declared, elements_total = declared_totals[group], element_sums[group]
        tolerance = max(Decimal('1'), abs(declared) * Decimal('0.005'))
        if abs(declared - elements_total) > tolerance:
            errors.append({'file': record['filename'], 'sheet': record['meta'].get('sheet', ''), 'row': '',
                           'reason': f'{group[0]}/{group[1]}/{group[2]}：总成本列 {declared} 与成本要素合计 '
                                     f'{elements_total} 不一致（超容差 {_tolerance_label(tolerance)}）——'
                                     f'请核对单位成本列是否已按产量换算、或数据本身勾稽不符'})
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
    """根据数据实际开放的分析能力：缺什么就明确说什么不可用。

    2026-09-23 修复（审计 AUD-DATA-02）：available 由数据决定而非恒真；
    语义对齐注册口径——发布注册要求成本与产量事实同时非空
    （industry.register_enterprise 对空任一侧拒绝 EMPTY_DATASET），
    缺产量时明示"发布需独立产量"，不再出现"可用+无成本数据"的自相矛盾。
    """
    has_amounts = bool(amounts)
    has_quantity = bool(quantities)
    has_budget = any(key[3] == 'budget' for key in amounts) or any(key[3] == 'budget' for key in quantities)
    has_yoy = any(str(int(p[:4]) - 1) + p[4:] in periods for p in periods)
    has_mom = len(periods) >= 2
    items = [
        {'capability': 'total_cost_analysis', 'available': has_amounts,
         'reason': '' if has_amounts else '未解析到任何金额数据（金额列全空或无数据行）'},
        {'capability': 'unit_cost_analysis', 'available': has_quantity and has_amounts,
         'reason': '' if (has_quantity and has_amounts)
                   else ('缺少独立产量：单位成本不可计算；发布注册需成本与产量事实同时齐备（请补产量列）'
                         if has_amounts else '缺少金额数据，无法分析也无法发布')},
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
    # 审计 AUD-IMP-03：企业目录名纳入数据指纹——同名重导不同数据得到新目录，
    # 不再覆盖旧注册条目指向的数据；同内容重导幂等落回同一目录。
    source_snapshot = record['sha256']
    enterprise_id = 'imp-' + hashlib.sha256((enterprise_name + pack_id + source_snapshot).encode()).hexdigest()[:8]
    facts: list[dict[str, Any]] = []
    quantities: dict[tuple[str, str, str, str], Decimal] = {}
    amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
    periods: set[str] = set()
    products: set[str] = set()
    factories: set[str] = set()
    _publish_errors: list = []
    _publish_warnings: list = []
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
        # 先取行产量：单位成本列（元/盒口径）须乘产量换算为期间金额（AUD-IMP-01）
        row_quantity = None
        for header, role in role_of.items():
            if role == 'quantity':
                number = parse_number(cells.get(header, ''))
                if number is not None:
                    row_quantity = number
                    quantities[(factory, product, period, scenario)] = number
        for header, role in role_of.items():
            value = cells.get(header, '')
            if role and (role.startswith('element:') or role == 'total_cost'):
                number = parse_number(value)
                if number is None:
                    continue
                converted = _row_amount(header, number, row_quantity, _publish_errors, _publish_warnings, record, index)
                if converted is None:
                    continue
                element = role.split(':', 1)[1] if role.startswith('element:') else '__total__'
                amounts[(factory, product, period, scenario, element)] = amounts.get(
                    (factory, product, period, scenario, element), Decimal(0)) + converted * scale
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
    existed_before = enterprise_dir.exists()  # 重复发布同企业时不得删除既有有效目录
    enterprise_dir.mkdir(parents=True, exist_ok=True)
    (enterprise_dir / 'facts.json').write_text(json.dumps(dataset, ensure_ascii=False), encoding='utf-8')
    if not (enterprise_dir / 'knowledge.json').exists():
        (enterprise_dir / 'knowledge.json').write_text('[]', encoding='utf-8')
    specification = options.get('specification') or '导入数据未声明规格'
    config = {'id': enterprise_id, 'name': enterprise_name, 'dataset_id': record['sha256'][:16],
              'policy_version': 'imported-v1', 'quantity_unit': quantity_unit, 'currency': 'CNY',
              'products': {product: {'name': product, 'specification': specification,
                                     'version': '1'} for product in sorted(products)},
              'responsibilities': {}, 'source_mode': 'imported_cost'}
    config_path = enterprise_dir / 'enterprise.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    try:
        register_enterprise(pack_id, str(config_path))
    except Exception:
        # 注册失败不留孤儿目录（审计 AUD-DATA-02）：仅在本次新建时回滚
        if not existed_before:
            shutil.rmtree(enterprise_dir, ignore_errors=True)
        raise
    return {'enterprise_id': enterprise_id, 'context_id': f'{pack_id}:{enterprise_id}',
            'dataset_facts': len(dataset['costs']) + len(dataset['quantities']),
            'published_at': _now()}


def publish_knowledge(record: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """Parse without flattening genuine page/paragraph locations or publishing yet."""
    from .knowledge import knowledge_context_id, parse_document
    record = get_import(record['id'])
    folder = IMPORTS_ROOT / record['id']
    path = original_path(record)
    suffix = record['meta']['suffix']
    context_id = knowledge_context_id(options.get('context_id') or
                                    ({'industry_id': options['industry_id'], 'enterprise_id': options['enterprise_id']}
                                     if options.get('industry_id') and options.get('enterprise_id') else None))
    industry_id, enterprise_id = context_id.split(':', 1)
    title = str(options.get('title') or record['filename'])[:200]
    products = options.get('products') or []
    if not isinstance(products, list) or any(not isinstance(p, str) or not p.strip() or len(p) > 200 for p in products):
        raise ValueError('INVALID_KNOWLEDGE_PRODUCTS')
    version = str(options.get('document_version') or options.get('version') or '1')[:100]
    metadata = {'context_id': context_id, 'title': title, 'products': products,
                'source_format': suffix.lstrip('.'),
                'factory': str(options.get('factory') or '')[:200],
                'specification': str(options.get('specification') or '')[:200],
                'document_version': version, 'effective_date': str(options.get('effective_date') or '')[:10],
                'data_type': record['meta'].get('data_type', 'enterprise')}
    source_seed = json.dumps([record['sha256'], record['filename'], metadata], ensure_ascii=False, sort_keys=True)
    source_id = 'src-' + hashlib.sha256(source_seed.encode()).hexdigest()[:24]
    blocks = []
    if suffix in ('.pdf', '.docx'):
        blocks = list(parse_document(path))
        ocr_pages = [b['page'] for b in blocks if b.get('requires_ocr')]
        if ocr_pages:
            raise ValueError('KNOWLEDGE_OCR_REQUIRED: 第' + '、'.join(map(str, ocr_pages)) + '页含图片但缺少可检索文字，请先OCR后重新上传；原件已保留')
    elif suffix == '.csv':
        headers, rows = _read_table(suffix, path.read_bytes(), record['encoding'] or 'utf-8', '')
        for offset in range(0, len(rows), 10):
            text = '\n'.join(','.join(r) for r in [headers, *rows[offset:offset + 10]])
            blocks.append({'page': None, 'location': f'数据行{offset + 2}-{min(offset + 11, len(rows) + 1)}', 'original_text': text})
    elif suffix == '.txt':
        lines = path.read_text(encoding=record['encoding'] or 'utf-8').splitlines()
        blocks = [{'page': None, 'location': f'行{i + 1}-{min(i + 12, len(lines))}', 'original_text': '\n'.join(lines[i:i + 12])}
                  for i in range(0, len(lines), 12)]
    text = '\n'.join(b['original_text'] for b in blocks).strip()
    if len(text) < 30:
        raise ValueError('KNOWLEDGE_PARSE_EMPTY: 解析后无有效文本（扫描件需先OCR，系统不自动宣称成功）')
    page_count = len({b['page'] for b in blocks if b.get('page') is not None})
    shared = {**metadata, 'enterprise_id': enterprise_id, 'industry_id': industry_id, 'source_id': source_id,
              'source': record['filename'], 'sha256': record['sha256'],
              'source_category': metadata['data_type'], 'scope': 'product' if products else 'general'}
    records = [{**b, **shared, 'text': b['original_text']} for b in blocks if b['original_text'].strip()]
    entry = {**shared, 'evidence_id': source_id, 'text': text, 'records': records,
             'pages': page_count, 'location': f'共{page_count}页' if suffix == '.pdf' else '段落/行号定位',
             'version': version, 'parsed_at': _now()}
    (folder / 'knowledge_entry.json').write_text(json.dumps(entry, ensure_ascii=False), encoding='utf-8')
    record = _save(record, {**record['meta'], 'knowledge_entry': True,
                            'context_id': context_id, 'source_id': source_id,
                            'parse': {'pages': page_count, 'characters': len(text)}})
    return {'source_id': source_id, 'evidence_id': source_id, 'title': title, 'context_id': context_id,
            'pages': page_count, 'characters': len(text), 'entry_file': 'knowledge_entry.json'}


def check_template(record: dict[str, Any]) -> dict[str, Any]:
    """报告模板兼容性检查：章节结构与占位符契约。

    章节识别兼容两种形态（2026-09-22 修复）：Heading 1 样式（python-docx 生成）
    与中文 Word 常见的“正文样式 + 一、二、… 编号标题”（题包原件即此形态）。
    """
    from docx import Document
    folder = IMPORTS_ROOT / record['id']
    path = folder / ('original' + record['meta']['suffix'])
    document = Document(path)
    headings = [p.text.strip() for p in document.paragraphs if p.text.strip() and (
        p.style.name.startswith('Heading 1') or re.match(r'^[一二三四五六七八九十]+、', p.text.strip()))]
    # 占位符同时扫描段落与表格单元格（题包原件约 88 个占位符位于动态表格内）
    body = '\n'.join(p.text for p in document.paragraphs)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                body += '\n' + cell.text
    required_sections = ['一、封面与基本信息', '二、总成本概览', '三、成本要素明细分析',
                         '四、重点产品专项分析', '五、对标分析', '六、总结与建议']
    # 前缀匹配：题包原件的章节标题带后缀（如“四、重点产品专项分析 — {{产品名称}}”）
    missing = [s for s in required_sections if not any(h.startswith(s) for h in headings)]
    placeholders = sorted(set(re.findall(r'\{\{([^{}]{1,40})\}\}', body)))
    return {'sections': headings, 'section_count': len(headings),
            'compatible': len(headings) >= 6 and not missing,
            'missing_sections': missing,
            'placeholders': placeholders[:120], 'placeholder_count': len(placeholders),
            'note': '章节与占位符契约通过后安装为对应类型当前模板；渲染绑定按占位符名称合同执行'}


# ---------- 数据中心 v2：原始预览、待解析列表、批量发布与状态流转 ----------

def preview_original(record: dict[str, Any]) -> dict[str, Any]:
    """预览上传的原始文件内容（未经映射/清洗），供列表预览按钮实时查看。

    csv/xlsx → 表格（前 200 行）；docx/txt/csv → 文本；pdf → 浏览器内嵌原始文件。
    一次只预览一份由前端保证；本端点只读原始字节，不产生任何写副作用。
    """
    folder = IMPORTS_ROOT / record['id']
    path = folder / ('original' + record['meta']['suffix'])
    suffix = record['meta']['suffix']
    if not path.is_file():
        raise KeyError('ORIGINAL_FILE_MISSING')
    common = {'import_id': record['id'], 'filename': record['filename'], 'suffix': suffix,
              'kind': record['kind'], 'data_type': record.get('meta', {}).get('data_type', ''),
              'size': record.get('size', path.stat().st_size)}
    if suffix in ('.csv', '.xlsx'):
        encoding = record.get('encoding') or 'utf-8'
        headers, rows = _read_table(suffix, path.read_bytes(), encoding, record['meta'].get('sheet'))
        return {**common, 'format': 'table', 'headers': headers, 'rows': rows[:200],
                'row_count': len(rows), 'sheet': record['meta'].get('sheet', '')}
    if suffix == '.pdf':
        return {**common, 'format': 'pdf', 'url': f'/api/imports/{record["id"]}/file'}
    if suffix == '.docx':
        from docx import Document
        document = Document(path)
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return {**common, 'format': 'docx-text', 'paragraphs': paragraphs[:400],
                'paragraph_count': len(paragraphs),
                'tables': [{'rows': [[c.text for c in row.cells] for row in t.rows][:20]} for t in document.tables[:10]]}
    if suffix == '.txt':
        text = path.read_text(encoding=record.get('encoding') or 'utf-8')
        return {**common, 'format': 'text', 'text': text[:80000], 'characters': len(text)}
    raise ValueError('UNSUPPORTED_PREVIEW_SUFFIX:' + suffix)


def original_path(record: dict[str, Any]) -> Path:
    path = IMPORTS_ROOT / record['id'] / ('original' + record['meta']['suffix'])
    if not path.is_file():
        raise KeyError('ORIGINAL_FILE_MISSING')
    return path


def waiting_imports(kind: str, stale_after_seconds: int = 1800) -> list[dict[str, Any]]:
    """待解析列表：UPLOADED / PARSE_FAILED，以及 PARSING 超时回收。

    审计 AUD-IMP-05：worker 崩溃后记录永久停在 PARSING 且无复位端点；按
    updated 时间戳判定——超过 stale_after_seconds（默认 30 分钟）视为
    死锁，可被重新领取解析。"""
    from datetime import datetime
    cutoff = datetime.now(timezone.utc).timestamp() - stale_after_seconds
    def recoverable(record: dict[str, Any]) -> bool:
        if record['status'] in ('UPLOADED', 'PARSE_FAILED'):
            return True
        if record['status'] != 'PARSING':
            return False
        try:
            return datetime.fromisoformat(record['updated']).timestamp() < cutoff
        except (ValueError, TypeError, KeyError):
            return False
    records = _business_records() if kind == 'business' else list_imports(kind)
    if kind == 'business':
        manifest=_workspace_manifest() or {}
        consumed={item['import_id'] for field in ('sources','superseded_sources') for item in manifest.get(field,[])}
        records=[record for record in records if record['id'] not in consumed]
    return [r for r in records if recoverable(r)]


def mark_import_status(record: dict[str, Any], status: str, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    if status not in IMPORT_STATUSES + ('PUBLISHED',):
        raise ValueError('UNKNOWN_IMPORT_STATUS')
    # Workers keep earlier copies while publication adds an immutable mapping
    # contract. Refresh metadata so marking PARSED cannot erase that contract.
    record = get_import(record['id'])
    record['status'] = status
    return _save(record, {**record['meta'], **(extra_meta or {})})


def _collect_industry_reference(validations: list[tuple[dict[str, Any], dict[str, str], dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    """汇集本批行业参考文件的结构化行（原样保留列名，供快照行业参考区块展示）。"""
    rows_out: list[dict[str, Any]] = []
    sources: list[str] = []
    for record, _mapping, _options, _validation in validations:
        if record['meta'].get('data_type') != 'industry_reference':
            continue
        payload = (IMPORTS_ROOT / record['id'] / ('original' + record['meta']['suffix'])).read_bytes()
        headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                    record['meta'].get('sheet'))
        sources.append(record['filename'])
        for row in rows:
            cells = {header: cell for header, cell in zip(headers, row) if str(cell).strip() != ''}
            if cells:
                rows_out.append(cells)
    return {'sources': sources, 'rows': rows_out}


def publish_business_batch(entries: list[tuple[dict[str, Any], dict[str, str], dict[str, Any]]],
                           enterprise_name: str, pack_id: str, quantity_unit: str, *,
                           workspace_enterprise_id: str | None = None,
                           workspace_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """多文件合并发布（v2 数据解析流水线）：同一企业的 汇总/明细/预算 文件
    合并为一个 facts 数据集后注册。

    entries = [(import_record, mapping, options), ...]；口径合并规则（防双计）：
    - 同键金额按数据类型优先级裁决——成本汇总 > 预算 > 明细；低优先级文件
      只补高优先级未覆盖的键，同值跳过、异值以高优先级为准并记提示；
    - 同优先级同键异值视为口径冲突，整体失败（不写注册表，不破坏现有数据）；
    - 产量为独立事实，任何文件间冲突均失败。
    """
    from .industry import register_enterprise
    validations = []
    for record, mapping, options in entries:
        validation = validate_business(record, mapping, options)
        validations.append((record, mapping, options, validation))
        if validation['status'] != 'VALID':
            failed = validation['errors'][:5]
            raise ValueError('IMPORT_VALIDATION_FAILED:' + record['filename'] + ':'
                             + '；'.join(e.get('reason', str(e)) for e in failed))
    from .import_pipeline import TYPE_PRIORITY
    # 审计 AUD-IMP-03：企业目录名纳入数据指纹——同名重导不同数据得到新目录，
    # 不再覆盖旧注册条目指向的数据；同内容重导幂等落回同一目录。
    if not validations:
        raise ValueError('EMPTY_BUSINESS_IMPORT')
    # Mapping, scenario and unit are part of the immutable input version too.
    # Sorting makes upload order immaterial and preserves reproducible snapshots.
    validations.sort(key=lambda entry: entry[0]['id'])
    source_snapshot = hashlib.sha256(json.dumps({'entries':[
        {'sha256':r['sha256'],'mapping':m,'options':o,'data_type':r['meta'].get('data_type'),
         'sheet':r['meta'].get('sheet')} for r,m,o,_ in validations],
        'enterprise':enterprise_name,'pack':pack_id,'unit':quantity_unit},
        ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    enterprise_id = workspace_enterprise_id or 'imp-' + hashlib.sha256((enterprise_name + pack_id + source_snapshot).encode()).hexdigest()[:8]
    merged_amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
    amount_priority: dict[tuple[str, str, str, str, str], int] = {}
    merged_quantities: dict[tuple[str, str, str, str], Decimal] = {}
    quantity_source: dict[tuple[str, str, str, str], str] = {}
    amount_sources: dict[tuple, list[str]] = {}
    quantity_sources: dict[tuple, list[str]] = {}
    periods: set[str] = set()
    products: set[str] = set()
    factories: set[str] = set()
    merge_warnings: list[str] = []
    for record, mapping, options, _validation in validations:
        priority = TYPE_PRIORITY.get(record['meta'].get('data_type', 'cost_summary'), 2)
        scale = Decimal(str(options.get('amount_scale', '1')))
        payload = (IMPORTS_ROOT / record['id'] / ('original' + record['meta']['suffix'])).read_bytes()
        headers, rows = _read_table(record['meta']['suffix'], payload, record['encoding'] or 'utf-8',
                                    record['meta'].get('sheet'))
        role_of = {h: mapping.get(h, '') for h in headers}
        file_amounts: dict[tuple[str, str, str, str, str], Decimal] = {}
        file_quantities: dict[tuple[str, str, str, str], Decimal] = {}
        file_amount_sources: dict[tuple, list[str]] = {}
        file_quantity_sources: dict[tuple, list[str]] = {}
        _publish_errors: list = []
        _publish_warnings: list = []
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
            # 先取行产量：单位成本列（元/盒口径）须乘产量换算（AUD-IMP-01）
            row_quantity = None
            for header, role in role_of.items():
                if role == 'quantity':
                    number = parse_number(cells.get(header, ''))
                    if number is not None:
                        row_quantity = number
                        key = (factory, product, period, scenario)
                        file_quantities[key] = number
                        file_quantity_sources.setdefault(key, []).append(f'{record["filename"]}:{index}')
            for header, role in role_of.items():
                value = cells.get(header, '')
                if role and (role.startswith('element:') or role == 'total_cost'):
                    number = parse_number(value)
                    if number is None:
                        continue
                    converted = _row_amount(header, number, row_quantity, _publish_errors, _publish_warnings, record, index)
                    if converted is None:
                        continue
                    element = role.split(':', 1)[1] if role.startswith('element:') else '__total__'
                    key = (factory, product, period, scenario, element)
                    file_amounts[key] = file_amounts.get(key, Decimal(0)) + converted * scale
                    file_amount_sources.setdefault(key, []).append(f'{record["filename"]}:{index}:{header}')
        for key, number in file_quantities.items():
            if key in merged_quantities and merged_quantities[key] != number:
                raise ValueError(f'IMPORT_QUANTITY_CONFLICT:{key[0]}/{key[1]}/{key[2]}'
                                 f' 在 {quantity_source[key]} 与 {record["filename"]} 中冲突：'
                                 f'{merged_quantities[key]} 与 {number}')
            merged_quantities[key] = number
            quantity_source.setdefault(key, record['filename'])
            quantity_sources.setdefault(key, []).extend(file_quantity_sources[key])
        for key, amount in file_amounts.items():
            if key not in merged_amounts:
                merged_amounts[key] = amount
                amount_priority[key] = priority
                amount_sources[key] = list(file_amount_sources[key])
                continue
            existing_priority = amount_priority[key]
            if workspace_enterprise_id and merged_amounts[key] != amount:
                raise ValueError(f'IMPORT_AMOUNT_CONFLICT:{key[0]}/{key[1]}/{key[2]}/{key[4]}：'
                                 f'{"、".join(amount_sources[key])} 与 {record["filename"]} 金额不一致；'
                                 '本批数据未加入工作区，请核对后重新上传')
            if existing_priority == priority:
                if merged_amounts[key] != amount:
                    raise ValueError(f'IMPORT_AMOUNT_CONFLICT:{key[0]}/{key[1]}/{key[2]}/{key[4]}'
                                     f' 同优先级文件口径冲突：{merged_amounts[key]} 与 {amount}')
                amount_sources[key].extend(file_amount_sources[key])
            elif priority < existing_priority:  # 汇总覆盖先前明细/预算
                if merged_amounts[key] != amount:
                    merge_warnings.append(f'{key[0]}/{key[1]}/{key[2]}/{key[4]}：以{record["filename"]}（汇总口径）为准')
                merged_amounts[key] = amount
                amount_priority[key] = priority
                amount_sources[key] = list(file_amount_sources[key])
            elif merged_amounts[key] != amount:  # 低优先级与汇总不一致：汇总为准
                merge_warnings.append(f'{key[0]}/{key[1]}/{key[2]}/{key[4]}：已由汇总口径覆盖，明细值 {amount} 不采用')
    amounts = merged_amounts
    quantities = merged_quantities
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
                      'source_row': '；'.join(sorted(set(quantity_sources[(factory,product,period,scen)]))),
                      'source_snapshot': source_snapshot, 'quantity': str(quantity), 'unit': quantity_unit})
    elements_present = sorted({key[4] for key in amounts if key[4] != '__total__'})
    for (factory, product, period, scen), total in totals.items():
        for element in elements_present:
            amount = amounts.get((factory, product, period, scen, element))
            if amount is None:
                continue
            facts.append({'fact_id': fact_id(f'c:{factory}:{product}:{period}:{scen}:{element}'),
                          'enterprise_id': enterprise_id, 'factory_id': factory, 'product_id': product,
                          'product_version': '1', 'period': period, 'cost_object': product,
                          'scenario': scen, 'policy_version': 'imported-v1',
                          'source_row': '；'.join(sorted(set(amount_sources[(factory,product,period,scen,element)]))),
                          'source_snapshot': source_snapshot,
                          'element_id': element, 'level': 'detail',
                          'amount': str(amount), 'currency': 'CNY', 'quantity_unit': quantity_unit})
    dataset = {'costs': [f for f in facts if 'element_id' in f],
               'quantities': [f for f in facts if 'quantity' in f],
               'optional': []}
    if workspace_enterprise_id and not any(f['scenario']=='actual' for f in dataset['costs']):
        raise ValueError('WORKSPACE_ACTUAL_DATA_REQUIRED: 仅有预算，尚缺实际成本数据；请补充后一起解析')
    enterprise_dir = (IMPORTS_ROOT / 'workspace' / 'versions' / source_snapshot
                      if workspace_enterprise_id else IMPORTS_ROOT / 'enterprises' / enterprise_id)
    existed_before = enterprise_dir.exists()  # 重复发布同企业时不得删除既有有效目录
    enterprise_dir.mkdir(parents=True, exist_ok=True)
    (enterprise_dir / 'facts.json').write_text(json.dumps(dataset, ensure_ascii=False), encoding='utf-8')
    if not (enterprise_dir / 'knowledge.json').exists():
        (enterprise_dir / 'knowledge.json').write_text('[]', encoding='utf-8')
    specification = options.get('specification') or '导入数据未声明规格'
    config = {'id': enterprise_id, 'name': enterprise_name, 'dataset_id': source_snapshot[:16],
              'policy_version': 'imported-v1', 'quantity_unit': quantity_unit, 'currency': 'CNY',
              'products': {product: {'name': product, 'specification': specification,
                                     'version': '1'} for product in sorted(products)},
              'responsibilities': {}, 'source_mode': 'imported_cost'}
    industry_reference = _collect_industry_reference(validations)
    if industry_reference['rows']:
        config['industry_reference'] = industry_reference
    config_path = enterprise_dir / 'enterprise.json'
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding='utf-8')
    if workspace_enterprise_id:
        from .industry import digest, NormalizedDataset
        version = {**(workspace_manifest or {}), 'context_id':f'{pack_id}:{enterprise_id}',
                   'enterprise_id':enterprise_id,'data_snapshot':digest(NormalizedDataset.model_validate(dataset).model_dump(mode='json')),
                   'source_snapshot':source_snapshot,'published_at':_now()}
        existing_version = enterprise_dir / 'workspace.json'
        if existing_version.is_file():
            previous=json.loads(existing_version.read_text(encoding='utf-8'))
            if previous.get('data_snapshot') != version['data_snapshot']:
                raise ValueError('WORKSPACE_IMMUTABLE_VERSION_CONFLICT')
            version['published_at']=previous['published_at']
        (enterprise_dir / 'workspace.json').write_text(json.dumps(version, ensure_ascii=False), encoding='utf-8')
    try:
        register_enterprise(pack_id, str(config_path), advance_workspace=bool(workspace_enterprise_id))
    except Exception:
        # 注册失败不留孤儿目录（审计 AUD-DATA-02）：仅在本次新建时回滚
        if not existed_before:
            shutil.rmtree(enterprise_dir, ignore_errors=True)
        raise
    return {'enterprise_id': enterprise_id, 'context_id': f'{pack_id}:{enterprise_id}',
            'dataset_facts': len(dataset['costs']) + len(dataset['quantities']),
            'factories': sorted(factories), 'products': sorted(products), 'periods': sorted(periods),
            'source_files': [r['filename'] for r, _, _, _ in validations],
            'data_snapshot': version['data_snapshot'] if workspace_enterprise_id else source_snapshot,
            'merge_warnings': merge_warnings[:50],
            'published_at': _now()}


def _business_records() -> list[dict[str, Any]]:
    """Internal enumeration is deliberately not the 200-row UI list."""
    with _connect() as db:
        rows = db.execute("SELECT * FROM imports WHERE kind='business' ORDER BY created,id").fetchall()
    return [{**dict(row), 'meta':json.loads(row['meta'])} for row in rows]


def _workspace_manifest() -> dict[str, Any] | None:
    """The enterprise registry is the sole atomic pointer to a complete version."""
    from .industry import _registered
    root = (IMPORTS_ROOT / 'workspace' / 'versions').resolve()
    candidates = []
    for path in _registered().values():
        path = Path(path).resolve()
        try: path.relative_to(root)
        except ValueError: continue
        manifest = path.parent / 'workspace.json'
        if manifest.is_file(): candidates.append(json.loads(manifest.read_text(encoding='utf-8')))
    if len(candidates) > 1:
        raise ValueError('WORKSPACE_REGISTRATION_CONFLICT: 本地工作区存在多个企业绑定，需核对导入记录')
    return candidates[0] if candidates else None


def _legacy_workspace_entries(records):
    """Recover old successful imports without calling a model or changing originals.

    Mappings are recovered from saved contracts/presets only. Unrecoverable or
    different-enterprise records block migration rather than being silently left
    out. Existing explicit contexts remain registered and readable.
    """
    from .industry import _enterprise, load_pack
    from .import_pipeline import DETAIL_TYPE_MAPPINGS, _options_for
    entries=[]; bindings=[]; contexts=[]
    for record in records:
        meta=record['meta']; published=meta.get('published') or meta.get('parsed') or {}
        context_id=published.get('context_id')
        if not context_id: continue
        pack_id, _, enterprise_id=context_id.partition(':')
        enterprise=_enterprise(load_pack(pack_id),enterprise_id)
        bindings.append((enterprise['name'],pack_id,enterprise['quantity_unit']))
        contexts.append(context_id)
        saved=meta.get('business_contract') or {}
        headers=meta.get('preview',{}).get('headers') or []
        mapping=saved.get('mapping')
        if mapping is None:
            fixed=DETAIL_TYPE_MAPPINGS.get(meta.get('data_type'))
            mapping={h:fixed.get(h,'') for h in headers} if fixed else {
                h:v for h,v in suggest_mapping(headers).items() if not h.startswith('_')}
        options=saved.get('options') or _options_for(record)
        entries.append((record,mapping,options))
    if not entries:return [],None,[]
    if len(set(bindings)) != 1:
        raise ValueError('WORKSPACE_ENTERPRISE_CONFLICT: 历史导入包含不同企业、行业或计量单位，不能自动合并；请在业务数据中核对来源')
    return entries,bindings[0],sorted(set(contexts))


def _declared_quantity_units(record, mapping):
    units=set()
    for header in record['meta'].get('preview',{}).get('headers') or []:
        role=mapping.get(header,'')
        if role=='quantity' or (role.startswith('element:') and _is_unit_cost_column(header)):
            match=re.search(r'(?:产量|数量)[(（]([^()（）]+)[)）]|元/([^()（）]+)',header)
            if match:units.add((match.group(1) or match.group(2)).strip())
    return units


def publish_workspace(entries, enterprise_name='', pack_id='', quantity_unit=''):
    """Publish every accepted source in this single-enterprise local installation.

    Versions are immutable. Validation/reconciliation completes before the one
    registry pointer changes; failed imports retain the prior valid version.
    The stable context ID keeps knowledge and chat history bound across updates.
    """
    from .locks import exclusive
    folder=IMPORTS_ROOT / 'workspace';folder.mkdir(parents=True,exist_ok=True)
    with exclusive(folder / 'publish.lock'):
        current=_workspace_manifest()
        legacy_contexts=[]
        if current:
            prior=[(get_import(item['import_id']),item['mapping'],item['options']) for item in current['sources']]
            binding=(current['enterprise_name'],current['industry_id'],current['quantity_unit'])
            enterprise_id=current['enterprise_id']
            legacy_contexts=current.get('legacy_context_ids',[])
            superseded=list(current.get('superseded_sources',[]))
        else:
            prior,binding,legacy_contexts=_legacy_workspace_entries(_business_records())
            # Adopt a single preexisting context so its uploaded knowledge and
            # conversation histories retain their identity during migration.
            enterprise_id=legacy_contexts[0].partition(':')[2] if len(legacy_contexts)==1 else 'imp-workspace'
            superseded=[]
        if binding:
            if enterprise_name and enterprise_name!=binding[0]:
                raise ValueError('WORKSPACE_ENTERPRISE_CONFLICT: 当前工作区已绑定企业“'+binding[0]+'”，新文件声明了不同企业')
            if pack_id and pack_id!=binding[1]:
                raise ValueError('WORKSPACE_INDUSTRY_CONFLICT: 新文件行业与已接入数据不一致')
            if quantity_unit and quantity_unit!=binding[2]:
                raise ValueError('WORKSPACE_UNIT_CONFLICT: 新文件计量单位与已接入数据不一致，请先核对口径')
            enterprise_name,pack_id,quantity_unit=binding
        else:
            enterprise_name=enterprise_name or '我的企业'
            pack_id=pack_id or 'generic_manufacturing'
            if not quantity_unit:
                declared=set().union(*[_declared_quantity_units(r,m) for r,m,_ in entries])
                if len(declared)>1:
                    raise ValueError('WORKSPACE_UNIT_CONFLICT: 上传文件声明了不同计量单位，不能合并计算')
                quantity_unit=next(iter(declared),'件')
        by_id={record['id']:(record,mapping,options) for record,mapping,options in prior}
        for record,mapping,options in entries:
            previous=by_id.get(record['id'])
            if previous and (previous[1],previous[2]) != (mapping,options):
                raise ValueError('WORKSPACE_MAPPING_CONFLICT: 同一原始文件不能同时采用不同字段映射或核算口径')
            replacement=options.get('replace_import_id')
            if replacement and not previous:
                replaced=by_id.get(replacement)
                if not replaced or replacement==record['id']:
                    raise ValueError('INVALID_REPLACEMENT_SOURCE: 只能明确替换当前工作区已接入的文件')
                if replaced[0]['meta'].get('data_type')!=record['meta'].get('data_type'):
                    raise ValueError('REPLACEMENT_DATA_TYPE_CONFLICT: 替换文件必须与原文件资料类型一致')
                superseded.append({'import_id':replacement,'filename':replaced[0]['filename'],
                                   'replaced_by':record['id'],'replacement_filename':record['filename']})
                del by_id[replacement]
            units=_declared_quantity_units(record,mapping)
            if units and units != {quantity_unit}:
                raise ValueError(f'WORKSPACE_UNIT_CONFLICT: {record["filename"]} 声明的单位与工作区单位“{quantity_unit}”不一致')
            if options.get('currency','CNY')!='CNY':
                raise ValueError('WORKSPACE_CURRENCY_NOT_SUPPORTED: 当前表格导入适配器仅支持人民币；不得混合币种或自动换汇')
            by_id[record['id']]=(record,dict(mapping),dict(options))
        combined=[by_id[key] for key in sorted(by_id)]
        manifest={'workspace_id':'local-enterprise','enterprise_name':enterprise_name,
                  'industry_id':pack_id,'quantity_unit':quantity_unit,
                  'legacy_context_ids':legacy_contexts,
                  'superseded_sources':superseded,
                  'sources':[{'import_id':r['id'],'filename':r['filename'],'sha256':r['sha256'],
                              'data_type':r['meta'].get('data_type'),'mapping':m,'options':o}
                             for r,m,o in combined]}
        result=publish_business_batch(combined,enterprise_name,pack_id,quantity_unit,
                    workspace_enterprise_id=enterprise_id,workspace_manifest=manifest)
        # The pointer is already durable. A process interruption here is safe:
        # workspace_state obtains accepted sources from the immutable manifest.
        for record,mapping,options in combined:
            fresh=get_import(record['id'])
            _save(fresh,{**fresh['meta'],'business_contract':{'mapping':mapping,'options':options},
                         'workspace_context_id':result['context_id']})
        return {**result,'workspace_id':'local-enterprise','enterprise_name':enterprise_name,
                'quantity_unit':quantity_unit,'accepted_imports':len(combined),
                'legacy_context_ids':legacy_contexts}


def workspace_state() -> dict[str, Any]:
    """Scope-free workbench status, including every pending or rejected file.

    No uploaded data silently falls back to the competition demonstration.
    Legacy published imports are migrated once using deterministic mappings.
    """
    from .industry import _competition_available
    records=_business_records();issues=[]
    try:
        current=_workspace_manifest()
        if current is None and any((r['meta'].get('published') or r['meta'].get('parsed')) for r in records):
            entries,binding,_contexts=_legacy_workspace_entries(records)
            if entries and binding:
                publish_workspace(entries,*binding)
                current=_workspace_manifest()
    except (ValueError,KeyError,OSError) as exc:
        current=None;issues.append({'code':'WORKSPACE_MIGRATION_BLOCKED','message':str(exc)})
    accepted={s['import_id'] for s in (current or {}).get('sources',[])}
    superseded={s['import_id'] for s in (current or {}).get('superseded_sources',[])}
    pending=[]
    for record in records:
        if record['id'] in accepted or record['id'] in superseded:continue
        item={'import_id':record['id'],'filename':record['filename'],'status':record['status']}
        pending.append(item)
        if record['status']=='PARSE_FAILED':
            issues.append({**item,'code':'IMPORT_REJECTED',
                           'message':record['meta'].get('parse_error') or '文件解析失败，请在业务数据中核对后重试'})
    has_uploads=bool(records or current)
    cid=(current or {}).get('context_id')
    if not has_uploads and _competition_available():cid='pharmaceutical:competition'
    status='BLOCKED' if issues else ('PENDING' if pending else ('READY' if cid else 'EMPTY'))
    return {'workspace_id':'local-enterprise','context_id':cid,'status':status,
            'has_uploads':has_uploads,'source':'uploaded' if has_uploads else ('competition' if cid else 'none'),
            'enterprise_name':(current or {}).get('enterprise_name'),
            'data_snapshot':(current or {}).get('data_snapshot'),
            'updated_at':(current or {}).get('published_at'),
            'imported_files':[{k:s[k] for k in ('import_id','filename','data_type')} for s in (current or {}).get('sources',[])],
            'pending_files':pending,'issues':issues,
            'superseded_files':(current or {}).get('superseded_sources',[]),
            'all_files_included':bool(cid) and not pending and not issues,
            'legacy_context_ids':(current or {}).get('legacy_context_ids',[])}


def write_knowledge_source(record: dict[str, Any], text: str | None = None, *, activate=True) -> Path:
    """Write immutable location records; activating a newer version keeps older sources."""
    from .knowledge import knowledge_scope_dir
    path = IMPORTS_ROOT / record['id'] / 'knowledge_entry.json'
    if not path.is_file():
        raise ValueError('KNOWLEDGE_NOT_PARSED')
    entry = json.loads(path.read_text(encoding='utf-8'))
    if not entry.get('records'):
        raise ValueError('KNOWLEDGE_REPARSE_REQUIRED')
    folder = knowledge_scope_dir(entry['context_id'])
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (entry['source_id'] + '.json')
    serialized = json.dumps(entry['records'], ensure_ascii=False, sort_keys=True)
    if target.exists() and target.read_text(encoding='utf-8') != serialized:
        raise ValueError('IMMUTABLE_KNOWLEDGE_VERSION_CONFLICT')
    if not target.exists():
        target.write_text(serialized, encoding='utf-8')
    if activate:
        activate_knowledge_sources(entry['context_id'], [record])
    return target


def candidate_knowledge_registry(context_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    from .knowledge import knowledge_context_id, knowledge_registry
    context_id = knowledge_context_id(context_id)
    registry = knowledge_registry(context_id)
    for record in records:
        entry = json.loads((IMPORTS_ROOT / record['id'] / 'knowledge_entry.json').read_text(encoding='utf-8'))
        if entry['context_id'] != context_id:
            raise ValueError('KNOWLEDGE_CONTEXT_MISMATCH')
        source_id = entry['source_id']
        registry['versions'][source_id] = {'import_id': record['id'], 'filename': record['filename'],
            'title': entry['title'], 'source_hash': record['sha256'], 'pages': entry['pages'],
            'document_version': entry['document_version'], 'data_type': record['meta'].get('data_type', 'enterprise')}
        logical_key = record['meta'].get('data_type', 'enterprise') + ':' + record['filename']
        registry['active'][logical_key] = source_id
    return registry


def activate_knowledge_sources(context_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    from .knowledge import knowledge_scope_dir
    from .locks import exclusive
    folder = knowledge_scope_dir(context_id)
    folder.mkdir(parents=True, exist_ok=True)
    with exclusive(folder / 'registry.lock'):
        registry = candidate_knowledge_registry(context_id, records)
        candidate = folder / 'registry.tmp'
        candidate.write_text(json.dumps(registry, ensure_ascii=False, sort_keys=True), encoding='utf-8')
        os.replace(candidate, folder / 'registry.json')
    return registry


def resolve_knowledge_source(source_id: str, context_id: str = 'pharmaceutical:competition') -> dict[str, Any]:
    """Resolve a registered immutable source only; callers never supply a path."""
    from .knowledge import knowledge_context_id, registered_knowledge_source, source_identifier, competition_extra_sources
    if not re.fullmatch(r'src-[a-f0-9]{24}', source_id):
        raise KeyError('KNOWLEDGE_SOURCE_NOT_FOUND')
    context_id = knowledge_context_id(context_id)
    source = registered_knowledge_source(source_id, context_id)
    if source:
        record = get_import(source['import_id'])
        path = original_path(record)
        if record['sha256'] != source['source_hash'] or hashlib.sha256(path.read_bytes()).hexdigest() != source['source_hash']:
            raise ValueError('KNOWLEDGE_ORIGINAL_CHANGED')
        return {'path': path, 'filename': source['filename'], 'title': source['title']}
    # Original contest/enterprise entries also expose opaque IDs; no arbitrary URL or path resolver.
    from .industry import resolve_context, knowledge_entry_for_context
    from .config import PACKAGE
    context = resolve_context(context_id)
    if context_id == 'pharmaceutical:competition':
        sources = [p for p in (PACKAGE / '03_制药知识文档').iterdir() if p.suffix.lower() in ('.pdf', '.docx', '.txt')]
        sources += competition_extra_sources()
    else:
        sources = [knowledge_entry_for_context(context)]
    for path in sources:
        if source_identifier(path, context_id) == source_id:
            return {'path': path, 'filename': path.name, 'title': path.name}
    raise KeyError('KNOWLEDGE_SOURCE_NOT_FOUND')


def get_import(id_: str) -> dict[str, Any]:
    return _row(id_)


def list_imports(kind: str | None = None) -> list[dict[str, Any]]:
    with _connect() as db:
        if kind:
            rows = db.execute('SELECT * FROM imports WHERE kind=? ORDER BY created DESC LIMIT 200', (kind,)).fetchall()
        else:
            rows = db.execute('SELECT * FROM imports ORDER BY created DESC LIMIT 200').fetchall()
    return [{**dict(r), 'meta': json.loads(r['meta'])} for r in rows]
