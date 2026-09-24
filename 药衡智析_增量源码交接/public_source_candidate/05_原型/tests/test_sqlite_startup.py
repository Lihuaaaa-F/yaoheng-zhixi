"""Real SQLite contention: startup must not strand import jobs in QUEUED."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from threading import Barrier, Event, Timer

from pharma.actions import ActionStore
from pharma.jobs import JobStore
from pharma.sqlite_utils import enable_wal


def test_initial_journal_lock_is_retried_without_losing_existing_rows(tmp_path):
    path = tmp_path / 'existing.sqlite3'
    held = sqlite3.connect(path, check_same_thread=False)
    held.execute('CREATE TABLE original(value TEXT)')
    held.execute("INSERT INTO original VALUES('preserve')")
    held.commit()
    held.execute('BEGIN EXCLUSIVE')
    started = Event()

    def connect_during_lock():
        connection = sqlite3.connect(path, timeout=.001)
        try:
            started.set()
            enable_wal(connection)
            return connection.execute('SELECT value FROM original').fetchone()[0]
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(connect_during_lock)
        assert started.wait(2)
        release = Timer(.12, held.commit)
        release.start()
        try:
            assert future.result(timeout=6) == 'preserve'
        finally:
            release.join()
            held.close()


def test_api_and_worker_stores_can_start_together_and_process_queued_job(tmp_path):
    path = tmp_path / 'fresh.sqlite3'
    barrier = Barrier(8)

    def initialize(index):
        barrier.wait(timeout=5)
        if index % 2:
            ActionStore(path)
            return None
        return JobStore(path).enqueue('data_parse', {'fixture': index})['id']

    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = [value for value in pool.map(initialize, range(8)) if value]
    worker = JobStore(path)
    assert len(ids) == 4
    for _ in ids:
        job = worker.next()
        assert job['id'] in ids
        worker.update(job['id'], 'SUCCEEDED', {'parsed': True})
    assert worker.next() is None
    assert all(worker.get(id)['status'] == 'SUCCEEDED' for id in ids)
