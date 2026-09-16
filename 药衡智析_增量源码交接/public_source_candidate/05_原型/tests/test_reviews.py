"""审核闭环：录入绑定产物哈希、产物变化失效、重算不代签。"""
import json
from pharma.reports import assess_report
from pharma.reviews import ReviewStore


def _review_dims(pass_all=True):
    status = 'PASS' if pass_all else 'FAIL'
    return {name: {'status': status, 'comment': ''} for name in ('section_completeness', 'readability', 'visual_quality')}


def _job(job_id='j1', docx='d1', pdf='p1'):
    return {'id': job_id, 'status': 'DEGRADED', 'result': {}}


def test_review_requires_reviewer_score_and_dimensions(tmp_path):
    store = ReviewStore(path=tmp_path/'reviews.sqlite3')
    import pytest
    with pytest.raises(ValueError, match='REVIEWER_REQUIRED'):
        store.submit(_job(), 'd1', 'p1', '  ', 3, _review_dims())
    with pytest.raises(ValueError, match='ATTRIBUTION_SCORE'):
        store.submit(_job(), 'd1', 'p1', '张三', 6, _review_dims())
    with pytest.raises(ValueError, match='DIMENSION'):
        store.submit(_job(), 'd1', 'p1', '张三', 3, {'section_completeness': {'status': 'PASS'}})


def test_valid_review_unlocks_human_dimensions_in_assessment(tmp_path):
    store = ReviewStore(path=tmp_path/'reviews.sqlite3')
    review = store.submit(_job(), 'd1', 'p1', '李评审', 4, _review_dims(True), '结构完整')
    actionable = {'claim_type': 'recommendation', 'suggestion': '核对采购合同', 'verification_target': '本期采购',
                  'expected_evidence': ['合同'], 'responsible_role': '采购部', 'deadline_basis': '复核前'}
    base = {'docx': {'status': 'PASS', 'verification': {'core_numbers': True, 'numeric_bindings_checked': 90, 'numeric_binding_failures': []}},
            'pdf': {'status': 'PASS'}, 'evidence': {'status': 'PASS', 'evidence': []},
            'narrative': {'status': 'PASS', 'model_live': True, 'evidence_applicability_checked': True, 'findings': [actionable]}}
    r = assess_report(base, review=review)
    assert r['section_completeness']['status'] == 'PASS'
    assert r['readability']['status'] == 'PASS'
    assert r['visual_quality']['status'] == 'PASS'
    assert r['human_attribution_score'] == 4
    assert r['overall'] == 'PASS'


def test_without_review_human_dimensions_stay_pending():
    # 无真人审核时人工维度PENDING；其余自动维度不通过则总体如实FAIL而非PENDING
    base = {'docx': {'status': 'PASS'}, 'pdf': {'status': 'PASS'},
            'evidence': {'status': 'PASS'}, 'narrative': {'status': 'PASS', 'model_live': True, 'findings': []}}
    r = assess_report(base)
    assert r['section_completeness']['status'] == 'PENDING'
    assert r['readability']['status'] == 'PENDING'
    assert r['visual_quality']['status'] == 'PENDING'
    assert r['overall'] == 'FAIL'  # 证据逐条核对未执行的维度按FAIL暴露，不静默


def test_artifact_change_expires_review(tmp_path):
    store = ReviewStore(path=tmp_path/'reviews.sqlite3')
    store.submit(_job(), 'd1', 'p1', '李评审', 4, _review_dims())
    store.submit(_job(), 'd2', 'p2', '李评审', 4, _review_dims())
    # 有效判定必须按哈希而不是按时间：当前产物是d1时，更新的d2审核不生效
    latest = store.latest_valid(_job(), {'docx': 'd1', 'pdf': 'p1'})
    assert latest is not None and latest['docx_sha256'] == 'd1'
    active = store.latest_valid(_job(), {'docx': 'd2', 'pdf': 'p2'})
    assert active is not None and active['docx_sha256'] == 'd2'
    assert store.latest_valid(_job(), {'docx': 'd3', 'pdf': 'p3'}) is None


def test_per_claim_evidence_check_replaces_aggregate_boolean():
    finding = {'claim_type': 'hypothesis', 'evidence_refs': ['ev1'], 'suggestion': ''}
    ev = {'status': 'PASS', 'evidence': [{'evidence_id': 'ev1', 'text': '工艺', 'products': ['别的产品']}]}
    base = {'snapshot': {'product': '板蓝根颗粒'}, 'docx': {'status': 'PASS'}, 'pdf': {'status': 'PASS'},
            'evidence': ev, 'narrative': {'status': 'PASS', 'model_live': True, 'evidence_applicability_checked': True, 'findings': [finding]}}
    r = assess_report(base)
    assert r['evidence_applicability']['status'] == 'FAIL'
    assert '证据不适用' in r['evidence_applicability']['reason'] or '不适用' in r['evidence_applicability']['reason']


def test_draft_preview_and_final_download_contract(tmp_path):
    from pharma.jobs import JobStore
    from pharma.config import ARTIFACTS
    import hashlib
    store = JobStore(path=tmp_path / 'jobs.sqlite3')
    job = store.enqueue('report', {})
    store.update(job['id'], 'RENDERING_DOCX')
    folder = ARTIFACTS / job['id']
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / 'report.docx'
    f.write_bytes(b'draft-bytes')
    record = {'path': str(f), 'sha256': hashlib.sha256(b'draft-bytes').hexdigest()}
    store.artifact(job['id'], record, 'docx')
    store.update(job['id'], 'DEGRADED', {})
    # 已注册且哈希一致：运行中可取草稿预览，终态可取正式产物
    assert store.artifact_path(job['id'] + '-docx', preview=True).is_file()
    assert store.artifact_path(job['id'] + '-docx').is_file()
    store.update(job['id'], 'GENERATING', {})
    import pytest
    with pytest.raises(ValueError):
        store.artifact_path(job['id'] + '-docx')
