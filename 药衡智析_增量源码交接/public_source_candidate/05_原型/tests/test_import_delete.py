"""待解析导入记录删除（2026-09-24 用户要求：传错数据要能删）。"""
import pytest

from pharma import data_import


@pytest.fixture()
def isolated_runtime(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path))
    import importlib
    import pharma.config as config
    import pharma.data_import as di
    importlib.reload(config)
    monkeypatch.setattr(di, 'IMPORTS_ROOT', config.RUNTIME / 'imports')
    monkeypatch.setattr(di, 'IMPORT_DB', config.RUNTIME / 'imports' / 'imports.sqlite3')
    monkeypatch.setattr(di, '_imports_db_ready', False)
    importlib.reload(di)
    yield tmp_path


CSV = (b'\xef\xbb\xbf\xe5\xb7\xa5\xe5\x8e\x82,\xe4\xba\xa7\xe5\x93\x81,\xe6\x9c\x88\xe4\xbb\xbd,'
       b'\xe4\xba\xa7\xe9\x87\x8f\n\xe7\x94\xb2\xe5\x8e\x82,P,2026-01,100\n')


def test_delete_uploaded_record_removes_row_and_folder(isolated_runtime):
    record = data_import.create_upload('business', 'x.csv', CSV, 'cost_summary')
    assert record['status'] == 'UPLOADED' and not record.get('dedup')
    folder = data_import.IMPORTS_ROOT / record['id']
    assert folder.exists()
    data_import.delete_import(record['id'])
    assert not folder.exists()
    with pytest.raises(KeyError):
        data_import.get_import(record['id'])


def test_delete_then_reupload_same_content_is_fresh_upload(isolated_runtime):
    first = data_import.create_upload('business', 'x.csv', CSV, 'cost_summary')
    again = data_import.create_upload('business', 'x.csv', CSV, 'cost_summary')
    assert again['id'] == first['id'] and again['dedup'] is True and again['status'] == 'UPLOADED'
    data_import.delete_import(first['id'])
    fresh = data_import.create_upload('business', 'x.csv', CSV, 'cost_summary')
    assert fresh['status'] == 'UPLOADED' and not fresh.get('dedup')


def test_delete_rejects_parsed_record(isolated_runtime):
    record = data_import.create_upload('business', 'x.csv', CSV, 'cost_summary')
    data_import.mark_import_status(record, 'PARSED', {})
    with pytest.raises(ValueError, match='IMPORT_NOT_DELETABLE'):
        data_import.delete_import(record['id'])
    data_import.get_import(record['id'])  # 仍存在
