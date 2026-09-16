"""Cross-platform exclusive file lock; keeps POSIX behavior unchanged."""
from contextlib import contextmanager

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None
    import msvcrt


@contextmanager
def exclusive(path):
    """Hold an exclusive lock on `path` for the duration of the block."""
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
