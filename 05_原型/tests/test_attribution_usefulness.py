"""Useful, bounded attribution: preserve reasoning and require testable alternatives."""
import pytest
import json
import httpx
from pharma.narrative import ModelGateway, generate
from pharma.narrative import compile_task_explanations, validate_findings, diagnostic_text, DiagnosticPath
from test_benchmark_explanation_contract import snap, explanation


def test_validated_diagnostic_reasoning_survives_visible_output():
    text = '需核查工资水平与单位工时差异，若单位工时接近则优先核查薪酬记录。补齐两厂工时与工资台账后可分解工时效率和工资率影响，尚不能直接认定为效率差异。'
    rows = compile_task_explanations([explanation('benchmark', text_template=text)], snap())
    rendered = validate_findings(rows, snap(), [])[0]['rendered_text']
    assert text in rendered


def test_calculated_driver_ranking_cannot_pass_with_only_missing_records():
    snapshot = snap()
    snapshot['attribution'] = {'status': 'PASS', 'root_causes': [{'set': '要素：材料'}]}
    with pytest.raises(ValueError, match='DIAGNOSTIC_PATHS_REQUIRED'):
        compile_task_explanations([explanation('benchmark')], snapshot)


def paths():
    return [
        dict(mechanism='采购结算价格偏高可能推高材料单位成本',
             basis='材料成本差异提示需优先核查采购价格路径',
             verification='若同规格采购单价偏高则支持该推测，否则降低价格路径优先级',
             data_needed=['两厂同规格采购结算单价记录','两厂同批次实耗与合格产出记录'],
             expected_result='可分解采购价差贡献并区分单位耗用影响'),
        dict(mechanism='单位耗用增加可能推高材料单位成本',
             basis='材料差异也可能来自实物投入与合格产出关系',
             verification='若单位耗用偏高则支持损耗路径，否则排除耗用增加推测',
             data_needed=['两厂批次投料与合格产出记录'],
             expected_result='可量化单位耗用差并定位需要复核的批次')]


def test_generated_paths_are_visible_and_retry_replaces_cold_checklist(tmp_path):
    snapshot=snap();snapshot['attribution']={'status':'PASS','root_causes':[{'set':'材料','direction':'上升'}]}
    requests=[]
    def respond(request):
        requests.append(json.loads(request.content))
        rows=[explanation(s,**({'diagnostic_paths':paths()} if len(requests)>1 else {})) for s in ('materials','benchmark')]
        return httpx.Response(200,json={'model':'controlled-model','choices':[{'message':{'content':json.dumps({'explanations':rows})}}]})
    gw=ModelGateway(runtime=tmp_path,client=httpx.Client(transport=httpx.MockTransport(respond)),
                    model='controlled-model',api_key='fixture',max_repairs=1)
    result=generate(snapshot,[],gateway=gw,use_cache=False)
    assert len(requests)==2 and result['status']=='PASS'
    assert any('DIAGNOSTIC_PATHS_REQUIRED' in f for f in result['failure_reasons'])
    for finding in result['findings']:
        if finding.get('origin')=='model':
            assert '采购价差贡献' in finding['rendered_text']
            assert '否则排除耗用增加推测' in finding['rendered_text']


@pytest.mark.parametrize('change',[
    {'verification':'请补齐更多资料以后进行进一步核查'},
    {'expected_result':'可以提供更加准确有用的分析结果'},
    {'mechanism':'已证实采购价格直接导致成本增加'},
    {'mechanism':'采购价格上涨导致成本增加但仍需核查'},
])
def test_empty_or_certain_diagnostic_promises_rejected(change):
    entries=paths();entries[0].update(change)
    with pytest.raises(ValueError):
        compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())


def test_diagnostic_fields_still_reject_invented_numbers():
    entries=paths();entries[0]['basis']='采购价格可能上涨98765元需要核查'
    rows=compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    with pytest.raises(ValueError,match='free business number'):
        validate_findings(rows,snap(),[])


def test_insufficient_label_cannot_hide_affirmative_causality():
    rows=compile_task_explanations([explanation('benchmark',text_template='需核查工资记录，但工资上涨导致差异扩大。')],snap())
    with pytest.raises(ValueError,match='causality'):
        validate_findings(rows,snap(),[])


def test_price_and_usage_decomposition_cannot_be_promised_from_prices_alone():
    entries=paths();entries[0]['data_needed']=['两厂采购结算单价记录']
    entries[1]['data_needed']=['两厂采购发票明细']
    with pytest.raises(ValueError,match='price/usage decomposition'):
        diagnostic_text([DiagnosticPath.model_validate(p) for p in entries])


@pytest.mark.parametrize('section,prefix',[('materials','本期及基期'),('benchmark','两厂同期间')])
def test_compiler_completes_decomposition_data_plan_without_inventing_facts(section,prefix):
    entries=paths()
    for path in entries:path['data_needed']=['对应月份采购合同记录']
    rows=compile_task_explanations([explanation(section,diagnostic_paths=entries)],snap())
    finding=validate_findings(rows,snap(),[])[0]
    plan=prefix+'同规格原料实际采购单价与同批次实耗及合格产出对照明细'
    assert finding['diagnostic_plan_additions']==[plan]
    assert plan in finding['rendered_text'] and plan in finding['missing_evidence']
    assert '采购结算价格偏高可能' in finding['rendered_text']
    assert finding['claim_type']=='insufficient_evidence'


def test_meeting_yield_standard_does_not_exclude_period_deterioration():
    entries=paths();entries[1]['mechanism']='提取收率下降可能增加材料单位耗用'
    entries[1]['verification']='若收率低于工艺标准则支持该推测，若收率达标则排除该推测'
    with pytest.raises(ValueError,match='yield change'):
        compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    entries[1]['verification']='若收率低于同口径基期则支持该推测，若收率未下降则降低该推测'
    rows=compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    assert '同口径基期' in validate_findings(rows,snap(),[])[0]['rendered_text']


def test_counter_observation_can_redirect_to_another_mechanism():
    entries=paths()
    entries[0]['verification']='若本期采购单价高于基期则支持该推测，若采购单价持平则应转向耗用机制'
    rows=compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    assert '转向耗用机制' in validate_findings(rows,snap(),[])[0]['rendered_text']


def test_natural_punctuation_and_equivalent_attribution_gain_survive():
    entries=paths()
    entries[0]['verification']='若采购单价偏高则支持该推测；若采购单价相近则转向耗用机制。'
    entries[0]['expected_result']='分离采购价格与实物耗用对材料成本的影响'
    rows=compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    text=validate_findings(rows,snap(),[])[0]['rendered_text']
    assert '分离采购价格与实物耗用' in text and '转向耗用机制' in text


def test_shared_task_data_plan_can_support_both_hypotheses():
    entries=paths();entries[0]['data_needed']=['两厂同规格采购结算单价记录']
    rows=compile_task_explanations([explanation('benchmark',diagnostic_paths=entries)],snap())
    finding=validate_findings(rows,snap(),[])[0]
    assert '两厂批次投料与合格产出记录' in finding['missing_evidence']


def test_two_periods_is_a_valid_comparison_data_plan():
    entries=paths()
    for entry in entries:
        entry['data_needed']=[x.replace('两厂','两期') for x in entry['data_needed']]
    rows=compile_task_explanations([explanation('materials',diagnostic_paths=entries)],snap())
    assert '两期同规格采购结算单价记录' in validate_findings(rows,snap(),[])[0]['missing_evidence']


def test_large_report_batches_tasks_without_repeating_frozen_explanations(tmp_path):
    snapshot=snap()
    for section in ('labor','overhead'):
        snapshot['elements'].append({'key':section,'name':section,'unit_delta':'1'})
        snapshot['metrics'][section]={'metric_id':'monthly:'+section,'display':'3.00','unit':'元/件'}
    snapshot['alerts']=[{'element_key':s,'basis':'unit'} for s in ('labor','overhead')]
    requested=[]
    def respond(request):
        body=json.loads(request.content)
        payload=json.JSONDecoder().raw_decode(body['messages'][1]['content'])[0]
        tasks=payload['tasks'];requested.append([t['section'] for t in tasks])
        # Captured S3/Q2 failure pattern: the large request exhausts output tokens.
        content='{"explanations":[' if len(tasks)>2 else json.dumps({'explanations':[explanation(t['section']) for t in tasks]})
        return httpx.Response(200,json={'model':'controlled-model','choices':[{'message':{'content':content}}]})
    gateway=ModelGateway(runtime=tmp_path,client=httpx.Client(transport=httpx.MockTransport(respond)),
                         model='controlled-model',api_key='fixture',max_repairs=2)
    result=generate(snapshot,[],gateway=gateway,use_cache=False)
    assert result['status']=='PASS',result['failure_reasons']
    assert len(requested)==2
    assert sorted(s for batch in requested for s in batch)==['benchmark','labor','materials','overhead']
    assert all(v['status']=='PASS' for v in result['unit_validation'].values())
