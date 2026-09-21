"""数据中心解析流水线：数据解析 / 知识索引构建 / 报告模板解析。

三模块改版（2026-09-22）：上传的数据先进入导入列表等待，点击对应按钮后由
worker 执行本模块的流水线，全程向 JobStore 上报 progress(0-100) 与当前进度
内容，前端进度条轮询 /api/jobs/{id} 渲染。终态消息按合同返回：

- 数据处理成功 / 数据处理失败，{出错步骤}报错：{原因}
- 知识库构建成功（向量不可用时附降级说明）/ 构建知识库失败，{出错步骤}报错：{原因}
- 报告模板解析成功 / 报告模板解析失败，{出错步骤}报错：{原因}

模型协作（赛题加分项"报表生成用大模型、数据提取用小模型"，无密钥时确定性
回退、不伪造模型参与）：
- 字段映射建议、文档类型辅助 → extraction（数据提取模型，小模型）；
- 归因推测、模板占位符语义绑定分析 → analysis（数据分析模型，大模型）。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from . import data_import
from .data_import import DATA_TYPE_LABELS

# 业务数据类型 → 固定角色映射（明细文件按要素归集：原材料→材料、费用→制造费用、人工→人工）。
# 明细行中的材料名/费用类别等文本维度不在 facts 合同内，聚合到要素级；缺明细
# 下钻能力由分析端显式声明（"不按比例推算"），不冒充真实明细分析。
DETAIL_TYPE_MAPPINGS = {
    'budget': {'工厂': 'factory_id', '车间': 'factory_id', '产品名称': 'product_id', '产品': 'product_id',
               '月份': 'period', '期间': 'period',
               '预算产量': 'quantity', '预算产量(盒)': 'quantity',
               '预算直接材料': 'element:material', '预算直接材料(元/盒)': 'element:material',
               '预算直接人工': 'element:labor', '预算直接人工(元/盒)': 'element:labor',
               '预算制造费用': 'element:overhead', '预算制造费用(元/盒)': 'element:overhead',
               '预算总成本': 'total_cost', '预算总成本(元)': 'total_cost',
               '预算单位成本': '', '预算单位成本(元/盒)': ''},
    'material_detail': {'工厂': 'factory_id', '车间': 'factory_id', '产品名称': 'product_id', '产品': 'product_id',
                        '月份': 'period', '期间': 'period', '产量': 'quantity', '产量(盒)': 'quantity',
                        '原材料总成本': 'element:material', '原材料总成本(元)': 'element:material',
                        '直接材料': 'element:material', '材料成本': 'element:material'},
    'manufacturing_detail': {'工厂': 'factory_id', '车间': 'factory_id', '产品名称': 'product_id', '产品': 'product_id',
                             '月份': 'period', '期间': 'period', '产量': 'quantity', '产量(盒)': 'quantity',
                             '费用总额': 'element:overhead', '费用总额(元)': 'element:overhead',
                             '制造费用': 'element:overhead', '制造费用(元)': 'element:overhead'},
    'labor_detail': {'工厂': 'factory_id', '车间': 'factory_id', '产品名称': 'product_id', '产品': 'product_id',
                     '月份': 'period', '期间': 'period', '产量': 'quantity', '产量(盒)': 'quantity',
                     '直接人工总额': 'element:labor', '直接人工总额(元)': 'element:labor',
                     '直接人工': 'element:labor', '人工成本': 'element:labor'},
}
# 多文件同键金额合并优先级：汇总口径优先，明细只补汇总缺失的键（防双计）。
TYPE_PRIORITY = {'cost_summary': 0, 'budget': 1, 'material_detail': 2, 'manufacturing_detail': 2, 'labor_detail': 2}
MAPPING_ROLES = ('factory_id', 'product_id', 'period', 'quantity', 'total_cost',
                 'element:material', 'element:labor', 'element:overhead')


class StepFailure(Exception):
    """携带用户可见步骤名与原因的流水线失败（终态消息由本模块写死格式）。"""

    def __init__(self, step: str, reason: str):
        super().__init__(f'{step}报错：{reason}')
        self.step = step
        self.reason = reason


def _parse_json_object(raw: str) -> dict[str, Any]:
    text = (raw or '').strip()
    fenced = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('JSON_NOT_OBJECT')
    return data


def _fail(store, job_id, result, message: str, imports: list[dict[str, Any]] | None = None):
    if imports:
        for record in imports:
            try:
                data_import.mark_import_status(record, 'PARSE_FAILED', {'parse_error': message})
            except Exception:
                pass
    store.update(job_id, 'FAILED', result, error=message)


# ---------- 业务数据：数据解析（预处理→映射→质检→指标→归因→发布） ----------

def _extraction_mapping(headers: list[str], sample_rows: list[list[str]]) -> tuple[dict[str, str] | None, str]:
    """数据提取模型（小模型）建议字段映射；未配置时返回 None 走预设/固定映射。

    数值性防护：金额/产量角色的建议必须与样例数据形态一致（多数可解析为数字），
    文本列（如原材料名称）不得被映射为金额——模型建议一律过此校验，防幻觉映射。
    """
    from .narrative import ModelGateway
    gateway = ModelGateway.for_route('extraction')
    if not gateway.key:
        return None, '未配置数据提取模型：使用内置预设映射（确定性回退）'
    system = ('你是制药成本数据的字段映射助手。根据表头与样例行，把每一列映射到给定角色之一；'
              '无法判断的列留空。只返回JSON对象 {"mapping": {"列名": "角色"}}，不要输出其他文字。')
    user = json.dumps({'表头': headers, '样例行': sample_rows[:3], '可选角色': list(MAPPING_ROLES)},
                      ensure_ascii=False)
    raw, _usage, _identity = gateway.complete(system, user, operation='import_mapping')
    data = _parse_json_object(raw)
    from .data_import import parse_number
    def _mostly_numeric(header: str) -> bool:
        index = headers.index(header) if header in headers else -1
        values = [row[index] for row in sample_rows[:5] if index < len(row)]
        values = [v for v in values if str(v).strip()]
        if not values:
            return False
        numeric = sum(1 for v in values if parse_number(str(v)) is not None)
        return numeric >= len(values) * 0.6
    mapping = {}
    for header, role in (data.get('mapping') or {}).items():
        if header not in headers or role not in MAPPING_ROLES:
            continue
        if role in ('quantity', 'total_cost') or str(role).startswith('element:'):
            if not _mostly_numeric(header):
                continue
        mapping[header] = str(role)
    if not mapping:
        return None, f'数据提取模型 {gateway.model} 未给出有效映射，使用预设映射'
    return mapping, f'数据提取模型 {gateway.model} 建议映射 {len(mapping)} 列'


def _mapping_for(record: dict[str, Any]) -> tuple[dict[str, str], str]:
    """按数据类型组合映射：明细类型用固定映射；汇总/预算用预设+提取模型建议。"""
    headers: list[str] = record['meta'].get('preview', {}).get('headers') or []
    sample: list[list[str]] = record['meta'].get('preview', {}).get('sample_rows') or []
    data_type = record['meta'].get('data_type', 'cost_summary')
    if data_type in DETAIL_TYPE_MAPPINGS:
        fixed = {h: DETAIL_TYPE_MAPPINGS[data_type].get(h.strip(), '') for h in headers}
        missing = [role for role in ('factory_id', 'product_id', 'period') if role not in fixed.values()]
        note = '固定映射（' + DATA_TYPE_LABELS.get(data_type, data_type) + '）'
        if missing or not any(str(v).startswith('element:') for v in fixed.values()):
            suggested, assist_note = _extraction_mapping(headers, sample)
            if suggested:
                for h, role in suggested.items():
                    if not fixed.get(h):
                        fixed[h] = role
                note += '；' + assist_note
        return fixed, note
    suggested = data_import.suggest_mapping(headers)
    suggested = {h: v for h, v in suggested.items() if not h.startswith('_')}
    if all(role in suggested.values() for role in ('factory_id', 'product_id', 'period')) \
            and any(str(v).startswith('element:') or v == 'total_cost' for v in suggested.values()):
        return suggested, '预设映射（表头命中成本宽表预设）'
    assisted, note = _extraction_mapping(headers, sample)
    if assisted:
        merged = {**{h: '' for h in headers}, **suggested, **assisted}
        return merged, note
    return suggested, '预设映射不完整且未配置数据提取模型；缺失角色将无法通过质检'


def _options_for(record: dict[str, Any]) -> dict[str, Any]:
    data_type = record['meta'].get('data_type', 'cost_summary')
    options: dict[str, Any] = {'scenario': 'budget'} if data_type == 'budget' else {'scenario': 'actual'}
    headers = record['meta'].get('preview', {}).get('headers') or []
    if any('万元' in str(h) for h in headers):
        options['amount_scale'] = '10000'
    for header in headers:
        m = re.search(r'产量\(([^)）]+)\)', str(header))
        if m:
            options['quantity_unit_hint'] = m.group(1)
            break
    return options


def _attribution_overview(context_id: str) -> dict[str, Any]:
    """发布后的归因分析概览：确定性告警提取 + 分析模型（大模型）归因推测。

    合同：模型只输出定性假设 hypothesis 与缺失证据 missing_evidence，不产生
    任何数字；数字一律来自确定性计算（与 narrative.py 解释合同同口径）。
    """
    from .industry import analyze_reference, catalog as scoped_catalog
    options = scoped_catalog(context_id)
    alerts: list[dict[str, Any]] = []
    for product in options.get('products', []):
        months = [m for m in options.get('months', [])]
        if not months:
            continue
        try:
            snapshot = analyze_reference(context_id, factory=options['factories'][0],
                                         product=product, month=months[-1],
                                         analysis_type='monthly', basis='unit')
        except (ValueError, KeyError, IndexError):
            continue
        for alert in snapshot.get('alerts', []) or []:
            alerts.append({'product': product, **alert})
    overview = {'context_id': context_id, 'alert_count': len(alerts), 'alerts': alerts[:60],
                'attribution_mode': 'rules', 'hypotheses': []}
    for alert in alerts[:12]:
        element = alert.get('element') or alert.get('name') or '成本要素'
        rate = alert.get('rate') or alert.get('change_rate')
        overview['hypotheses'].append({
            'element': element, 'basis': 'unit',
            'hypothesis': f'{element}环比波动{("+" + str(rate)) if rate is not None else ""}严格超过±10%，需要核查业务原因；现有导入数据不足以证实因果。',
            'missing_evidence': ['经核实的业务原因记录（采购/工艺/设备/质量）', '对应期间的原始明细与责任部门确认'],
            'suggestion': '按“证据支持假设”处理：先核查口径与原始记录，再决定是否立项整改。'})
    if alerts:
        gateway_note = _analysis_hypotheses(alerts)
        if gateway_note:
            overview['hypotheses'] = gateway_note
            overview['attribution_mode'] = 'analysis_model'
    return overview


def _analysis_hypotheses(alerts: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """数据分析模型（大模型）归因推测：定性假设 + 缺失证据，失败回退规则文本。"""
    from .narrative import ModelGateway
    gateway = ModelGateway.for_route('analysis')
    if not gateway.key:
        return None
    system = ('你是制药成本归因分析助手。输入是确定性计算得到的成本要素环比告警（JSON）。'
              '对每条告警给出定性归因推测与待核查证据清单。禁止编造任何数字或因果结论；'
              '数字只能原样引用输入。只返回JSON对象 {"hypotheses": [{"element": str, '
              '"hypothesis": str, "missing_evidence": [str], "suggestion": str}]}。')
    user = json.dumps({'alerts': alerts[:12],
                       '要求': '假设必须说明“证据不足时不认定因果”，missing_evidence 至少一条'},
                      ensure_ascii=False)
    try:
        raw, _usage, _identity = gateway.complete(system, user, operation='import_attribution')
        data = _parse_json_object(raw)
        result = []
        for item in data.get('hypotheses', [])[:12]:
            if not isinstance(item, dict) or not item.get('hypothesis'):
                continue
            result.append({'element': str(item.get('element', '')), 'basis': 'unit',
                           'hypothesis': str(item['hypothesis'])[:500],
                           'missing_evidence': [str(x)[:200] for x in (item.get('missing_evidence') or ['待核查的业务原因记录'])][:5],
                           'suggestion': str(item.get('suggestion', ''))[:300]})
        return result or None
    except Exception:
        return None


def run_data_parse(store, job):
    job_id = job['id']; result = job['result']; payload = job['input']
    records = [data_import.get_import(x) for x in payload.get('import_ids', [])]
    enterprise_name = (payload.get('enterprise_name') or '').strip()
    quantity_unit = (payload.get('quantity_unit') or '').strip()

    def step(pct, detail, stage):
        store.update(job_id, stage, result, progress=pct, detail=detail)

    try:
        step(5, f'预处理 {len(records)} 个待解析文件（编码/表结构读取）…', 'PREPROCESS')
        entries = []
        quantity_hint = quantity_unit
        factories_seen: list[str] = []
        for record in records:
            data_import.mark_import_status(record, 'PARSING', {'parse_job': job_id})
            headers = record['meta'].get('preview', {}).get('headers') or []
            if not headers:
                raise StepFailure('预处理', f'{record["filename"]} 无法读取表头（文件为空或格式不支持）')
            options = _options_for(record)
            if not quantity_hint and options.get('quantity_unit_hint'):
                quantity_hint = options['quantity_unit_hint']
            stats = (record['meta'].get('preview') or {}).get('row_count')
            if not stats:
                raise StepFailure('预处理', f'{record["filename"]} 无有效数据行')
            entries.append((record, options))
            for factory in (record['meta'].get('last_validation') or {}).get('statistics', {}).get('factories', []):
                if factory not in factories_seen:
                    factories_seen.append(factory)
        step(20, '智能字段映射：数据提取模型建议 + 预设方案…', 'MAPPING')
        mapped = []
        for record, options in entries:
            mapping, note = _mapping_for(record)
            mapped.append((record, mapping, options))
            if note:
                store.update(job_id, 'MAPPING', result, progress=20,
                             detail=f'字段映射（{record["filename"]}）：{note}')
        step(38, '质量校验：维度/数字/口径检查（定位到文件/行）…', 'VALIDATE')
        validated = []
        for record, mapping, options in mapped:
            validation = data_import.validate_business(record, mapping, options)
            data_import._save(record, {**record['meta'], 'last_validation': validation})
            if validation['status'] != 'VALID':
                reasons = '；'.join(e.get('reason', str(e)) for e in validation['errors'][:3])
                raise StepFailure('质量校验', f'{record["filename"]}：{reasons}（共 {validation["error_count"]} 个错误）')
            for factory in validation['statistics']['factories']:
                if factory not in factories_seen:
                    factories_seen.append(factory)
            validated.append((record, mapping, options, validation))
        step(55, '指标计算与能力评估（合并多文件口径，防双计）…', 'COMPUTE')
        if not enterprise_name:
            enterprise_name = '、'.join(factories_seen[:2]) or Path(records[0]['filename']).stem
            enterprise_name = f'{enterprise_name}（导入）'
        if not quantity_hint:
            quantity_hint = '件'
        step(70, '归因分析：告警提取 + 数据分析模型归因推测…', 'ATTRIBUTION')
        publish_entries = [(record, mapping, options) for record, mapping, options, _v in validated]
        published = data_import.publish_business_batch(publish_entries, enterprise_name,
                                                       'pharmaceutical', quantity_hint)
        context_id = published['context_id']
        overview = _attribution_overview(context_id)
        step(90, f'发布注册：企业“{enterprise_name}”（{published["dataset_facts"]} 条事实）…', 'PUBLISH')
        for record, _mapping, _options, _v in validated:
            data_import.mark_import_status(record, 'PARSED', {
                'parsed': {'context_id': context_id, 'enterprise_name': enterprise_name,
                           'job_id': job_id, 'at': data_import._now()}})
        result['published'] = published
        result['attribution'] = overview
        result['message'] = '数据处理成功'
        result['message_detail'] = (f'新数据集 {context_id}：{len(published["factories"])} 工厂 · '
                                    f'{len(published["products"])} 产品 · {len(published["periods"])} 期间；'
                                    f'告警 {overview["alert_count"]} 条，归因推测 {len(overview["hypotheses"])} 条'
                                    f'（{ "数据分析模型" if overview["attribution_mode"] == "analysis_model" else "确定性规则" }）。'
                                    + (f'口径合并提示 {len(published["merge_warnings"])} 条。' if published.get('merge_warnings') else ''))
        store.update(job_id, 'SUCCEEDED', result, progress=100, detail='数据处理成功')
    except StepFailure as exc:
        _fail(store, job_id, result, f'数据处理失败，{exc.step}报错：{exc.reason}', records)
    except Exception as exc:  # noqa: BLE001
        _fail(store, job_id, result, f'数据处理失败，{type(exc).__name__}报错：{str(exc)[:300]}', records)
        import traceback
        traceback.print_exc()


# ---------- 知识库数据：构建知识索引（解析→分块→词法→向量→验证） ----------

def run_kb_build(store, job):
    job_id = job['id']; result = job['result']; payload = job['input']
    records = [data_import.get_import(x) for x in payload.get('import_ids', [])]

    def step(pct, detail):
        store.update(job_id, 'KB_BUILD', result, progress=pct, detail=detail)

    try:
        parsed_files = []
        if records:
            step(3, f'解析待入库知识文档（{len(records)} 份）…', )
            for index, record in enumerate(records):
                data_import.mark_import_status(record, 'PARSING', {'parse_job': job_id})
                try:
                    data_import.publish_knowledge(record, {'title': Path(record['filename']).stem})
                except ValueError as exc:
                    raise StepFailure('解析文档', f'{record["filename"]}：{str(exc)[:200]}')
                entry = json.loads((data_import.IMPORTS_ROOT / record['id'] / 'knowledge_entry.json')
                                   .read_text(encoding='utf-8'))
                source = data_import.write_knowledge_source(record, entry['text'])
                parsed_files.append({'import_id': record['id'], 'filename': record['filename'],
                                     'data_type': record['meta'].get('data_type', ''),
                                     'characters': len(entry['text']), 'kb_source': source.name})
                step(3 + 10 * (index + 1) / len(records), f'解析文档 {index + 1}/{len(records)}：{record["filename"]}')
        elif payload.get('rebuild'):
            step(3, '无待解析文档，按当前知识源重建索引…')
        else:
            raise StepFailure('解析文档', '没有待解析的知识文档，也没有请求重建')
        from .knowledge import Knowledge
        knowledge = Knowledge()

        def build_progress(pct, detail):
            # build 内部 0-100 映射到本任务的 15-95 区间
            step(15 + 80 * pct / 100, detail)

        record_result = knowledge.build(progress=build_progress)
        if record_result.get('status') == 'FAILED':
            reasons = '；'.join(str(f.get('reason', f)) for f in (record_result.get('failures') or [])[:3])
            raise StepFailure('构建索引', f'知识库构建失败：{reasons or "无有效知识分块"}')
        for item in parsed_files:
            data_import.mark_import_status(data_import.get_import(item['import_id']), 'PARSED', {
                'parsed': {'job_id': job_id, 'kb_source': item['kb_source'], 'at': data_import._now()}})
        degraded = record_result.get('status') == 'DEGRADED'
        vector_note = '（向量索引不可用，已降级为词法检索：' + str(record_result.get('vector_error') or '') + '）' if degraded else ''
        result['knowledge'] = record_result
        result['parsed_documents'] = parsed_files
        result['message'] = '知识库构建成功' + vector_note
        result['message_detail'] = (f'知识版本 {str(record_result.get("knowledge_version"))[:12]}：'
                                    f'{record_result.get("chunks", 0)} 个分块 · {len(record_result.get("sources", {}))} 份来源文档'
                                    + (f'；新入库 {len(parsed_files)} 份' if parsed_files else ''))
        store.update(job_id, 'SUCCEEDED' if not degraded else 'DEGRADED', result, progress=100,
                     detail='知识库构建成功' + vector_note)
    except StepFailure as exc:
        _fail(store, job_id, result, f'构建知识库失败，{exc.step}报错：{exc.reason}', records)
    except Exception as exc:  # noqa: BLE001
        _fail(store, job_id, result, f'构建知识库失败，{type(exc).__name__}报错：{str(exc)[:300]}', records)
        import traceback
        traceback.print_exc()


# ---------- 报告模板：解析报告模板（结构→占位符→语义绑定→安装） ----------

def _template_binding_analysis(placeholders: list[str]) -> tuple[dict[str, str] | None, str]:
    """数据分析模型辅助的占位符语义绑定分析（信息性建议；运行时绑定仍按
    reports.binding_semantics 确定性执行）。"""
    from .narrative import ModelGateway
    from .reports import binding_semantics
    gateway = ModelGateway.for_route('analysis')
    deterministic = {name: binding_semantics(name)[0] for name in placeholders[:80]}
    if not gateway.key or not placeholders:
        return None, '未配置数据分析模型：展示确定性绑定语义（reports.binding_semantics）'
    system = ('你是 Word 报告模板占位符分析助手。对每个 {{占位符}} 给出一句话语义说明（它应填充什么数据）。'
              '只返回JSON对象 {"bindings": {"占位符": "语义说明"}}。')
    user = json.dumps({'placeholders': placeholders[:80], '领域': '制药企业产品成本分析报告'}, ensure_ascii=False)
    try:
        raw, _usage, _identity = gateway.complete(system, user, operation='template_binding')
        data = _parse_json_object(raw)
        bindings = {str(k): str(v)[:120] for k, v in (data.get('bindings') or {}).items() if k in placeholders}
        if not bindings:
            return None, '数据分析模型未返回有效绑定说明，展示确定性绑定语义'
        return bindings, f'数据分析模型 {gateway.model} 分析 {len(bindings)} 个占位符语义'
    except Exception:
        return None, '数据分析模型分析失败，展示确定性绑定语义'


def run_template_parse(store, job):
    job_id = job['id']; result = job['result']; payload = job['input']
    records = [data_import.get_import(x) for x in payload.get('import_ids', [])]

    def step(pct, detail):
        store.update(job_id, 'TEMPLATE_PARSE', result, progress=pct, detail=detail)

    try:
        installed = []
        for index, record in enumerate(records):
            data_import.mark_import_status(record, 'PARSING', {'parse_job': job_id})
            base = 100 * index / max(len(records), 1)
            step(base + 5, f'解析模板文档（{index + 1}/{len(records)}）：{record["filename"]}…')
            check = data_import.check_template(record)
            if not check.get('compatible'):
                missing = '、'.join(check.get('missing_sections', [])) or '章节数不符'
                raise StepFailure('章节结构检查', f'{record["filename"]}：缺少固定章节：{missing}')
            step(base + 20, f'章节结构检查通过（6 章节，{check["placeholder_count"]} 个占位符）')
            if check['placeholder_count'] < 20:
                raise StepFailure('占位符提取', f'{record["filename"]}：占位符仅 {check["placeholder_count"]} 个'
                                                 f'（不足 20），无法支撑报告数据绑定合同')
            bindings, note = _template_binding_analysis(check.get('placeholders', []))
            step(base + 45, f'占位符语义绑定分析：{note}')
            analysis_type = record['meta'].get('data_type', 'monthly')
            if analysis_type not in ('monthly', 'quarterly', 'special'):
                analysis_type = 'monthly'
            from .reports import install_template
            source = data_import.original_path(record)
            step(base + 75, f'安装为{DATA_TYPE_LABELS.get(analysis_type, analysis_type)}模板…')
            install_result = install_template(source, analysis_type)
            installed.append({'import_id': record['id'], 'filename': record['filename'],
                              'analysis_type': analysis_type,
                              'placeholder_count': install_result['placeholder_count']})
            data_import.mark_import_status(record, 'PARSED', {
                'parsed': {'analysis_type': analysis_type, 'job_id': job_id,
                           'template_hash': install_result['template_hash'], 'at': data_import._now()}})
        result['installed'] = installed
        result['bindings_note'] = note if records else ''
        result['message'] = '报告模板解析成功'
        result['message_detail'] = '；'.join(
            f'{DATA_TYPE_LABELS.get(item["analysis_type"])} ← {item["filename"]}（{item["placeholder_count"]} 占位符）'
            for item in installed) or '没有待解析的模板'
        store.update(job_id, 'SUCCEEDED', result, progress=100, detail='报告模板解析成功')
    except StepFailure as exc:
        _fail(store, job_id, result, f'报告模板解析失败，{exc.step}报错：{exc.reason}', records)
    except Exception as exc:  # noqa: BLE001
        _fail(store, job_id, result, f'报告模板解析失败，{type(exc).__name__}报错：{str(exc)[:300]}', records)
        import traceback
        traceback.print_exc()
