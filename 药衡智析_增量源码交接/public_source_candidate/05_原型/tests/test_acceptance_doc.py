"""人工验收凭证上传（2026-09-23）：类型校验、最终态校验、登记审核并重算验收。"""
import sqlite3
from contextlib import contextmanager
import pytest
from fastapi.testclient import TestClient

from pharma import api, config, reviews

REVIEW_FIELDS = {'reviewer': '测试审核员（虚构夹具）', 'attribution_score': '4',
                 'section_completeness': 'PASS', 'readability': 'PASS', 'visual_quality': 'PASS'}


def _fake_store(monkeypatch, status='SUCCEEDED'):
    captured = {}

    class FakeStore:
        def get(self, job_id):
            return {'id': job_id, 'status': status, 'result': {'narrative': {'status': 'PASS', 'model_live': True, 'findings': []}, 'evidence': {'status': 'PASS', 'evidence': []}, 'docx': {'status': 'PASS'}, 'pdf': {'status': 'PASS'}}}
        def artifact(self, job_id, record, fmt):
            captured['record'] = record; captured['fmt'] = fmt
            return {'artifact_id': job_id + '-accept', 'sha256': record['sha256']}
        @contextmanager
        def db(self):
            conn = sqlite3.connect(':memory:')
            conn.execute('CREATE TABLE jobs(id TEXT PRIMARY KEY, status TEXT, stage TEXT, result TEXT)')
            try: yield conn
            finally: conn.close()
    monkeypatch.setattr(api, 'store', FakeStore())
    monkeypatch.setattr(api, '_current_hashes', lambda job, strict=False: {'docx': 'h-docx', 'pdf': 'h-pdf'})
    return captured


def _fake_review_store(monkeypatch):
    captured = {}

    def fake_submit(self, job, docx_sha, pdf_sha, reviewer, score, dims, comment=''):
        captured.update(job_id=job['id'], reviewer=reviewer, score=score, dims=dims, comment=comment)
        return {'id': 'REV-1', 'job_id': job['id'], 'reviewer': reviewer, 'reviewed_at': 't',
                'attribution_score': score, 'dimensions': dims, 'comment': comment}
    def fake_latest(self, job, hashes):
        return {'id': 'REV-1', 'reviewer': captured.get('reviewer', ''), 'reviewed_at': 't',
                'attribution_score': captured.get('score', 0), 'dimensions': captured.get('dims', {}), 'comment': captured.get('comment', '')}
    monkeypatch.setattr(reviews.ReviewStore, 'submit', fake_submit)
    monkeypatch.setattr(reviews.ReviewStore, 'latest_valid', fake_latest)
    return captured


def test_acceptance_doc_rejects_unknown_type(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARTIFACTS', tmp_path)
    _fake_store(monkeypatch); _fake_review_store(monkeypatch)
    client = TestClient(api.app)
    r = client.post('/api/reports/j1/acceptance-doc',
                    files={'file': ('virus.exe', b'xx')}, data=REVIEW_FIELDS)
    assert r.status_code == 422 and 'ACCEPTANCE_DOC_TYPE' in r.text


def test_acceptance_doc_rejects_non_final_job(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARTIFACTS', tmp_path)
    _fake_store(monkeypatch, status='RUNNING'); _fake_review_store(monkeypatch)
    client = TestClient(api.app)
    r = client.post('/api/reports/j1/acceptance-doc',
                    files={'file': ('a.pdf', b'x')}, data=REVIEW_FIELDS)
    assert r.status_code == 422 and 'REVIEW_TARGET_NOT_FINAL' in r.text


def test_acceptance_doc_registers_review_and_recomputes(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARTIFACTS', tmp_path)
    stored = _fake_store(monkeypatch); captured = _fake_review_store(monkeypatch)
    client = TestClient(api.app)
    r = client.post('/api/reports/j1/acceptance-doc',
                    files={'file': ('验收记录.docx', b'docx-bytes')},
                    data={**REVIEW_FIELDS, 'reviewer': '测试审核员（虚构夹具）', 'attribution_score': '5'})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body['status'] == 'OK'
    assert body['acceptance_doc']['artifact_id'] == 'j1-accept'
    assert captured['reviewer'] == '测试审核员（虚构夹具）' and captured['score'] == 5
    assert captured['job_id'] == 'j1'
    assert all(captured['dims'][k]['status'] == 'PASS' for k in ('section_completeness', 'readability', 'visual_quality'))
    assert '人工验收凭证' in captured['comment'] and 'j1-accept' in captured['comment']
    # 凭证字节真实落盘在 ARTIFACTS/acceptance 下
    assert (tmp_path / 'acceptance' / 'j1-accept.docx').read_bytes() == b'docx-bytes'
    # 验收重算后人工三维为 PASS（不再 PENDING）
    acceptance = body['acceptance']['acceptance'] if 'acceptance' in body['acceptance'] else body['acceptance']
    for k in ('section_completeness', 'readability', 'visual_quality'):
        assert acceptance[k]['status'] == 'PASS', acceptance[k]


def test_acceptance_doc_never_supplies_implicit_human_pass(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ARTIFACTS', tmp_path)
    _fake_store(monkeypatch)
    captured = _fake_review_store(monkeypatch)
    response = TestClient(api.app).post('/api/reports/j1/acceptance-doc',
        files={'file': ('a.pdf', b'fixture')}, data={'reviewer': '测试审核员（虚构夹具）'})
    assert response.status_code == 422
    assert not captured
