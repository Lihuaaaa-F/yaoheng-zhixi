"""Cross-factory explanation regressions using independent synthetic facts."""
import json
import httpx
import pytest
from pharma.narrative import ModelGateway,generate,validate_findings,explanation_tasks,compile_task_explanations


def snap(cross_metrics=True):
    metrics={'materials':{'metric_id':'monthly:materials','display':'12.00','unit':'元/件'}}
    if cross_metrics:
        metrics['benchmark:A:B:materials:delta']={'metric_id':'benchmark:A:B:materials:delta','display':'2.00','unit':'元/件'}
    return {'month':'2031-05','period':{'start':'2031-05','end':'2031-05'},'metrics':metrics,
        'elements':[{'key':'materials','name':'材料','unit_delta':'1'}],
        'benchmark_context':{'direction':'合成甲厂−合成乙厂，以合成乙厂为分母','left':'合成甲厂','right':'合成乙厂',
            'period':{'start':'2031-05','end':'2031-05'},'summary':[],
            'elements':[{'key':'materials','name':'材料','left':'12','right':'10','delta':'2','metric_refs':{'delta':'benchmark:A:B:materials:delta'}}],
            'limits':['仅合成归集成本；两厂缺采购与实物耗用明细']}}


def explanation(section='materials',**extra):
    return {'task_id':'explain:'+section,'claim_type':'insufficient_evidence','text_template':'现有证据不足以确认原因，需核查两厂同口径成本记录。',
            'missing_evidence':['两厂同口径成本归集明细'],**extra}


def execute(tmp_path,rows,snapshot=None):
    client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'model':'glm-5.3-flash','choices':[{'message':{'content':json.dumps({'explanations':rows})}}]})))
    key=tmp_path/'key';key.write_text('synthetic-key')
    gateway=ModelGateway(client=client,runtime=tmp_path,key_file=key,model='glm-5.3-flash',max_repairs=0)
    return generate(snapshot or snap(),[],gateway,use_cache=False)


def test_other_sections_pass_cannot_hide_missing_benchmark_explanation(tmp_path):
    out=execute(tmp_path,[explanation()])
    assert out['status']=='DEGRADED'
    assert 'benchmark' in out['required_explanation_sections']
    assert out['section_validation']['benchmark']['status']=='DEGRADED'


def test_cross_factory_task_binds_only_cross_metrics_and_accepts_action(tmp_path):
    action={'suggestion':'核对两厂同口径原料领用与费用分摊记录','verification_target':'两厂同期间成本归集差异',
            'expected_evidence':['两厂原料领用明细','两厂费用分摊记录'],'department':'两厂成本核算部门','responsible_role':'待分配',
            'priority':'high','deadline_basis':'月度成本复核前'}
    out=execute(tmp_path,[explanation(),explanation('benchmark',recommendation=action)])
    assert out['status']=='PASS'
    cross=[f for f in out['findings'] if f.get('origin')=='model' and f['section']=='benchmark']
    assert {f['claim_type'] for f in cross}=={'insufficient_evidence','recommendation'}
    assert all(f['metric_refs']==['benchmark:A:B:materials:delta'] for f in cross)
    assert '合成甲厂−合成乙厂' in cross[0]['text']


def test_benchmark_finding_cannot_reference_monthly_metric():
    f={'claim_type':'insufficient_evidence','section':'benchmark','text_template':'现有证据不足以归因。',
       'metric_refs':['monthly:materials'],'missing_evidence':['两厂成本归集记录']}
    with pytest.raises(ValueError,match='benchmark'):
        validate_findings([f],snap(),[])


def test_no_cross_metrics_does_not_fall_back_to_monthly_references():
    snapshot=snap(cross_metrics=False)
    task=next(t for t in explanation_tasks(snapshot) if t['section']=='benchmark')
    assert task['metric_refs']==[]
    compiled=compile_task_explanations([explanation('benchmark')],snapshot)
    assert validate_findings(compiled,snapshot,[])[0]['metric_refs']==[]
    compiled[0]['claim_type']='hypothesis';compiled[0]['hypothesis']=True
    with pytest.raises(ValueError):validate_findings(compiled,snapshot,[])


def test_explicitly_incomparable_context_does_not_promise_benchmark_attribution():
    snapshot=snap();snapshot['benchmark_context']['comparable']=False
    assert not any(t['section']=='benchmark' for t in explanation_tasks(snapshot))


@pytest.mark.parametrize('record',[
    '合成甲厂与合成乙厂同口径成本核算表',
    '两厂同口径产量与成本对比表',
    '两厂制造费用归集与分摊口径说明',
    '直接材料成本差异分析表',
    '直接人工成本计算单',
    '合成甲厂与合成乙厂同口径成本核算说明',
    '两厂2031-05同产品同规格成本核算口径说明',
    '合成甲厂与合成乙厂同口径产量与成本对照表',
])
def test_specific_business_cost_documents_are_valid_missing_evidence(record):
    compiled=compile_task_explanations([explanation('benchmark',missing_evidence=[record])],snap())
    assert validate_findings(compiled,snap(),[])[0]['missing_evidence']==[record]


@pytest.mark.parametrize('record',[
    '其他说明', '相关对比表', '有关核算表', '成本情况说明',
    '两厂生产工艺与产能利用情况说明', '成本核算情况说明',
    '成本核算口径说明已证实故障直接导致成本上升',
    '费用分摊口径说明已证实设备故障直接导致成本上升',
    '成本核算表证明设备故障是成本上升原因',
])
def test_vague_or_causal_disguised_document_is_rejected(record):
    compiled=compile_task_explanations([explanation('benchmark',missing_evidence=[record])],snap())
    with pytest.raises(ValueError,match='specific records'):
        validate_findings(compiled,snap(),[])
