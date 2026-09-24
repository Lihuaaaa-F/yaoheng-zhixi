"""Cross-platform exclusive file lock; keeps POSIX behavior unchanged."""
import os
import threading
from contextlib import contextmanager

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt

# Windows 文件锁按"进程"持有：同进程第二个线程对同一区域 msvcrt.locking(LK_LOCK)
# 立即抛 EDEADLK（Errno 36），不会像跨进程那样重试等待——2026-09-24 审查实测
# /api/benchmarks 双请求并发首建知识库时双双 500 即此因。先用进程内互斥量按路径
# 串行化，再取跨进程文件锁；POSIX 行为不受影响。
_process_locks: dict[str, threading.Lock] = {}
_process_locks_guard = threading.Lock()


def _process_key(path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


@contextmanager
def exclusive(path):
    """Hold an exclusive lock on `path` for the duration of the block."""
    key = _process_key(path)
    with _process_locks_guard:
        process_lock = _process_locks.setdefault(key, threading.Lock())
    with process_lock:
        with open(path, 'a') as handle:
            if fcntl is not None:
                fcntl.flock(handle, fcntl.LOCK_EX)
            else:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle, fcntl.LOCK_UN)
                else:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


def try_exclusive(path):
    """Return an active lock context manager, or None if already held."""
    import errno
    handle = open(path, 'a')
    try:
        if fcntl is not None:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    except (BlockingIOError, OSError) as exc:
        handle.close()
        if isinstance(exc, OSError) and exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
            raise
        return None
    return handle
