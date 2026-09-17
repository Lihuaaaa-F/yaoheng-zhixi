"""Only invented public products/devices exercise local private-JSON contracts."""
import json
import pytest
from pharma import knowledge as km
from pharma import ingestion


def terms():
    return {'products':['模拟制剂甲','模拟制剂乙'],'product_aliases':{'模拟制剂甲':['模拟制剂甲'],'模拟制剂乙':['模拟制剂乙']},'equipment_aliases':{'模拟制剂甲':['模拟设备甲'],'模拟制剂乙':['模拟设备乙']},'tokenizer_terms':['模拟制剂甲','模拟设备甲']}


def test_private_terminology_is_dynamic_and_schema_checked(tmp_path,monkeypatch):
    path=tmp_path/'terminology.json';value=terms();path.write_text(json.dumps(value))
    monkeypatch.setenv('PHARMA_PRIVATE_TERMINOLOGY_FILE',str(path))
    assert km.pharmaceutical_terminology()==value
    from pharma.narrative import quote_matches_product
    assert not quote_matches_product('模拟设备乙的维护记录','模拟制剂甲')
    value['equipment_aliases']['模拟制剂甲'].append('模拟设备丙');path.write_text(json.dumps(value))
    assert '模拟设备丙' in km.pharmaceutical_terminology()['equipment_aliases']['模拟制剂甲']
    path.write_text(json.dumps({**value,'python':'print(1)'}))
    with pytest.raises(ValueError):km.pharmaceutical_terminology()


@pytest.mark.parametrize('value',[[],{'products':'not-a-list'},{**terms(),'equipment_aliases':{'not-a-product':['模拟设备丙']}},{**terms(),'tokenizer_terms':['']}])
def test_invalid_private_terminology_shape_rejected(tmp_path,monkeypatch,value):
    path=tmp_path/'invalid.json';path.write_text(json.dumps(value))
    monkeypatch.setenv('PHARMA_PRIVATE_TERMINOLOGY_FILE',str(path))
    with pytest.raises(ValueError):km.pharmaceutical_terminology()


def test_same_knowledge_object_rebuilds_when_private_mapping_changes(tmp_path,monkeypatch):
    path=tmp_path/'private.json';value=terms();path.write_text(json.dumps(value))
    monkeypatch.setenv('PHARMA_PRIVATE_TERMINOLOGY_FILE',str(path))
    source=tmp_path/'sources';source.mkdir()
    (source/'模拟制剂甲_规程.txt').write_text('模拟制剂甲的模拟设备甲需要核查维护记录、合格产出以及工时归集。')
    knowledge=km.Knowledge(root=tmp_path,source_dir=source,vector_enabled=False)
    first=knowledge.search('维护记录',product='模拟制剂甲',mode='bm25')
    original_source_hash=km.source_snapshot(source)
    value['equipment_aliases']['模拟制剂甲'].append('模拟设备丙');path.write_text(json.dumps(value))
    second=knowledge.search('维护记录',product='模拟制剂甲',mode='bm25')
    assert first['evidence'] and second['evidence']
    assert first['knowledge_version']!=second['knowledge_version']
    assert km.source_snapshot(source)!=original_source_hash


def test_private_masterdata_can_only_override_typed_enterprise_fields(tmp_path,monkeypatch):
    value={'specifications':{'模拟制剂甲':['2片/盒',2,'元/片','模拟片剂']},'factories':['模拟工厂甲']}
    path=tmp_path/'masterdata.json';path.write_text(json.dumps(value))
    monkeypatch.setenv('PHARMA_PRIVATE_MASTERDATA_FILE',str(path))
    before=ingestion.source_contract()
    assert before['specifications']==value['specifications'] and before['factories']==value['factories']
    assert before['fields']==ingestion.FIELDS
    first=ingestion.source_contract_hash()
    value['factories'].append('模拟工厂乙');path.write_text(json.dumps(value))
    assert ingestion.source_contract_hash()!=first
    path.write_text(json.dumps({**value,'fields':{'cost':['anything']}}))
    with pytest.raises(ValueError):ingestion.source_contract()
