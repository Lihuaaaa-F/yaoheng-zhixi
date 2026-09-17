"""Synthetic regressions for immutable repair units and typed planned time."""
import json
import httpx
import pytest
from pharma.narrative import ModelGateway, generate, validate_findings


def snapshot():
    return {'month':'2031-05','period':{'start':'2031-05','end':'2031-05'},
            'metrics':{'materials':{'display':'10','unit':'元/件','comparison_period':['2031-04']}},
            'elements':[{'key':'materials','name':'合成材料','unit_delta':'1'}]}


def action(**changes):
    out={'suggestion':'核查原料归集记录','verification_target':'原料成本变化来源','expected_evidence':['实际采购价格记录'],
         'responsible_role':'待分配','department':'成本核算部门','priority':'medium','deadline_basis':'月度成本复核前'}
    return {**out,**changes}


def row(**changes):
    return {'task_id':'explain:materials','claim_type':'insufficient_evidence','text_template':'现有证据不足以确认原因，需核查采购记录。',
            'missing_evidence':['实际采购价格记录'],'recommendation':None,**changes}


def run(tmp_path,responses):
    calls=[]
    def reply(request):
        content=responses[min(len(calls),len(responses)-1)];calls.append(json.loads(request.content))
        return httpx.Response(200,json={'model':'glm-5.3-flash','choices':[{'message':{'content':json.dumps({'explanations':content})}}]})
    key=tmp_path/'key';key.write_text('synthetic-key')
    gateway=ModelGateway(client=httpx.Client(transport=httpx.MockTransport(reply)),runtime=tmp_path,key_file=key,model='glm-5.3-flash',max_repairs=1)
    return generate(snapshot(),[],gateway,use_cache=False),calls


def test_valid_explanation_is_frozen_while_action_is_repaired(tmp_path):
    first=row(recommendation=action(suggestion='预计节省100元'))
    second=row(text_template='已证实采购直接导致成本上升。',recommendation=action())
    out,calls=run(tmp_path,[[first],[second]])
    assert out['status']=='PASS' and len(calls)==2
    model=[f for f in out['findings'] if f.get('origin')=='model']
    assert len(model)==2 and all('已证实' not in f['text'] for f in model)


def test_repair_can_supply_only_the_failed_action_unit(tmp_path):
    out,_=run(tmp_path,[[row(recommendation=action(suggestion='预计节省100元'))],[{'task_id':'explain:materials','recommendation':action()}]])
    assert out['status']=='PASS'


def test_omitting_failed_action_does_not_clear_its_failure(tmp_path):
    out,_=run(tmp_path,[[row(recommendation=action(suggestion='预计节省100元'))],[row()]])
    assert out['status']=='DEGRADED'
    assert any('recommendation' in str(x) for x in out.get('unit_validation',{}))


def test_valid_action_is_frozen_while_explanation_is_repaired(tmp_path):
    first=row(text_template='已证实采购直接导致成本上升。',recommendation=action())
    second=row(recommendation=action(suggestion='预计节省100元'))
    out,_=run(tmp_path,[[first],[second]])
    assert out['status']=='PASS'
    assert all('100' not in f['text'] for f in out['findings'] if f.get('origin')=='model')


def test_actual_and_comparison_months_normalize_only_when_bound():
    f={'claim_type':'insufficient_evidence','text_template':'现有证据不足以确认原因。',
       'missing_evidence':['2031年5月与2031年4月实际采购价格记录']}
    accepted=validate_findings([f],snapshot(),[])[0]
    assert accepted['missing_evidence']==['2031-05与2031-04实际采购价格记录']
    for value in ['2031年3月采购价格记录','2031-03采购价格记录','2031年5月7日采购价格记录']:
        with pytest.raises(ValueError,match='number'):
            validate_findings([{**f,'missing_evidence':[value]}],snapshot(),[])


def test_deadline_workdays_are_typed_proposals_not_cost_facts():
    f={'claim_type':'recommendation','text_template':'核查采购记录',**action(deadline_basis='月度成本结账后5个工作日内')}
    result=validate_findings([f],snapshot(),[])[0]
    assert result['deadline_proposal']['working_days']==5
    assert result['deadline_proposal']['requires_confirmation'] is True
    assert any(b['type']=='proposed_deadline' for b in result['numeric_bindings'])
    with pytest.raises(ValueError,match='number'):
        validate_findings([{**f,'suggestion':'核查后节省5元'}],snapshot(),[])


@pytest.mark.parametrize('deadline',['月度成本结账后0个工作日内','月度成本结账后31个工作日内','月度成本结账后5个工作日内节省100元','产品每件5元'])
def test_deadline_proposal_bounds_and_non_deadline_numbers_remain_strict(deadline):
    with pytest.raises(ValueError):
        validate_findings([{'claim_type':'recommendation','text_template':'核查采购记录',**action(deadline_basis=deadline)}],snapshot(),[])
