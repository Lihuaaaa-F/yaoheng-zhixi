from pharma.ingestion import ingest, load_rows

def test_original_snapshot_is_valid_and_has_334_rows(tmp_path):
    manifest = ingest(destination=tmp_path)
    assert manifest['status'] == 'VALID'
    assert manifest['row_count'] == 334
    assert len(load_rows(destination=tmp_path)) == 334

def test_invalid_new_snapshot_keeps_published_snapshot(tmp_path):
    import csv,json
    from pharma.ingestion import FIELDS
    source=tmp_path/'input';source.mkdir()
    destination=tmp_path/'snapshots'
    path=source/'演示_成本汇总.csv'
    row=dict(zip(FIELDS['cost'],['中药一厂','银黄口服液','10ml×10支/盒','2026-01','100','6','2','2','10','1000']))
    def write():
        with path.open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=FIELDS['cost']);writer.writeheader();writer.writerow(row)
    write();first=ingest(source,destination)
    row['总成本(元)']='999';write()
    import pytest
    with pytest.raises(ValueError,match='DATA_VALIDATION_FAILED'):
        ingest(source,destination)
    assert json.loads((destination/'current.json').read_text())['snapshot_id']==first['snapshot_id']
    assert load_rows(destination)[0]['data']['总成本(元)']=='1000'

def test_zip_name_repair_and_path_escape_rejected(tmp_path):
    import zipfile,pytest
    from pharma.ingestion import inspect_zip
    bad=tmp_path/'unsafe.zip'
    with zipfile.ZipFile(bad,'w') as archive:archive.writestr('../escape.csv','x')
    with pytest.raises(ValueError,match='UNSAFE_ARCHIVE_ENTRY'):inspect_zip(bad)
    safe=tmp_path/'safe.zip'
    with zipfile.ZipFile(safe,'w') as archive:
        archive.writestr('资料/数据.csv','字段\n值')
        archive.writestr('__MACOSX/._数据.csv','metadata')
    result=inspect_zip(safe)
    assert result['entries'][1]['excluded'] is True

def test_unknown_field_is_quarantined_not_silently_dropped(tmp_path):
    import pytest
    source=tmp_path/'input';source.mkdir()
    (source/'演示_成本汇总.csv').write_text('未知字段\n123\n',encoding='utf-8-sig')
    with pytest.raises(ValueError,match='DATA_VALIDATION_FAILED'):
        ingest(source,tmp_path/'output')
    assert not (tmp_path/'output/current.json').exists()
    assert list((tmp_path/'output').glob('rejected-*.json'))
