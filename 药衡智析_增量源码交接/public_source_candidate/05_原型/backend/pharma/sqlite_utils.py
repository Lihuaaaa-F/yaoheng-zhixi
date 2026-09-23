"""Bounded WAL initialization for concurrent API/worker startup."""
import sqlite3
import time


def enable_wal(connection):
    # A journal-mode change can return SQLITE_BUSY immediately even with a
    # connection busy timeout. Retry initialization only, never a transaction.
    deadline = time.monotonic() + 5
    while True:
        try:
            mode = connection.execute('PRAGMA journal_mode').fetchone()[0]
            if mode.lower() != 'wal':
                connection.execute('PRAGMA journal_mode=WAL').fetchone()
            return
        except sqlite3.OperationalError as exc:
            code = getattr(exc, 'sqlite_errorcode', 0) & 0xff
            if code not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED) or time.monotonic() >= deadline:
                raise
            time.sleep(.025)
