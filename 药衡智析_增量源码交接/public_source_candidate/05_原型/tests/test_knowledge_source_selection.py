"""Public synthetic regressions for explicit enterprise knowledge entries."""
from hashlib import sha256
import json

from pharma import knowledge as km
from pharma import industry
from pharma.context_services import retrieve


def test_enterprise_entry_reads_exact_json_not_its_parent_directory(tmp_path,monkeypatch):
    entries={}
    for name, marker in [('knowledge.json','旧规程'),('enterprise_kb.json','新规程')]:
        path=tmp_path/name
        # The same declared record ID and product intentionally make directory
        # scanning unsafe even if the normal product applicability check runs.
        path.write_text(json.dumps([{'id':'shared-record-id','products':['shared-product'],'scope':'product',
            'text':f'合成演示{marker}明确要求复核设备工时记录及成本归集资料。'}],ensure_ascii=False))
        entries[name]=path
    (tmp_path/'unrelated.txt').write_text('合成演示干扰规程：设备工时记录不属于本次授权知识入口，不得纳入索引。')
    monkeypatch.setattr(km,'RUNTIME',tmp_path/'runtime')
    actual=km.Knowledge
    def lexical_only(**kwargs):return actual(vector_enabled=False,**kwargs)
    monkeypatch.setattr('pharma.context_services.Knowledge',lexical_only)
    contexts=[]
    for name in entries:
        contexts.append(industry.AnalysisContext(enterprise_id='same-company',dataset_id='same-dataset',industry_id='mechanical_demo',
            industry_version='1',policy_version='1',data_snapshot='synthetic-data',knowledge_snapshot=sha256(entries[name].read_bytes()).hexdigest(),template_version='1',formula_version='1'))
    mapping={c.knowledge_snapshot:entries[name] for c,name in zip(contexts,entries)}
    monkeypatch.setattr(industry,'knowledge_entry_for_context',lambda c:mapping[c.knowledge_snapshot])
    results=[retrieve({'analysis_context':c.model_dump(),'product':'shared-product'},'设备工时记录',mode='bm25') for c in contexts]
    for (name,entry),result,marker in zip(entries.items(),results,['旧规程','新规程']):
        assert result['status']=='PASS' and len(result['evidence'])==1
        assert result['evidence'][0]['source']==name
        assert marker in result['evidence'][0]['text']
        assert '干扰规程' not in result['evidence'][0]['text']
    assert results[0]['knowledge_version']!=results[1]['knowledge_version']


def test_explicit_file_selection_cannot_reuse_another_current_index(tmp_path):
    content=json.dumps([{'id':'same-id','products':['same-product'],'text':'合成演示设备维护与工时计量记录需要逐项核对成本归集。'}],ensure_ascii=False)
    first=tmp_path/'first.json';second=tmp_path/'second.json'
    first.write_text(content);second.write_text(content)
    a=km.Knowledge(root=tmp_path,source_files=(first,),vector_enabled=False)
    b=km.Knowledge(root=tmp_path,source_files=(second,),vector_enabled=False)
    assert a.search('设备维护',product='same-product',mode='bm25')['evidence'][0]['source']=='first.json'
    assert b.search('设备维护',product='same-product',mode='bm25')['evidence'][0]['source']=='second.json'
    assert a.path != b.path
