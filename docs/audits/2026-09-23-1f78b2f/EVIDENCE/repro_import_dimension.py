# -*- coding: utf-8 -*-
"""AUD-P0-1 隔离复现：题包成本汇总 CSV 经数据中心自助导入（UI 同款链路）后总成本量纲。

链路：create_upload(cost_summary) → import_pipeline._mapping_for → _options_for
      → data_import.validate_business → publish_business → industry.analyze_reference
隔离：PHARMA_RUNTIME_DIR 指向审查专用临时目录，不触碰主工作区 .runtime。
"""
import os, sys, json

BACKEND = r'D:/yaoheng-audit-wt-1f78b2f/药衡智析_增量源码交接/public_source_candidate/05_原型/backend'
REPRO_RUNTIME = r'D:/重庆市AI大赛/docs/audits/2026-09-23-1f78b2f/EVIDENCE/repro_runtime'
CSV_PATH = (r'D:/yaoheng-audit-wt-1f78b2f/药衡智析_增量源码交接/public_source_candidate/'
            r'00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据/01_成本明细数据/中药一厂_成本汇总_2026年1-6月.csv')

os.environ['PHARMA_RUNTIME_DIR'] = REPRO_RUNTIME
sys.path.insert(0, BACKEND)

from pharma import data_import, import_pipeline  # noqa: E402

payload = open(CSV_PATH, 'rb').read()
record = data_import.create_upload('business', '中药一厂_成本汇总_2026年1-6月.csv', payload, 'cost_summary')
print('upload ok, meta.preview.headers =', record['meta'].get('preview', {}).get('headers'))

mapping, note = import_pipeline._mapping_for(record)
print('mapping note:', note)
print('mapping:', json.dumps(mapping, ensure_ascii=False))
options = import_pipeline._options_for(record)
print('options:', options)

validation = data_import.validate_business(record, mapping, options)
print('validation status:', validation['status'], 'errors:', validation.get('error_count'),
      'warnings:', len(validation.get('warnings', [])))
if validation['status'] != 'VALID':
    print('first errors:', validation['errors'][:5])

if validation['status'] == 'VALID':
    published = data_import.publish_business(record, mapping, options,
                                             enterprise_name='审查复现企业', pack_id='pharmaceutical',
                                             quantity_unit='盒')
    print('published:', {k: published[k] for k in ('enterprise_id', 'context_id', 'dataset_facts')})
    context_id = published['context_id']
    from pharma.industry import analyze_reference
    snap = analyze_reference(context_id, factory='中药一厂', product='银黄口服液',
                             month='2026-01', analysis_type='monthly', basis='unit')
    m = snap['metrics']
    print('--- 发布后 analyze_reference（中药一厂/银黄口服液/2026-01）---')
    for k in ('quantity', 'unit_cost', 'total_cost'):
        print(f'{k:12s} = {m[k]["value"]} {m[k]["unit"]}')
    # 独立真值（出题方问题检查报告口径：总成本=产量×单位成本）
    import csv as _csv, io
    rows = list(_csv.DictReader(io.StringIO(payload.decode('utf-8-sig'))))
    truth = [r for r in rows if r.get('产品') == '银黄口服液' and r.get('月份') in ('2026-01', '2026年1月', '2026-1')]
    if not truth:  # 表头/月份格式兜底打印首行看列名
        print('CSV columns:', list(rows[0].keys()))
        print('CSV first row:', rows[0])
    else:
        r = truth[0]
        qty = r.get('产量(盒)') or r.get('产量')
        total = r.get('总成本(元)') or r.get('总成本')
        print(f'--- 题包真值: 产量={qty} 盒, 总成本={total} 元 ---')
