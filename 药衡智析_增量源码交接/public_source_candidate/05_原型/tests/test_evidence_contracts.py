"""Independent synthetic regressions: no competition source material."""
import json
import sqlite3
import pytest
from pharma.narrative import validate_findings
from pharma.knowledge import Knowledge

@pytest.mark.parametrize('text,missing', [('', []), ('证据不足以归因。', []), ('证据不足以归因。', ['']), ('已证实设备故障直接导致成本上升。', ['设备运行记录']), ('现有证据不足。设备故障是成本上升的原因。', ['设备运行记录'])])
def test_insufficient_evidence_cannot_disguise_empty_or_certain_claim(text, missing):
    with pytest.raises(ValueError):
        validate_findings([{'claim_type':'insufficient_evidence','text_template':text,'missing_evidence':missing}], {}, [])

def test_legitimate_insufficient_evidence_has_specific_missing_records():
    finding={'claim_type':'insufficient_evidence','text_template':'现有证据不能支持材料上涨的机制归因。','missing_evidence':['采购合同','批次投料记录']}
    assert validate_findings([finding], {}, [])[0]['missing_evidence']==finding['missing_evidence']

def test_bm25_filters_scope_before_ranking_limit(tmp_path):
    source=tmp_path/'source'; source.mkdir()
    (source/'seed.txt').write_text('合成演示设备维护记录与成本核查需要核实具体生产批次。')
    knowledge=Knowledge(root=tmp_path,source_dir=source,vector_enabled=False)
    knowledge.build()
    path=knowledge.path/knowledge.version/'fts.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM chunks');db.execute('DELETE FROM search')
        for i in range(101):
            ident=f'e{i:03d}'
            row={'evidence_id':ident,'products':['target' if i==100 else 'other'],'text':'合成设备核查','source':'synthetic.txt','location':f'行{i+1}'}
            db.execute('INSERT INTO chunks VALUES (?,?)',(ident,json.dumps(row)))
            db.execute('INSERT INTO search VALUES (?,?)',(ident,'设备 '* (1 if i==100 else 5)))
    result=knowledge.search('设备',product='target',mode='bm25')
    assert [e['evidence_id'] for e in result['evidence']]==['e100']

def _gateway(tmp_path, responses):
    import httpx
    from pharma.narrative import ModelGateway
    calls=[]
    def respond(request):
        calls.append(json.loads(request.content))
        rows=responses[min(len(calls)-1,len(responses)-1)]
        return httpx.Response(200,json={'model':'glm-5.3-flash','choices':[{'message':{'content':json.dumps({'findings':rows})}}]})
    key=tmp_path/'key';key.write_text('synthetic-test-key')
    gateway=ModelGateway(client=httpx.Client(transport=httpx.MockTransport(respond)),runtime=tmp_path,key_file=key,max_repairs=1)
    return gateway,calls


def _missing(section='materials', alerts=()):
    return {'claim_type':'insufficient_evidence','section':section,'text_template':'现有证据不能支持成本变动归因。','missing_evidence':['批次生产记录'],'alert_refs':list(alerts)}


def test_every_alert_including_total_basis_requires_model_explanation(tmp_path):
    from pharma.narrative import generate
    snapshot={'metrics':{},'elements':[{'key':'materials','name':'材料','unit_delta':'2'},{'key':'energy','name':'能源','unit_delta':'1'}],
              'alerts':[{'alert_id':'a-unit','element_key':'materials','basis':'unit'}, {'alert_id':'a-total','element_key':'materials','basis':'total'}, {'alert_id':'b-unit','element_key':'energy','basis':'unit'}]}
    gateway,calls=_gateway(tmp_path,[[_missing('materials',['a-unit'])],[_missing('materials',['a-total']),_missing('energy',['b-unit'])]])
    out=generate(snapshot,[],gateway,use_cache=False)
    assert out['status']=='PASS' and len(calls)==2
    assert all(v['covered'] for v in out['alert_coverage'].values())
    assert out['required_explanation_sections']==['materials','energy']
    assert 'a-total' in calls[1]['messages'][-1]['content']


def test_partial_alert_coverage_cannot_pass(tmp_path):
    from pharma.narrative import generate
    snapshot={'elements':[{'key':'materials','name':'材料','unit_delta':'1'}],'alerts':[{'alert_id':'unit','element_key':'materials','basis':'unit'},{'alert_id':'total','element_key':'materials','basis':'total'}]}
    gateway,_=_gateway(tmp_path,[[_missing('materials',['unit'])]])
    out=generate(snapshot,[],gateway,use_cache=False)
    assert out['status']=='DEGRADED' and not out['alert_coverage']['total']['covered']


def test_all_action_fields_use_typed_renderer_and_reject_residuals():
    finding={'claim_type':'recommendation','text_template':'核查生产记录','suggestion':'核对[[context:month]]记录','verification_target':'[[context:product]]生产记录','expected_evidence':['[[context:month]]批次记录'],'department':'生产部','deadline_basis':'成本复核前','responsible_role':'核算员'}
    out=validate_findings([finding],{'month':'2030-04','product':'合成部件'},[])[0]
    assert out['suggestion']=='核对2030-04记录'
    assert out['verification_target']=='合成部件生产记录'
    assert out['expected_evidence']==['2030-04批次记录']
    for field in ('suggestion','verification_target','department','deadline_basis'):
        bad=dict(finding,**{field:'{{missing}}'})
        with pytest.raises(ValueError,match='placeholder'):
            validate_findings([bad],{'month':'2030-04','product':'合成部件'},[])


def test_evidence_same_id_isolated_by_enterprise_and_industry():
    a={'enterprise_id':'A','industry_id':'mechanical_demo','industry_version':'1','dataset_id':'d','knowledge_snapshot':'k'}
    b=dict(a,enterprise_id='B')
    evidence={'evidence_id':'same','products':['same-product'],'analysis_context':a}
    assert Knowledge.evidence_applicability(evidence,product='same-product',context=a)['applicable']
    assert not Knowledge.evidence_applicability(evidence,product='same-product',context=b)['applicable']
    assert not Knowledge.evidence_applicability(evidence,product='same-product',context=dict(a,industry_id='chemical_demo'))['applicable']


def test_generation_cache_context_prompt_and_retriever_changes_invalidate(tmp_path,monkeypatch):
    import pharma.narrative as narrative
    gateway,calls=_gateway(tmp_path,[[_missing()]])
    snapshot={'elements':[{'key':'materials','name':'材料','unit_delta':'1'}],'analysis_context':{'enterprise_id':'A'}}
    evidence={'status':'PASS','evidence':[],'retriever_version':'r1','embedding_version':'e1'}
    assert not narrative.generate(snapshot,evidence,gateway)['cache_hit']
    assert narrative.generate(snapshot,evidence,gateway)['cache_hit']
    assert not narrative.generate(dict(snapshot,analysis_context={'enterprise_id':'B'}),evidence,gateway)['cache_hit']
    assert narrative.generate(snapshot,evidence,gateway)['cache_hit']
    assert not narrative.generate(snapshot,dict(evidence,retriever_version='r2'),gateway)['cache_hit']
    assert not narrative.generate(snapshot,dict(evidence,embedding_version='e2'),gateway)['cache_hit']
    monkeypatch.setattr(narrative,'PROMPT_VERSION','synthetic-next-version')
    assert not narrative.generate(snapshot,evidence,gateway)['cache_hit']
    gateway.base_url='https://synthetic.invalid/v2'
    assert not narrative.generate(snapshot,evidence,gateway)['cache_hit']
    gateway.model='synthetic-changed-model'
    assert not narrative.generate(snapshot,evidence,gateway)['cache_hit']
    assert len(calls)==7


def test_vector_query_receives_only_applicable_candidate_ids(tmp_path):
    source=tmp_path/'source';source.mkdir()
    (source/'seed.txt').write_text('合成演示设备维护记录与成本核查需要核实具体生产批次。')
    knowledge=Knowledge(root=tmp_path,source_dir=source,vector_enabled=False);knowledge.build()
    path=knowledge.path/knowledge.version/'fts.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('DELETE FROM chunks');db.execute('DELETE FROM search')
        for ident,product in [('eligible','target'),('other','other')]:
            row={'evidence_id':ident,'products':[product],'text':'设备记录','source':'synthetic.txt','location':'行1'}
            db.execute('INSERT INTO chunks VALUES (?,?)',(ident,json.dumps(row)))
            db.execute('INSERT INTO search VALUES (?,?)',(ident,'设备'))
    queries=[]
    class Collection:
        def query(self,**kwargs):
            queries.append(kwargs)
            return {'ids':[['eligible']]}
    class Embedding:
        def encode(self,*args,**kwargs):return [[1.0]]
    knowledge.vector_enabled=True;knowledge._embedding=Embedding();knowledge._collection=(knowledge.version,Collection())
    result=knowledge.search('设备',product='target',mode='vector')
    assert queries[0]['where']=={'evidence_id':{'$in':['eligible']}}
    assert result['evidence'][0]['evidence_id']=='eligible'


def test_atomic_knowledge_failure_retains_old_snapshot(tmp_path):
    source=tmp_path/'source';source.mkdir()
    (source/'seed.txt').write_text('合成演示设备维护记录与成本核查需要核实具体生产批次。')
    knowledge=Knowledge(root=tmp_path,source_dir=source,vector_enabled=False);knowledge.build()
    previous=knowledge.version
    (source/'bad.pdf').write_bytes(b'not a PDF')
    assert knowledge.build()['failures']
    assert knowledge.version==previous

def test_reference_contexts_concurrent_same_product_and_document_ids(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from pharma import knowledge as km
    from pharma.context_services import retrieve
    from pharma.industry import analyze_reference
    monkeypatch.setattr(km,'RUNTIME',tmp_path)
    # This test exercises isolation without requiring or downloading embeddings.
    original_model=km.Knowledge._model
    def unavailable(self): raise RuntimeError('SYNTHETIC_VECTOR_UNAVAILABLE')
    monkeypatch.setattr(km.Knowledge,'_model',unavailable)
    ids=['mechanical_demo:synthetic-mechanical','chemical_demo:synthetic-chemical']
    snapshots=[analyze_reference(cid) for cid in ids]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda s:retrieve(s,'成本核查记录'),snapshots))
    for s,r in zip(snapshots,results):
        assert r['status']=='DEGRADED' and r['evidence']
        assert all(e['analysis_context']==s['analysis_context'] for e in r['evidence'])
    again=retrieve(snapshots[0],'成本核查记录')
    assert again['knowledge_version']==results[0]['knowledge_version']
    assert results[0]['knowledge_version']!=results[1]['knowledge_version']


def test_reference_pack_end_to_end_mock_explanation(tmp_path,monkeypatch):
    from pharma import knowledge as km
    from pharma.context_services import retrieve
    from pharma.industry import analyze_reference
    from pharma.narrative import generate,required_alerts,required_explanation_sections
    monkeypatch.setattr(km,'RUNTIME',tmp_path/'indexes')
    def unavailable(self):raise RuntimeError('SYNTHETIC_VECTOR_UNAVAILABLE')
    monkeypatch.setattr(km.Knowledge,'_model',unavailable)
    for i,cid in enumerate(['pharmaceutical:synthetic-pharma','mechanical_demo:synthetic-mechanical','chemical_demo:synthetic-chemical']):
        snapshot=analyze_reference(cid)
        evidence=retrieve(snapshot,'成本核查记录',mode='bm25')
        rows=[]
        for section in required_explanation_sections(snapshot):
            alerts=[a['alert_id'] for a in required_alerts(snapshot) if a['element_key']==section]
            rows.append(_missing(section,alerts))
        run=tmp_path/f'model-{i}';run.mkdir()
        gateway,_=_gateway(run,[rows])
        out=generate(snapshot,evidence,gateway,use_cache=False)
        assert out['status']=='PASS'  # Mock identity, not a live model assertion.
        assert out['analysis_context']==snapshot['analysis_context']
        assert all(v['covered'] for v in out['alert_coverage'].values())
        assert not any('每盒' in f['text'] for f in out['findings'])


@pytest.mark.parametrize('text,missing', [
    ('缺少本期实际采购价格资料，无法判断成本上涨是否来自采购价格变化。',['供应商结算单','实际采购价格']),
    ('现有证据不足以区分产量与分配政策影响；需核对分配基数。',['费用分配政策','本期分配基数']),
    ('尚未取得计量资料，不能确认单位能耗的变化原因。',['能源计量数据','合格产出记录']),
])
def test_legitimate_domain_missing_evidence_phrases_remain_accepted(text,missing):
    finding={'claim_type':'insufficient_evidence','text_template':text,'missing_evidence':missing}
    out=validate_findings([finding],{},[])[0]
    assert out['missing_evidence']==missing and '证据不足' in out['text']


def _semantic_snapshot():
    return {'metrics':{'labor':{'metric_id':'labor','label':'人工单位成本','display':'9.38','unit':'元/件'},'labor_total_rate':{'metric_id':'rate','display':'172.73','unit':'%'}},
            'elements':[{'key':'labor','name':'人工','unit_delta':'1'}],
            'alerts':[{'alert_id':'total-alert','element_key':'labor','element':'人工','basis':'total','rate':'172.73','metric_id':'rate','current':'30000','base':'11000','value_unit':'元'}]}


def _semantic_finding(text,alerts=()):
    return {'claim_type':'hypothesis','section':'labor','text_template':text,'hypothesis':True,'metric_refs':['labor'],'evidence_refs':['synthetic'],'evidence_quotes':{'synthetic':'设备停机可能影响人工工时'},'missing_evidence':['实际人工工时记录'],'alert_refs':list(alerts)}


def _semantic_evidence():
    return [{'evidence_id':'synthetic','text':'设备停机可能影响人工工时','location':'合成记录','source':'synthetic.txt'}]


@pytest.mark.parametrize('text',[
    '本期人工总额为[[metric:labor]]，设备停机可能影响人工工时。',
    '基期人工单位成本为[[metric:labor]]，设备停机可能影响人工工时。',
    '本期人工总额为[[metric:labor]]，基期人工总额为[[metric:labor]]，设备停机可能影响人工工时。',
])
def test_numeric_reference_cannot_change_unit_or_period_role(text):
    with pytest.raises(ValueError,match='semantic|role|unit'):
        validate_findings([_semantic_finding(text)],_semantic_snapshot(),_semantic_evidence())


def test_alert_facts_are_compiled_from_typed_deterministic_values():
    out=validate_findings([_semantic_finding('设备停机可能影响人工工时，尚需核查。',['total-alert'])],_semantic_snapshot(),_semantic_evidence())[0]
    assert '本期30000.00元' in out['text'] and '基期11000.00元' in out['text'] and '172.73%' in out['text']
    assert '9.38' not in out['text']


def test_explicit_current_unit_cost_is_valid_even_with_total_alert():
    out=validate_findings([_semantic_finding('本期人工单位成本为[[metric:labor]]，设备停机可能影响人工工时。',['total-alert'])],_semantic_snapshot(),_semantic_evidence())[0]
    assert '本期人工单位成本为9.38元/件' in out['text']



def test_total_amount_cannot_bind_percentage_metric():
    f=_semantic_finding('本期人工总额为[[metric:rate]]，设备停机可能影响人工工时。')
    f['metric_refs']=['rate']
    with pytest.raises(ValueError,match='semantic'):
        validate_findings([f],_semantic_snapshot(),_semantic_evidence())


def test_task_compiler_keeps_qualitative_text_and_binds_fact_references():
    from pharma.narrative import compile_task_explanations
    text='设备停机可能影响人工工时，尚需核查。'
    row={'task_id':'explain:labor','claim_type':'hypothesis','text_template':text,'evidence_refs':['synthetic'],'evidence_quotes':{'synthetic':'设备停机可能影响人工工时'},'missing_evidence':['实际人工工时记录']}
    compiled=compile_task_explanations([row],_semantic_snapshot())
    assert compiled[0]['text_template']==text and '[[' not in compiled[0]['text_template']
    assert compiled[0]['metric_refs'] and compiled[0]['alert_refs']==['total-alert']
    accepted=validate_findings(compiled,_semantic_snapshot(),_semantic_evidence())[0]
    assert '本期30000.00元' in accepted['text'] and text in accepted['text']


def test_task_compiler_rejects_scope_overrides_duplicates_and_unknowns():
    from pharma.narrative import compile_task_explanations
    row={'task_id':'explain:labor','claim_type':'insufficient_evidence','text_template':'现有证据不足以归因。','missing_evidence':['实际人工工时记录']}
    for rows in ([dict(row,section='summary')],[dict(row,task_id='other')],[row,row]):
        with pytest.raises(ValueError): compile_task_explanations(rows,_semantic_snapshot())


def test_task_shape_can_pass_gateway_without_model_repeating_numeric_facts(tmp_path):
    import httpx
    from pharma.narrative import generate,ModelGateway
    row={'task_id':'explain:labor','claim_type':'hypothesis','text_template':'设备停机可能影响人工工时，尚需核查。','evidence_refs':['synthetic'],'evidence_quotes':{'synthetic':'设备停机可能影响人工工时'},'missing_evidence':['实际人工工时记录']}
    client=httpx.Client(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'model':'glm-5.3-flash','choices':[{'message':{'content':json.dumps({'explanations':[row]})}}]})))
    key=tmp_path/'key';key.write_text('synthetic-key')
    gateway=ModelGateway(runtime=tmp_path,key_file=key,client=client,max_repairs=0,model='glm-5.3-flash')
    out=generate(_semantic_snapshot(),_semantic_evidence(),gateway,use_cache=False)
    assert out['status']=='PASS' and out['alert_coverage']['total-alert']['covered']
    assert any(f.get('origin')=='model' and '设备停机可能影响人工工时' in f['text'] for f in out['findings'])


def test_more_than_eight_legitimate_elements_use_task_derived_capacity(tmp_path):
    from pharma.narrative import generate
    elements=[{'key':f'element{i}','name':f'合成要素{i}','unit_delta':'1'} for i in range(10)]
    alerts=[{'alert_id':f'alert{i}','element_key':e['key'],'basis':'unit'} for i,e in enumerate(elements)]
    snapshot={'elements':elements,'alerts':alerts}
    rows=[_missing(e['key'],[f'alert{i}']) for i,e in enumerate(elements)]
    gateway,_=_gateway(tmp_path,[rows])
    out=generate(snapshot,[],gateway,use_cache=False)
    assert out['status']=='PASS' and len(out['alert_coverage'])==10


@pytest.mark.parametrize('deadline',['下一月度成本分析前','下一年度成本结账前'])
def test_relative_accounting_cycle_is_not_a_free_business_number(deadline):
    action={'claim_type':'recommendation','text_template':'核对人工成本归集记录','suggestion':'调取本期与基期人工工时记录并核对归集口径','verification_target':'人工成本变化来源','expected_evidence':['实际人工工时记录'],'responsible_role':'待分配','department':'成本核算部门','priority':'medium','deadline_basis':deadline}
    assert validate_findings([action],{},[])[0]['deadline_basis']==deadline


@pytest.mark.parametrize('deadline',['预计节约一万元','成本降低百分之十','下月节省100元'])
def test_relative_deadline_field_still_rejects_unbound_business_numbers(deadline):
    action={'claim_type':'recommendation','text_template':'核对人工成本归集记录','suggestion':'核对归集口径','verification_target':'人工成本变化来源','expected_evidence':['实际人工工时记录'],'responsible_role':'待分配','department':'成本核算部门','deadline_basis':deadline}
    with pytest.raises(ValueError,match='number'):
        validate_findings([action],{},[])
