"""Public-store regression from independent review's real concurrent failures."""
import threading
from concurrent.futures import ThreadPoolExecutor
from test_actions import ActionStore
from pharma.jobs import JobStore


def test_same_report_concurrent_enqueue_returns_one_persistent_job(tmp_path):
    store=JobStore(tmp_path/'jobs.sqlite')
    barrier=threading.Barrier(16)
    def enqueue(_):
        barrier.wait()
        return store.enqueue('report',{'snapshot_id':'from-scratch-fixture'},'same-fixture-key')['id']
    with ThreadPoolExecutor(max_workers=16) as pool:
        ids=list(pool.map(enqueue,range(16)))
    assert len(set(ids))==1
    assert len(store.list())==1


def test_same_finding_concurrent_draft_returns_one_unconfirmed_action(tmp_path):
    store=ActionStore(tmp_path/'actions.sqlite')
    barrier=threading.Barrier(16)
    def draft(_):
        barrier.wait()
        return store.draft({'snapshot_id':'from-scratch-fixture','analysis_type':'monthly','month':'2026-05','product':'演示产品'},
            '测试发现',{'name':'演示责任人','department':'演示部门'},'测试建议')['id']
    with ThreadPoolExecutor(max_workers=16) as pool:
        ids=list(pool.map(draft,range(16)))
    assert len(set(ids))==1
    assert store.get(ids[0])['status']=='DRAFT'
    assert store.pending()==[]
