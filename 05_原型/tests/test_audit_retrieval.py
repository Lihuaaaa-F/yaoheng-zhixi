"""Synthetic regressions for the retrieval audit; never call a model service."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from pharma import knowledge as kb, vector_switch as vs, narrative, context_services


def make_knowledge(tmp_path):
    source = tmp_path / 'source'
    source.mkdir()
    (source / 'seed.txt').write_text('合成演示设备维护记录与成本核查需要核实具体生产批次。', encoding='utf-8')
    knowledge = kb.Knowledge(root=tmp_path, source_dir=source, vector_enabled=False)
    knowledge.build()
    return knowledge, source


def test_failed_source_keeps_old_index_without_rebuilding_each_request(tmp_path, monkeypatch):
    knowledge, source = make_knowledge(tmp_path)
    old_version = knowledge.version
    (source / 'broken.pdf').write_bytes(b'not a pdf')
    calls = []
    original = kb.Knowledge._build
    def track(self, progress=None):
        calls.append(1)
        return original(self, progress)
    monkeypatch.setattr(kb.Knowledge, '_build', track)
    for _ in range(3):
        fresh = kb.Knowledge(root=tmp_path, source_dir=source, vector_enabled=False)
        result = fresh.search('设备', mode='bm25')
        assert result['status'] == 'DEGRADED'
        assert result['evidence'] and result['knowledge_version'] == old_version
        assert 'REBUILD_FAILED' in result['reason']
    assert len(calls) == 1
    (source / 'broken.pdf').unlink()
    assert knowledge.search('设备', mode='bm25')['status'] == 'PASS'


def test_same_name_sources_retain_individual_hashes(tmp_path):
    knowledge, source = make_knowledge(tmp_path)
    extra = tmp_path / 'extra'; extra.mkdir()
    other = extra / 'seed.txt'
    other.write_text('独立合成的采购合同记录与费用核查需要确认具体材料批次。', encoding='utf-8')
    knowledge.extra_dir = extra
    knowledge.build()
    rows = json.loads((knowledge.path / knowledge.version / 'chunks.json').read_text(encoding='utf-8'))
    assert {r['hash'] for r in rows} == {kb.file_fingerprint(other), kb.file_fingerprint(source / 'seed.txt')}
    assert len(knowledge.status()['sources']) == 2


def test_knowledge_json_participates_in_source_snapshot(tmp_path):
    path = tmp_path / 'knowledge.json'; path.write_text('[]', encoding='utf-8')
    before = kb.source_snapshot(tmp_path)
    path.write_text('[{}]', encoding='utf-8')
    assert kb.source_snapshot(tmp_path) != before


def test_truncated_manifest_can_be_rebuilt(tmp_path):
    knowledge, _ = make_knowledge(tmp_path)
    (knowledge.path / knowledge.version / 'manifest.json').write_text('{', encoding='utf-8')
    assert knowledge.build()['chunks'] > 0
    assert knowledge.search('设备', mode='bm25')['evidence']


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -float('inf')])
def test_probe_rejects_nonfinite_vectors(tmp_path, monkeypatch, bad):
    (tmp_path / 'model.onnx').touch(); (tmp_path / 'tokenizer.json').touch()
    monkeypatch.setattr(kb, 'CpuEmbedding', lambda path: SimpleNamespace(encode=lambda *a, **k: [[bad], [1.0]]))
    with pytest.raises(vs.SwitchFailure, match='非有限'):
        vs._probe_local(tmp_path)


def test_unexpected_switch_exception_rolls_back_config(tmp_path, monkeypatch):
    from pharma import model_settings
    old = tmp_path / 'old'; old.mkdir()
    new = tmp_path / 'new'; new.mkdir()
    model_settings.set_vector_model(str(old))
    monkeypatch.delenv('PHARMA_EMBEDDING_DIR', raising=False)
    monkeypatch.setattr(vs, '_probe_local', lambda p: {'name': 'new', 'probe_dimension': 1})
    monkeypatch.setattr(vs, '_model_adaptation', lambda p: {'dimension': 1, 'api_reason': 'ok'})
    class BrokenKnowledge:
        path = tmp_path
        def build(self, **kwargs): raise RuntimeError('synthetic unexpected failure')
    monkeypatch.setattr(kb, 'Knowledge', BrokenKnowledge)
    updates = []
    vs.run_vector_switch(SimpleNamespace(update=lambda *a, **k: updates.append((a,k))),
                         {'id':'j', 'result':{}, 'input':{'path':str(new)}})
    assert model_settings._load()['vector_model']['path'] == str(old)
    assert updates[-1][0][1] == 'FAILED'


def test_retrieve_forwards_document_version(monkeypatch):
    scopes=[]
    monkeypatch.setattr(context_services, 'knowledge_for_context', lambda c: SimpleNamespace(search=lambda q, **kw: scopes.append(kw) or {'evidence':[]}))
    context_services.retrieve({'document_version':'v2'}, '设备', graph_enabled=False)
    assert scopes[0]['document_version'] == 'v2'


def test_total_metric_cannot_add_per_box_unit():
    snapshot={'metrics':{'total_cost':{'metric_id':'total', 'value':'100', 'unit':'元'}}}
    with pytest.raises(ValueError, match='unit'):
        narrative._metric_role_validation('本期金额为[[metric:total]]元/盒。', snapshot)


@pytest.mark.parametrize('query,product,expected', [('设备',None,'RECALLED'),('zzzznotfound',None,'NO_MATCH'),('设备','unknown','NO_APPLICABLE_CANDIDATES')])
def test_recall_status_is_separate_from_execution(tmp_path, query, product, expected):
    knowledge, _ = make_knowledge(tmp_path)
    result = knowledge.search(query, product=product, mode='bm25')
    assert result['status'] == 'PASS'
    assert result['recall_status'] == expected


def test_reranker_cannot_introduce_evidence(tmp_path):
    knowledge, _ = make_knowledge(tmp_path)
    knowledge.reranker = lambda *args: ['fabricated-id']
    result = knowledge.search('设备', mode='bm25')
    assert result['reranker_error']
    assert all(row['evidence_id'] != 'fabricated-id' for row in result['evidence'])


@pytest.mark.parametrize('requested,expected', [(None,2),(-3,0),(8,2),(1,1)])
def test_max_repairs_default_and_clamp(tmp_path, monkeypatch, requested, expected):
    monkeypatch.delenv('PHARMA_MODEL_MAX_REPAIRS', raising=False)
    assert narrative.ModelGateway(runtime=tmp_path, max_repairs=requested).max_repairs == expected


@pytest.mark.parametrize('change', [{'pooling':'mean'}, {'normalize':False}, {'query_prefix':''}, {'dimension':99}])
def test_adaptation_rejects_unsupported_inference_contract(monkeypatch, change):
    answer = {'adaptable':True, 'dimension':2, 'pooling':'cls', 'normalize':True,
              'query_prefix':'为这个句子生成表示以用于检索相关文章：', 'reason':'合成评估'} | change
    gateway=SimpleNamespace(key='synthetic', model='fake', complete=lambda *a, **k:(json.dumps(answer), {}, {}))
    monkeypatch.setattr(narrative.ModelGateway, 'for_route', lambda r: gateway)
    with pytest.raises(vs.SwitchFailure, match='推理合同'):
        vs._model_adaptation({'probe_dimension':2})


@pytest.mark.parametrize('unit,expected', [('g','g'),('kg','kg'),('毫克','mg'),('备注',None)])
def test_graph_dose_uses_document_unit(tmp_path, monkeypatch, unit, expected):
    from pharma.graph import KnowledgeGraph
    graph=KnowledgeGraph(SimpleNamespace(path=tmp_path))
    monkeypatch.setattr(graph, '_chunks', lambda v:[{'source':'合成配方', 'products':['合成药品'],
        'text':f'1 黄芪 20 {unit} 原料', 'location':'行1'}])
    result=graph._build('synthetic')
    assert result['edges'][0]['props']['unit'] == expected


def test_terminology_cache_avoids_repeated_reads_and_observes_changes(tmp_path, monkeypatch):
    terms={'products':['合成药'], 'product_aliases':{}, 'equipment_aliases':{}, 'tokenizer_terms':['合成词']}
    path=tmp_path/'terms.json'; path.write_text(json.dumps(terms), encoding='utf-8')
    monkeypatch.setenv('PHARMA_PRIVATE_TERMINOLOGY_FILE', str(path))
    reads=[]; original=Path.read_text
    def read(self,*a,**k):
        if self==path: reads.append(1)
        return original(self,*a,**k)
    monkeypatch.setattr(Path,'read_text',read)
    for _ in range(4): kb.tokenize('合成词')
    assert len(reads)==1
    terms['tokenizer_terms'].append('新增词')
    path.write_text(json.dumps(terms),encoding='utf-8')
    assert '新增词' in kb.pharmaceutical_terminology()['tokenizer_terms']
    assert len(reads)==2


def test_model_audit_files_support_non_gbk_unicode(tmp_path, monkeypatch):
    import httpx
    key=tmp_path/'key'; key.write_text('synthetic-test-key',encoding='utf-8')
    client=httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(200,json={
        'model':'glm-5.3-flash', 'choices':[{'message':{'content':'审计成功😀'}}]})))
    gateway=narrative.ModelGateway(runtime=tmp_path,key_file=key,client=client)
    original=Path.write_text
    def windows_write(self,data,encoding=None,**kwargs):
        return original(self,data,encoding=encoding or 'cp936',**kwargs)
    monkeypatch.setattr(Path,'write_text',windows_write)
    text,_,_=gateway.complete('合成测试😀','合成测试😀')
    assert text=='审计成功😀'
    assert json.loads((tmp_path/'model-response-1.json').read_text(encoding='utf-8'))['response_text']==text


def test_switch_rollback_restores_current_without_rebuilding_old_sources(tmp_path, monkeypatch):
    from pharma import model_settings
    old=tmp_path/'old';old.mkdir();new=tmp_path/'new';new.mkdir()
    model_settings.set_vector_model(str(old));monkeypatch.delenv('PHARMA_EMBEDDING_DIR',raising=False)
    pointer=tmp_path/'CURRENT';pointer.write_text('old-version',encoding='utf-8')
    monkeypatch.setattr(vs,'_probe_local',lambda p:{'name':'new','probe_dimension':1})
    monkeypatch.setattr(vs,'_model_adaptation',lambda p:{'dimension':1,'api_reason':'ok'})
    class InterruptedKnowledge:
        path=tmp_path
        def build(self,**kwargs):
            pointer.write_text('new-version',encoding='utf-8')
            raise RuntimeError('interrupted after publishing new index')
    monkeypatch.setattr(kb,'Knowledge',InterruptedKnowledge)
    vs.run_vector_switch(SimpleNamespace(update=lambda *a,**k:None), {'id':'j','result':{},'input':{'path':str(new)}})
    assert pointer.read_text(encoding='utf-8')=='old-version'
    assert model_settings._load()['vector_model']['path']==str(old)


@pytest.mark.parametrize('broken', ['[]', '{"parser_version":"'+kb.PARSER_VERSION+'"}'])
def test_wrong_manifest_shape_can_be_rebuilt(tmp_path,broken):
    knowledge,_=make_knowledge(tmp_path)
    (knowledge.path/knowledge.version/'manifest.json').write_text(broken,encoding='utf-8')
    assert knowledge.build()['chunks']>0


def test_narrative_rechecks_document_version():
    evidence={'evidence_id':'synthetic-e', 'text':'合成设备需要维护记录核查', 'location':'行1',
              'document_version':'old'}
    finding={'claim_type':'document_fact', 'text_template':evidence['text'], 'evidence_refs':['synthetic-e'],
             'evidence_quotes':{'synthetic-e':evidence['text']}}
    with pytest.raises(ValueError, match='不匹配'):
        narrative.validate_findings([finding], {'document_version':'new'}, [evidence])


@pytest.mark.parametrize('suffix', ['元/盒的单位成本', '元／盒的单位成本', '元/盒，待核查'])
def test_metric_suffix_does_not_consume_following_chinese_prose(suffix):
    snapshot={'metrics':{'unit_cost':{'value':'1.00','unit':'元/盒'}}}
    narrative._metric_role_validation('本期[[metric:unit_cost]]'+suffix, snapshot)


def test_metric_slot_still_supplies_its_own_unit():
    snapshot={'metrics':{'unit_cost':{'value':'1.00','unit':'元/盒'}}}
    assert narrative.render_visible_text('本期[[metric:unit_cost]]的单位成本',snapshot,
        metric_refs=['unit_cost'])=='本期1.00元/盒的单位成本'


@pytest.mark.parametrize('suffix', ['元/支的单位成本', '元/盒/天的单位成本', '元/kg的单位成本', '元的单位成本'])
def test_metric_suffix_cannot_replace_or_extend_unit(suffix):
    snapshot={'metrics':{'unit_cost':{'value':'1.00','unit':'元/盒'}}}
    with pytest.raises(ValueError, match='unit'):
        narrative._metric_role_validation('本期[[metric:unit_cost]]'+suffix,snapshot)


@pytest.mark.parametrize('line', ['1 白芍 250   g 原料', '  1 白芍 250   g 原料', '1 白芍 250\t\tg 原料'])
def test_graph_dose_unit_tolerates_table_whitespace(tmp_path, monkeypatch, line):
    from pharma.graph import KnowledgeGraph
    graph=KnowledgeGraph(SimpleNamespace(path=tmp_path))
    monkeypatch.setattr(graph, '_chunks', lambda v:[{'source':'合成配方', 'products':['合成药品'],
        'text':'表格内容\n'+line, 'location':'行2'}])
    assert graph._build('synthetic')['edges'][0]['props']['unit']=='g'
