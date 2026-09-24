"""2026-09-24 审查回归：Windows 同进程并发 exclusive() 不得 EDEADLK。

实测背景：msvcrt 文件锁按进程持有，同进程第二个线程对同一区域 LK_LOCK 立即抛
OSError Errno 36（api.log 7786 有真实 traceback，/api/benchmarks 双请求并发首建
知识库时双双 500）。修复后 exclusive() 用进程内互斥量按路径串行化，第二个等待者
在前者释放后应正常进入临界区。
"""
import threading
import time

from pharma.locks import exclusive, try_exclusive


def test_concurrent_exclusive_same_path_no_deadlock(tmp_path):
    lock_path = tmp_path / 'build.lock'
    order = []
    errors = []

    def worker(tag):
        try:
            with exclusive(lock_path):
                order.append(f'{tag}:enter')
                time.sleep(0.05)
                order.append(f'{tag}:exit')
        except OSError as exc:  # 修复前：Errno 36 Resource deadlock avoided
            errors.append(f'{tag}: {exc}')

    threads = [threading.Thread(target=worker, args=(t,)) for t in ('A', 'B')]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert errors == []
    assert order == ['A:enter', 'A:exit', 'B:enter', 'B:exit'] or order == ['B:enter', 'B:exit', 'A:enter', 'A:exit']


def test_exclusive_serializes_critical_section(tmp_path):
    lock_path = tmp_path / 'publish.lock'
    counter = {'value': 0}

    def worker():
        for _ in range(20):
            with exclusive(lock_path):
                current = counter['value']
                time.sleep(0.001)
                counter['value'] = current + 1

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert counter['value'] == 80


def test_try_exclusive_still_nonblocking(tmp_path):
    lock_path = tmp_path / 'ledger.lock'
    with try_exclusive(lock_path) as first:
        assert first is not None
        assert try_exclusive(lock_path) is None
    assert try_exclusive(lock_path) is not None
