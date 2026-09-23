# -*- coding: utf-8 -*-
"""2026-09-23 全仓审查修复的回归测试（docs/audits/20260923-1f78b2f）。

对应缺陷编号与验收要求（均来自审查报告的"验收"栏）：
- AUD-DATA-01：XLSX 无缓存公式单元格金额不再静默丢失——行级警告、
  金额全空/关键列空值率超阈值判 INVALID（xlsx 反例）。
- AUD-DATA-02：能力预览 available 由数据决定；发布注册失败不留孤儿目录。
- AUD-BENCH-02：benchmark() 缺省方向=本单位−对标厂（与报告路径同向），
  方向断言测试。
- AUD-TPL-01：安装模板同比补绑定按表头/首列文字定位（行序打乱反例）。
- AUD-BENCH-01：generate(allow_model=False) 不发起模型调用即返回规则结果；
  cached_generation 只读缓存不写。
"""
import importlib
import io
import json

import pytest

from pharma import data_import, import_pipeline, model_settings

WIDE_CSV = ('工厂,产品名称,月份,产量(盒),直接材料(元/盒),直接人工(元/盒),制造费用(元/盒),单位成本(元/盒),总成本(元)\n'
            '中药一厂,银黄口服液,2026-01,10000,3.10,1.00,0.90,5.00,50000\n'
            '中药一厂,银黄口服液,2026-02,10100,3.50,1.00,0.90,5.40,54540\n')


@pytest.fixture
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path))
    monkeypatch.delenv('PHARMA_SHOW_TEST_CONTEXTS', raising=False)
    monkeypatch.setenv('PHARMA_MODEL_KEY_FILE', str(tmp_path / 'no-key-in-tests.key'))
    monkeypatch.delenv('PHARMA_API_KEY', raising=False)
    monkeypatch.delenv('PHARMA_MODEL_ROUTES', raising=False)
    import pharma.config as config
    importlib.reload(config)
    for module in (data_import, model_settings, import_pipeline):
        importlib.reload(module)
    import pharma.industry as industry
    monkeypatch.setattr(industry, 'ENTERPRISE_REGISTRY', tmp_path / 'enterprise_registry.json')
    monkeypatch.setattr(import_pipeline, '_extraction_mapping', lambda h, s: (None, '测试：预设映射'))
    monkeypatch.setattr(import_pipeline, '_analysis_hypotheses', lambda a: None)
    return tmp_path


def _xlsx_payload(amount_formulas: dict[str, bool]) -> bytes:
    """构造成本宽表 xlsx；amount_formulas 指定哪些金额列写公式（无缓存值）。"""
    import openpyxl
    headers = ['工厂', '产品名称', '月份', '产量(盒)', '直接材料(元/盒)', '直接人工(元/盒)', '制造费用(元/盒)']
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    rows = [('中药一厂', '银黄口服液', '2026-01', '10000', '3.10', '1.00', '0.90'),
            ('中药一厂', '银黄口服液', '2026-02', '10100', '3.50', '1.00', '0.90'),
            ('中药一厂', '银黄口服液', '2026-03', '10200', '3.60', '1.05', '0.92')]
    for values in rows:
        out = []
        for header, value in zip(headers, values):
            if amount_formulas.get(header):
                col = openpyxl.utils.get_column_letter(headers.index('产量(盒)') + 1)
                out.append(f'={col}{ws.max_row + 2}*1')  # 公式：读回无缓存值
            else:
                out.append(value)
        ws.append(out)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _mapping_for(record):
    suggested = record['meta']['preview'].get('suggested_mapping') or {}
    return {h: v for h, v in suggested.items() if not str(h).startswith('_')}


# ---------- AUD-BENCH-02：benchmark 缺省方向 ----------

def test_benchmark_default_direction_matches_report_path():
    from pharma.metrics import benchmark, analyze
    analyze('中药一厂', '银黄口服液', '2026-05')  # 确保数据快照已建立（CI 冷缓存）
    comp = benchmark('银黄口服液', '2026-05', factory='中药一厂')
    assert (comp['left'], comp['right']) == ('中药一厂', '中药二厂')
    assert comp['direction'] == '中药一厂−中药二厂，以中药二厂为分母'
    only_left = benchmark('银黄口服液', '2026-05', left='中药一厂')
    assert only_left['right'] == '中药二厂'
    only_right = benchmark('银黄口服液', '2026-05', right='中药二厂')
    assert only_right['left'] == '中药一厂'
    # 显式两厂不受缺省逻辑影响
    explicit = benchmark('银黄口服液', '2026-05', left='中药二厂', right='中药一厂')
    assert explicit['direction'].startswith('中药二厂−中药一厂')


# ---------- AUD-DATA-01：XLSX 公式无缓存值不静默丢失 ----------

def test_xlsx_partial_formula_amounts_get_row_warning_and_invalid(isolated_runtime):
    payload = _xlsx_payload({'直接材料(元/盒)': True})  # 材料列全部为公式
    record = data_import.create_upload('business', '成本汇总.xlsx', payload, 'cost_summary')
    result = data_import.validate_business(record, _mapping_for(record), {})
    # 行级警告：每一行都点名公式列
    assert any('为空（公式无缓存值或漏填）' in w and '直接材料' in w for w in result['warnings'])
    assert any(w.startswith('第 2 行：') for w in result['warnings'])
    # 空值率 3/3 超过 50% 阈值 → INVALID，错误指明原因与出路
    assert result['status'] == 'INVALID'
    assert any('空值率 3/3' in e['reason'] and '公式' in e['reason'] for e in result['errors'])


def test_xlsx_all_formula_amounts_invalid_with_capability_note(isolated_runtime):
    payload = _xlsx_payload({'直接材料(元/盒)': True, '直接人工(元/盒)': True, '制造费用(元/盒)': True})
    record = data_import.create_upload('business', '成本汇总.xlsx', payload, 'cost_summary')
    result = data_import.validate_business(record, _mapping_for(record), {})
    assert result['status'] == 'INVALID'
    assert any('未解析到任何金额数据' in e['reason'] for e in result['errors'])
    caps = {c['capability']: c for c in result['capabilities']}
    assert caps['total_cost_analysis']['available'] is False


def test_few_empty_amount_cells_stay_valid_with_warning_only(isolated_runtime):
    # 少量空单元格（1/3，未过阈值）：VALID 但逐行警告可见，不再静默
    import openpyxl
    headers = ['工厂', '产品名称', '月份', '产量(盒)', '直接材料(元/盒)', '直接人工(元/盒)', '制造费用(元/盒)']
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(headers)
    ws.append(['中药一厂', '银黄口服液', '2026-01', '10000', '3.10', '1.00', '0.90'])
    ws.append(['中药一厂', '银黄口服液', '2026-02', '10100', None, '1.00', '0.90'])
    ws.append(['中药一厂', '银黄口服液', '2026-03', '10200', '3.60', '1.05', '0.92'])
    buf = io.BytesIO(); wb.save(buf)
    record = data_import.create_upload('business', '汇总.xlsx', buf.getvalue(), 'cost_summary')
    result = data_import.validate_business(record, _mapping_for(record), {})
    assert result['status'] == 'VALID'
    assert any('第 3 行：列“直接材料(元/盒)”为空' in w for w in result['warnings'])
    assert result['statistics']['cost_cells'] >= 4  # 其余金额仍参与聚合


# ---------- AUD-DATA-02：能力预览语义 + 发布失败不留孤儿目录 ----------

def test_capability_preview_available_follows_data():
    caps = {c['capability']: c for c in data_import._capabilities({'2026-01'}, {}, {})}
    assert caps['total_cost_analysis']['available'] is False
    amounts = {('f', 'p', '2026-01', 'actual', 'material'): 1}
    caps = {c['capability']: c for c in data_import._capabilities({'2026-01'}, {}, amounts)}
    assert caps['total_cost_analysis']['available'] is True
    # 缺产量：单位成本不可用，且 reason 对齐注册口径（发布需产量）
    assert caps['unit_cost_analysis']['available'] is False
    assert '发布' in caps['unit_cost_analysis']['reason'] and '产量' in caps['unit_cost_analysis']['reason']
    quantities = {('f', 'p', '2026-01', 'actual'): 10}
    caps = {c['capability']: c for c in data_import._capabilities({'2026-01'}, quantities, amounts)}
    assert caps['unit_cost_analysis']['available'] is True


def test_publish_failure_cleans_orphan_enterprise_dir(isolated_runtime, tmp_path, monkeypatch):
    import pharma.industry as industry
    record = data_import.create_upload('business', '汇总.csv', WIDE_CSV.encode('utf-8'), 'cost_summary')
    monkeypatch.setattr(industry, 'register_enterprise',
                        lambda *a, **k: (_ for _ in ()).throw(ValueError('EMPTY_DATASET')))
    with pytest.raises(ValueError, match='EMPTY_DATASET'):
        data_import.publish_business(record, _mapping_for(record), {}, '测试企业', 'pharmaceutical', '盒')
    enterprises = data_import.IMPORTS_ROOT / 'enterprises'
    leftovers = list(enterprises.iterdir()) if enterprises.is_dir() else []
    assert leftovers == [], f'注册失败后残留企业目录：{leftovers}'


# ---------- AUD-TPL-01：同比补绑定按表头文字定位 ----------

def test_install_template_yoy_binding_locates_by_header_text(isolated_runtime, tmp_path, monkeypatch):
    import pharma.reports as reports
    from docx import Document
    monkeypatch.setattr(reports, 'RUNTIME_TEMPLATES', tmp_path / 'templates')
    doc = Document()
    for title in ('一、封面与基本信息', '二、总成本概览', '三、成本要素明细分析',
                  '四、重点产品专项分析', '五、对标分析', '六、总结与建议'):
        doc.add_paragraph(title)
    doc.add_paragraph('{{产品名称}} {{分析月份}}')
    headers = ['指标', '本月实际', '上月实际', '环比变动', '去年同月', '同比变动', '预算值', '预算偏差']
    table = doc.add_table(rows=1, cols=len(headers))
    for cell, header in zip(table.rows[0].cells, headers):
        cell.text = header
    # 行序故意打乱（人工在最前、中间插产量行；旧实现按 rows[4:7] 顺序会错绑）
    for label in ('其中：直接人工(元/盒)', '产量(盒)', '其中：直接材料(元/盒)', '其中：制造费用(元/盒)'):
        table.add_row().cells[0].text = label
    source = tmp_path / 'tpl.docx'
    doc.save(source)
    result = reports.install_template(source, 'monthly')
    installed = tmp_path / 'templates' / 'monthly.docx'
    doc2 = Document(installed)
    overview = next(t for t in doc2.tables if any('去年同月' in c.text for c in t.rows[0].cells))
    header_texts = [c.text.strip() for c in overview.rows[0].cells]
    yoy_col, rate_col = header_texts.index('去年同月'), header_texts.index('同比变动')
    def row_of(keyword):
        return next(r for r in overview.rows[1:] if keyword in r.cells[0].text)
    assert row_of('直接材料').cells[yoy_col].text == '{{去年材料成本}}'
    assert row_of('直接材料').cells[rate_col].text == '{{材料成本同比}}%'
    assert row_of('直接人工').cells[yoy_col].text == '{{去年人工成本}}'
    assert row_of('直接人工').cells[rate_col].text == '{{人工成本同比}}%'
    assert row_of('制造费用').cells[yoy_col].text == '{{去年制造费用}}'
    assert '同比补绑定 6 个单元格' in result['yoy_binding_note']
    # 占位符登记了补绑定的六个字段
    fields = {e['field'] for e in result['placeholders']}
    assert {'去年材料成本', '材料成本同比', '去年人工成本', '去年制造费用'} <= fields


def test_install_template_missing_yoy_columns_skips_binding(isolated_runtime, tmp_path, monkeypatch):
    import pharma.reports as reports
    from docx import Document
    monkeypatch.setattr(reports, 'RUNTIME_TEMPLATES', tmp_path / 'templates')
    doc = Document()
    for title in ('一、封面与基本信息', '二、总成本概览', '三、成本要素明细分析',
                  '四、重点产品专项分析', '五、对标分析', '六、总结与建议'):
        doc.add_paragraph(title)
    doc.add_paragraph('{{产品名称}}')
    headers = ['指标', '本月实际', '上月实际', '环比变动', '预算值']  # 无去年同月/同比列
    table = doc.add_table(rows=1, cols=len(headers))
    for cell, header in zip(table.rows[0].cells, headers):
        cell.text = header
    table.add_row().cells[0].text = '其中：直接材料(元/盒)'
    source = tmp_path / 'tpl2.docx'
    doc.save(source)
    result = reports.install_template(source, 'monthly')
    assert '跳过' in result['yoy_binding_note']
    assert not any(e['field'].startswith('去年') for e in result['placeholders'])


# ---------- AUD-BENCH-01：allow_model=False 与只读缓存 ----------

def test_generate_allow_model_false_returns_rules_without_model_calls():
    from pharma.narrative import generate
    from pharma.metrics import analyze
    snapshot = analyze('中药一厂', '银黄口服液', '2026-05')
    result = generate(snapshot, [], allow_model=False)
    assert result['generation_mode'] == 'rules'
    assert result['model_responded'] is False
    assert result['findings']  # 确定性事实仍在（数字由程序绑定）
    # 无输入证据时结论显式为证据不足，而非模型解释
    assert all(f.get('origin') in (None, 'rules') for f in result['findings'])


def test_cached_generation_readonly_and_generate_write_visible(tmp_path):
    # 独立 gateway runtime：不读写真实 .runtime/model_gateway.sqlite3
    import pharma.narrative as narrative
    from pharma.metrics import analyze
    snapshot = analyze('中药一厂', '银黄口服液', '2026-05')
    evidence = {'status': 'PASS', 'knowledge_version': 'v-test', 'evidence': []}
    gateway = narrative.ModelGateway(runtime=tmp_path, key_file=str(tmp_path / 'k.key'))
    assert narrative.cached_generation(snapshot, evidence, gateway=gateway) is None  # 空缓存不命中且不抛错
    fake = {'status': 'PASS', 'model': 'stub', 'model_live': True, 'findings': [{'claim_type': 'hypothesis'}]}
    import sqlite3
    _sources, _excluded, _kv, gateway, key = narrative._prepare_generation(snapshot, evidence, gateway)
    with sqlite3.connect(gateway.dbpath) as db:
        db.execute('INSERT OR REPLACE INTO cache VALUES(?,?,?)',
                   (key, 12345.0, json.dumps(fake, ensure_ascii=False)))
    hit = narrative.cached_generation(snapshot, evidence, gateway=gateway)
    assert hit is not None and hit.get('cache_hit') is True and hit['model'] == 'stub'


def test_benchmark_async_default_queues_report_and_returns_rules_immediately(tmp_path, monkeypatch):
    """对标页默认 async（AUD-BENCH-01）：冷缓存即时返回规则解释 + 入队报告任务；
    入队失败不阻断响应；已完成任务的 narrative 被直接复用。"""
    from types import SimpleNamespace
    from pharma import api, narrative, context_services, knowledge
    from pharma.jobs import JobStore
    context = {'enterprise_id': 'competition', 'industry_id': 'pharmaceutical', 'data_snapshot': 'synthetic-only'}
    monkeypatch.setattr(api, 'selected_context', lambda _: 'pharmaceutical:competition')
    monkeypatch.setattr(api, 'benchmark_analysis',
                        lambda *a, **k: ({'snapshot_id': 's1', 'factory': 'A', 'product': 'P', 'month': '2026-05',
                                          'period': {'start': '2026-05', 'end': '2026-05'}, 'elements': []}, {'elements': []}))
    import pharma.industry as industry
    monkeypatch.setattr(industry, 'resolve_context',
                        lambda _: SimpleNamespace(model_dump=lambda: context, context_hash='scope'))
    monkeypatch.setattr(context_services, 'retrieve', lambda *a, **k: {'status': 'PASS', 'evidence': []})
    monkeypatch.setattr(knowledge, 'Knowledge', lambda *a, **k: SimpleNamespace(search=None))
    monkeypatch.setattr(api, 'store', JobStore(tmp_path / 'db'))
    enqueued = []
    def fake_enqueue(req):
        job = {'id': 'job-async-1', 'status': 'QUEUED', 'result': {}}
        enqueued.append(req.model_dump())
        return job, {}
    monkeypatch.setattr(api, '_enqueue_report', fake_enqueue)
    def no_model(snapshot, evidence, use_cache=True, allow_model=True, gateway=None):
        assert allow_model is False, 'async 冷缓存路径不得发起模型调用'
        return {'status': 'DEGRADED', 'generation_mode': 'rules', 'findings': [{'claim_type': 'insufficient_evidence', 'rendered_text': '现有证据不足以确认差异原因。'}]}
    monkeypatch.setattr(narrative, 'generate', no_model)
    result = api.get_benchmark('P', '2026-05', 'A', 'B', context_id='pharmaceutical:competition')
    assert result['narrative']['model_status'] == 'QUEUED' and result['narrative']['job_id'] == 'job-async-1'
    assert result['narrative']['generation_mode'] == 'rules'
    assert enqueued and enqueued[0]['factory'] == 'A'
    # 已完成任务 → 直接复用其 narrative，不再入队新任务
    enqueued.clear()
    monkeypatch.setattr(api, '_enqueue_report',
                        lambda req: ({'id': 'job-done', 'status': 'SUCCEEDED',
                                      'result': {'narrative': {'status': 'PASS', 'generation_mode': 'llm', 'findings': []}}}, {}))
    result2 = api.get_benchmark('P', '2026-05', 'A', 'B', context_id='pharmaceutical:competition')
    assert result2['narrative']['generation_mode'] == 'llm' and 'model_status' not in result2['narrative']
    # 入队失败：响应保留规则解释并标注，不抛错
    def boom(req):
        raise ValueError('NO_COMPLETE_PERIOD_DATA')
    monkeypatch.setattr(api, '_enqueue_report', boom)
    result3 = api.get_benchmark('P', '2026-05', 'A', 'B', context_id='pharmaceutical:competition')
    assert result3['narrative']['model_status'] == 'ENQUEUE_FAILED'
    assert result3['narrative']['generation_mode'] == 'rules'


# ---------- AUD-KB-01：knowledge.search 分块/适用性缓存与副本隔离 ----------

def test_knowledge_search_caches_chunks_and_applicability_with_isolation(tmp_path, monkeypatch):
    import pharma.knowledge as km
    monkeypatch.setattr(km, '_CHUNK_CACHE', {})
    monkeypatch.setattr(km, '_APPLICABILITY_CACHE', {})
    src = tmp_path / 'k.json'
    src.write_text(json.dumps([
        {'id': 'a', 'products': ['P1'], 'text': '银黄口服液配方含金银花与黄芩提取物，需核对用量与批次记录。'},
        {'id': 'b', 'products': ['P2'], 'text': '另一产品工艺说明：浓缩与制粒工序的温度控制要求完整记录。'},
    ], ensure_ascii=False))
    knowledge = km.Knowledge(root=tmp_path, source_files=(src,), vector_enabled=False)
    first = knowledge.search('配方 金银花', product='P1', mode='bm25')
    second = knowledge.search('配方 金银花', product='P1', mode='bm25')
    assert first['status'] == second['status'] == 'PASS'
    assert [e['evidence_id'] for e in first['evidence']] == [e['evidence_id'] for e in second['evidence']]
    # 命中路径：分块与适用性进入进程内缓存
    assert km._CHUNK_CACHE and km._APPLICABILITY_CACHE
    # 副本隔离：调用方修改返回的 evidence 内层结构不污染缓存
    if first['evidence'][0].get('products'):
        first['evidence'][0]['products'].append('POLLUTED')
    first['evidence'][0]['applicability']['reasons'].append('POLLUTED')
    third = knowledge.search('配方 金银花', product='P1', mode='bm25')
    assert all('POLLUTED' not in (e.get('products') or []) for e in third['evidence'])
    assert all('POLLUTED' not in e['applicability']['reasons'] for e in third['evidence'])
    # 不同过滤参数不串缓存：P2 只命中 b 分块
    other = knowledge.search('工艺 制粒', product='P2', mode='bm25')
    assert other['evidence'] and all('浓缩' in e['text'] for e in other['evidence'])
    # 索引重建（源变化→新版本指纹）后缓存自然失效出新结果
    src.write_text(json.dumps([
        {'id': 'a', 'products': ['P1'], 'text': '银黄口服液配方含金银花与黄芩提取物，需核对用量与批次记录。'},
        {'id': 'b', 'products': ['P2'], 'text': '另一产品工艺说明：浓缩与制粒工序的温度控制要求完整记录。'},
        {'id': 'c', 'products': ['P1'], 'text': '新增分块：金银花市场行情上涨说明与采购核查要求逐条记录。'},
    ], ensure_ascii=False))
    knowledge2 = km.Knowledge(root=tmp_path, source_files=(src,), vector_enabled=False)
    knowledge2.build()  # 真实链路（worker）检索前总是幂等 build；search 仅在术语变化时自动重建
    refreshed = knowledge2.search('行情 上涨', product='P1', mode='bm25')
    assert any('行情' in e['text'] for e in refreshed['evidence'])
