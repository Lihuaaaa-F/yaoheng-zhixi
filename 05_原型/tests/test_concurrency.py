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


def test_concurrent_active_parse_guard_enqueues_exactly_one(tmp_path):
    """处置遗留#6：活跃同类任务防重在 BEGIN IMMEDIATE 事务内与入队原子执行。
    真实并发反例——旧实现为 api 层无锁快照读，两个请求可同时通过检查并各自入队。"""
    store=JobStore(tmp_path/'jobs.sqlite')
    barrier=threading.Barrier(8)
    def enqueue(_):
        barrier.wait()
        try:
            return store.enqueue('data_parse',{'import_ids':['i1']},reject_active_kind='data_parse')
        except ValueError as exc:
            return exc
    with ThreadPoolExecutor(max_workers=8) as pool:
        results=list(pool.map(enqueue,range(8)))
    jobs=[r for r in results if isinstance(r,dict)]
    rejected=[str(r) for r in results if isinstance(r,ValueError)]
    assert len(jobs)==1
    assert len(rejected)==7
    assert all(r.startswith('PARSE_ALREADY_RUNNING:') for r in rejected)
    assert all(r==f'PARSE_ALREADY_RUNNING:{jobs[0]["id"]}' for r in rejected)
    assert len(store.list())==1
