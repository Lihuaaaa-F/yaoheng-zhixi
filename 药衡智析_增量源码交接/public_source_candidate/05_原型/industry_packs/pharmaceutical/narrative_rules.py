"""Trusted pharmaceutical competition rules. No numeric inference by a model.

This file is registered explicitly by the core; an uploaded manifest cannot
select an executable path. Edit with the original pharmaceutical regressions.
"""
from decimal import Decimal


def append_findings(snapshot, evidence, findings, *, elements, metric_id, number, fact, action):
    from pharma.narrative import validate_findings
    by_key = snapshot.get('metrics', {})
    materials=snapshot.get('materials_summary',[])
    material_drivers=[r for r in materials if r.get('delta') is not None and Decimal(r['delta'])!=0]
    if material_drivers:
        row=material_drivers[0]; refs=row['metric_refs']
        text=row['name']+'每盒消耗成本由'+number(refs['previous'])+'变为'+number(refs['current'])
        if row.get('contribution') is not None:text+='，占材料环比变动的'+number(refs['contribution'])
        fact('materials',text+'，是优先核查的材料差异来源。',list(refs.values()),row.get('source_labels'))
        action('materials','现有明细已定位主要原料驱动；价格与实物耗用的影响尚未分开。',row['name']+'本期与上期采购和批次耗用',
               ['实际采购合同及入库单价','批次投料、合格产出与收率记录'],'采购部、生产部、财务部',
               '按同批次核对采购价、投料与合格产出，分别检查采购变化和生产损耗；工艺调整须经质量部门批准。')
        # A process limit supports a possible mechanism, never an assertion
        # that this month's process actually deteriorated.
        for ev in evidence:
            from pharma.knowledge import Knowledge
            if not Knowledge.evidence_applicability(ev,product=snapshot.get('product'),factory=snapshot.get('factory'),period=snapshot.get('period'),specification=snapshot.get('specification'),context=snapshot.get('analysis_context'))['applicable']:continue
            quote=next((line.strip() for line in ev.get('text','').splitlines() if '提取收率' in line and 4<=len(line.strip())<=180),None)
            if not quote:continue
            candidate={'claim_type':'hypothesis','section':'materials','text_template':'提取收率变化可能影响每盒材料耗用；现有工艺文档给出控制要求，尚不能证明本期实际收率下降。需将批次投料和合格产出与上期对照核查。',
                'metric_refs':[metric_id(refs['delta'])],'evidence_refs':[ev['evidence_id']], 'evidence_quotes':{ev['evidence_id']:quote},
                'hypothesis':True,'missing_evidence':['本期及上期实际批次提取收率','同批次投料与合格产出']}
            try:
                item=validate_findings([candidate],snapshot,evidence)[0]
            except ValueError:continue
            item['origin']='rules';findings.append(item)
            break
    elif snapshot.get('elements'):
        action('materials','已能比较材料总差异，但当前工厂缺少可完整对照的原料明细。','同产品、同规格、同期间原料明细',
               ['原料成本明细','采购与批次耗用台账'],'财务部、采购部、生产部',
               '补齐对应期间明细并与材料总账勾稽，再按原料排序核查；不按比例推算缺失工厂数据。')
    bridge=snapshot.get('budget_bridge')
    if bridge and bridge.get('metric_refs'):
        refs=bridge['metric_refs']
        fact('summary','实际总成本与预算相差'+number(refs['total_delta'])+'，其中产量影响为'+number(refs['quantity_effect'])+'，单位成本影响为'+number(refs['unit_cost_effect'])+'。产量影响不能全部解释为效率恶化。',list(refs.values()))
    labor=next((e for e in elements if e['key']=='labor' and e.get('unit_delta') is not None and Decimal(e['unit_delta'])!=0),None)
    if labor:
        action('labor','人工单位成本存在差异；题包平均小时工资是折算结果，不能据此断言基础薪率上涨。','本期与上期工时、工资组成和合格产量',
               ['班次及加班记录','工资组成与工时台账','返工工时与合格产量'],'生产部、人力资源部、财务部',
               '核对人员结构、加班及返工工时，区分每盒工时变化与人工费用结构变化。',priority='medium')
    overhead=next((e for e in elements if e['key']=='overhead' and e.get('unit_delta') is not None and Decimal(e['unit_delta'])!=0),None)
    if overhead:
        action('overhead','制造费用单位成本存在差异；事件记录不能直接作为本期新增费用。','本期费用分配、维修入账与设备运行',
               ['费用分配表及分配基数','本期维修工单与入账凭证','停机和能耗记录'],'设备部、财务部、生产部',
               '逐项核对费用总额、分配基数和产量影响，仅将本期适用工单用于原因核查，避免重复计入维修费。',priority='medium')
    for ev in evidence:
        from pharma.knowledge import Knowledge
        if not snapshot.get('period') or not ev.get('event_period'):continue
        if not Knowledge.evidence_applicability(ev,product=snapshot.get('product'),factory=snapshot.get('factory'),period=snapshot.get('period'),specification=snapshot.get('specification'),context=snapshot.get('analysis_context'))['applicable']:continue
        event_text=ev.get('text','')
        if not all(term in event_text for term in ('计量盘磨损','装量','偏差')):continue
        refs=[metric_id(k) for k in ('materials_unit_delta','overhead_unit_delta') if k in by_key]
        if not refs:continue
        candidate={'claim_type':'hypothesis','section':'overhead','hypothesis':True,
            'text_template':'本期维修记录中的计量盘磨损可能引起装量偏差，进而影响材料损耗、返工工时和设备停工。事件中的局部产出损失不等于本月净减产；月度单位成本与总成本仍按汇总数据分别判断。需核对受影响批次与成本归集，维修费不得再次追加到汇总成本。',
            'metric_refs':refs,'evidence_refs':[ev['evidence_id']],'evidence_quotes':{ev['evidence_id']:event_text.strip()},
            'missing_evidence':['受影响批次装量偏差及物料损耗记录','停工与返工工时记录','维修费用入账与制造费用归集凭证']}
        try:item=validate_findings([candidate],snapshot,evidence)[0]
        except ValueError:continue
        item['origin']='rules';findings.append(item)
        break
    comparison=snapshot.get('benchmark_context')
    if comparison:
        for row in comparison.get('elements',[]):
            refs=row.get('metric_refs',{})
            if refs.get('delta'):
                text=comparison['direction']+'：'+row['name']+'差额'+number(refs['delta'])
                if row.get('contribution') is not None:text+='，占跨厂单位成本总差额'+number(refs['contribution'])
                fact('benchmark',text+'。',list(refs.values()))
        action('benchmark','跨厂三要素结构可以由汇总数据拆分；差异机制仍需两厂同口径明细支持。','两厂同规格产品成本归集、工时及费用分配',
               ['两厂原料明细','两厂工时和费用分配表','可比批次工艺记录'],'两厂财务部、生产部',
               '先核对两厂成本归集口径，再按材料、人工和制造费用差额检查主要项目；缺少二厂原料明细时保留缺项。')
