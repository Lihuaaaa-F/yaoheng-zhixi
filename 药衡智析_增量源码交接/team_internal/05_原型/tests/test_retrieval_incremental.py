import json
import pytest
from pharma.knowledge import Knowledge
from pharma.narrative import validate_findings, generate, ModelGateway


def test_unknown_scope_is_not_general():
    assert not Knowledge.product_matches({'products': [], 'text': '提取收率达到要求'}, '板蓝根颗粒')
    assert Knowledge.product_matches({'products': [], 'scope': 'general', 'text': '通用质量记录应留存'}, '板蓝根颗粒')


def test_real_process_page_inherits_product_section():
    k = Knowledge()
    k.build()
    evidence = k.search('板蓝根提取收率', product='板蓝根颗粒', mode='bm25', limit=20)['evidence']
    assert any(e['page'] == 3 and '工艺' in e['source'] and '82%' in e['text'] for e in evidence)
    assert not any('85%' in e['text'] and '工艺' in e['source'] for e in evidence)


def test_wrong_period_factory_spec_and_version_are_rejected():
    ev={'products':['板蓝根颗粒'],'scope':'product','event_period':'2025-08','factory':'中药一厂','specification':'10g*20袋','document_version':'V3'}
    assert not Knowledge.evidence_applicability(ev, product='板蓝根颗粒', period={'start':'2026-05','end':'2026-05'})['applicable']
    for key,value in [('factory','中药二厂'),('specification','10g*10袋'),('document_version','V2')]:
        assert not Knowledge.evidence_applicability(ev, product='板蓝根颗粒', **{key:value})['applicable']


def test_context_and_positioned_document_numbers_are_typed():
    snap={'product':'板蓝根颗粒','month':'2026-05','specification':'10g*20袋','metrics':{}}
    ev={'evidence_id':'e','products':['板蓝根颗粒'],'scope':'product','source':'工艺.pdf','page':3,'text':'提取收率≥82%','location':'第3页'}
    f={'claim_type':'recommendation','text_template':'核查[[context:month]]的[[context:specification]]产品，工艺要求[[evidence:e]]。','evidence_refs':['e'],'evidence_quotes':{'e':'提取收率≥82%'}}
    out=validate_findings([f],snap,[ev])
    assert '2026-05' in out[0]['text'] and '≥82%' in out[0]['text']
    with pytest.raises(ValueError,match='number'):
        validate_findings([{'claim_type':'recommendation','text_template':'预计节约82元'}],snap,[ev])


def test_one_invalid_finding_preserves_valid_model_section(tmp_path):
    import httpx
    good={'claim_type':'numeric_fact','section':'summary','text_template':'本期指标','metric_refs':['cost']}
    bad={'claim_type':'hypothesis','section':'materials','text_template':'成本上涨8500元','hypothesis':True}
    payload=json.dumps({'findings':[good,bad]})
    client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'choices':[{'message':{'content':payload}}]})))
    key=tmp_path/'key';key.write_text('synthetic-key')
    g=ModelGateway(client=client,runtime=tmp_path,key_file=key,max_repairs=0)
    out=generate({'metrics':{'cost':{'display':'7.47','unit':'元/盒'}}},[],gateway=g,use_cache=False)
    assert out['model_live'] is True
    assert out['generation_mode']=='mixed'
    assert out['section_validation']['summary']['status']=='PASS'
    assert out['section_validation']['materials']['status']=='DEGRADED'
    assert any(f.get('origin')=='model' and '7.47' in f['text'] for f in out['findings'])


def test_glm_default_contract_has_no_deepseek_thinking(tmp_path,monkeypatch):
    import httpx
    for key in ('PHARMA_MODEL','PHARMA_MODEL_BASE_URL','PHARMA_MODEL_PROTOCOL'):monkeypatch.delenv(key,raising=False)
    requests=[]
    def reply(request):
        requests.append(request)
        return httpx.Response(200,json={'choices':[{'message':{'content':'{}'}}]})
    key=tmp_path/'key';key.write_text('synthetic-key')
    g=ModelGateway(runtime=tmp_path,key_file=key,client=httpx.Client(transport=httpx.MockTransport(reply)))
    g.complete('test','test')
    body=json.loads(requests[0].content)
    assert g.model=='glm-5.3-flash'
    assert str(requests[0].url)=='https://open.bigmodel.cn/api/paas/v4/chat/completions'
    assert 'thinking' not in body


def test_real_maintenance_events_are_individual_rows_and_period_filtered():
    k=Knowledge();k.build()
    chunks=json.loads((k.path/k.version/'chunks.json').read_text())
    events=[e for e in chunks if e.get('event_period')]
    assert {e['event_period'] for e in events}=={'2026-03','2025-11','2025-08','2025-05'}
    result=k.search('板蓝根颗粒分装机切刀磨损',product='板蓝根颗粒',period={'start':'2026-05','end':'2026-05'},mode='bm25',limit=20)
    assert not any(e.get('event_period') for e in result['evidence'])


def test_rules_retain_known_drivers_and_executable_actions():
    from pharma.metrics import analyze
    from pharma.narrative import rule_findings
    out=rule_findings(analyze('中药一厂','板蓝根颗粒','2026-05'),[])
    texts=' '.join(f['text'] for f in out)
    assert all(value in texts for value in ('2.90','3.05','83.33%','131940.00','84000.00','47940.00'))
    tasks=[f for f in out if f['claim_type']=='recommendation']
    assert len(tasks)>=3
    for item in tasks:
        assert all(item[k] for k in ('suggestion','verification_target','expected_evidence','department','responsible_role','priority','deadline_basis'))
    assert not any(f.get('claim_type')=='document_fact' for f in out)


def test_registered_literal_date_specification_and_document_parameter_are_not_free_costs():
    snap={'product':'板蓝根颗粒','month':'2026-05','specification':'10g*20袋'}
    ev={'evidence_id':'e','products':['板蓝根颗粒'],'scope':'product','text':'提取收率≥82%','location':'第3页'}
    f={'claim_type':'recommendation','text_template':'核查2026-05的10g*20袋产品，工艺要求提取收率≥82%。','evidence_refs':['e'],'evidence_quotes':{'e':'提取收率≥82%'}}
    out=validate_findings([f],snap,[ev])
    assert {x['type'] for x in out[0]['numeric_bindings']}=={'date','specification','positioned_document'}
    with pytest.raises(ValueError,match='number'):
        validate_findings([{**f,'text_template':'预计节省82元，核查2026-05的10g*20袋产品。'}],snap,[ev])


def test_no_evidence_and_conflicting_process_parameters_do_not_become_hypotheses():
    f={'claim_type':'hypothesis','section':'materials','hypothesis':True,'text_template':'提取收率已证实导致材料增加','metric_refs':['cost'],'evidence_refs':['e'],'evidence_quotes':{'e':'提取收率≥82%'},'missing_evidence':['实际批次记录']}
    snapshot={'product':'板蓝根颗粒','metrics':{'cost':{'display':'7.47','unit':'元/盒'}}}
    with pytest.raises(ValueError,match='unknown evidence'):
        validate_findings([f],snapshot,[])
    with pytest.raises(ValueError,match='causality'):
        validate_findings([f],snapshot,[{'evidence_id':'e','text':'提取收率≥82%','products':['板蓝根颗粒'],'location':'第3页'}])


def test_runtime_coding_endpoint_is_rejected(tmp_path):
    with pytest.raises(ValueError,match='CODING_ENDPOINT'):
        ModelGateway(runtime=tmp_path,base_url='https://open.bigmodel.cn/api/coding/paas/v4')


def test_conflicting_document_versions_are_excluded_before_model(tmp_path,monkeypatch):
    for key in ('PHARMA_API_KEY','GLM_API_KEY','ZHIPU_API_KEY','PHARMA_API_KEY_FILE','PHARMA_MODEL_KEY_FILE'):monkeypatch.delenv(key,raising=False)
    evidence=[{'evidence_id':str(i),'document_number':'MFG-YC01','document_version':v,'text':'提取收率≥'+rate+'%','products':['板蓝根颗粒'],'location':'第3页'} for i,(v,rate) in enumerate([('V2','85'),('V3','82')])]
    out=generate({'product':'板蓝根颗粒'},evidence,gateway=ModelGateway(runtime=tmp_path),use_cache=False)
    assert len(out['excluded_evidence'])==2
    assert all('多个版本' in e['reasons'][-1] for e in out['excluded_evidence'])
    assert not out['model_live']


def test_knowledge_default_respects_external_package_runtime_and_embeddings(tmp_path,monkeypatch):
    import pharma.knowledge as module
    data=tmp_path/'external-data';runtime=tmp_path/'external-runtime';models=tmp_path/'licensed-model'
    monkeypatch.setattr(module,'PACKAGE',data)
    monkeypatch.setattr(module,'RUNTIME',runtime)
    monkeypatch.setenv('PHARMA_EMBEDDING_DIR',str(models))
    k=Knowledge()
    assert k.source_dir==data/'03_制药知识文档'
    assert k.path==runtime/'knowledge'
    assert k.model_dir==models


def test_explicit_test_root_keeps_isolated_defaults_with_external_package(tmp_path,monkeypatch):
    import pharma.knowledge as module
    monkeypatch.setattr(module,'PACKAGE',tmp_path/'unrelated-external-data')
    monkeypatch.setattr(module,'RUNTIME',tmp_path/'unrelated-runtime')
    monkeypatch.delenv('PHARMA_EMBEDDING_DIR',raising=False)
    k=Knowledge(root=tmp_path/'isolated-project')
    assert k.source_dir==tmp_path/'isolated-project/00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据/03_制药知识文档'
    assert k.path==tmp_path/'isolated-project/05_原型/.runtime/knowledge'
    assert k.model_dir==tmp_path/'isolated-project/05_原型/.runtime/models/bge-small-zh-v1.5'


def test_rule_action_priorities_match_task_api_contract():
    from pharma.metrics import analyze
    from pharma.narrative import rule_findings
    actions=[f for f in rule_findings(analyze('中药一厂','板蓝根颗粒','2026-05'),[]) if f['claim_type']=='recommendation']
    assert actions and all(f['priority'] in ('high','medium','low') for f in actions)
    assert actions[0]['priority']=='high'


def test_real_index_excludes_product_heading_without_section_body():
    k=Knowledge();k.build()
    chunks=json.loads((k.path/k.version/'chunks.json').read_text())
    assert not any(e['source']=='生产工艺文档_中药一厂.pdf' and e['page']==2 and e.get('products')==['板蓝根颗粒'] for e in chunks)


def test_current_capsule_maintenance_supports_bounded_hypothesis_but_not_other_periods():
    from pharma.metrics import analyze
    from pharma.narrative import rule_findings
    k=Knowledge()
    result=k.search('胶囊填充机 维修 停机',product='六味地黄胶囊',factory='中药一厂',period={'start':'2026-03','end':'2026-03'})
    out=rule_findings(analyze('中药一厂','六味地黄胶囊','2026-03'),result['evidence'])
    hypotheses=[f for f in out if f['claim_type']=='hypothesis' and f.get('section')=='overhead']
    assert len(hypotheses)==1
    h=hypotheses[0]
    assert '计量盘磨损' in h['text'] and '可能' in h['text'] and '不等于本月净减产' in h['text']
    assert h['missing_evidence'] and h['metric_refs'] and h['evidence_refs']
    assert not any(token in h['text'] for token in ('8500','8,500','12000','24'))
    later=rule_findings(analyze('中药一厂','六味地黄胶囊','2026-05'),result['evidence'])
    assert not any(f['claim_type']=='hypothesis' and f.get('section')=='overhead' for f in later)
    other=rule_findings(analyze('中药一厂','板蓝根颗粒','2026-03'),result['evidence'])
    assert not any(f['claim_type']=='hypothesis' and f.get('section')=='overhead' for f in other)
