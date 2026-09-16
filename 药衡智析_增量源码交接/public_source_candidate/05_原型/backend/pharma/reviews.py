"""Human review records bound to the exact artifact bytes they judged.

Reviews are entered by real reviewers only; neither the developer model nor a
visual model may sign. A review stays valid only while the artifact hashes it
was bound to still match the registered artifacts — content changes expire it.
"""
from contextlib import contextmanager
from datetime import datetime
import hashlib, json, sqlite3, uuid
from .config import DB_PATH

REVIEW_DIMENSIONS = ('section_completeness', 'readability', 'visual_quality')


def now(): return datetime.now().astimezone().isoformat()


class ReviewStore:
    def __init__(self, path=DB_PATH):
        self.path = path
        with self.db() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS reviews(
            id TEXT PRIMARY KEY,job_id TEXT NOT NULL,docx_sha256 TEXT, pdf_sha256 TEXT,
            reviewer TEXT NOT NULL,reviewed_at TEXT NOT NULL,attribution_score INTEGER,
            dimensions TEXT NOT NULL,comment TEXT,created_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS reviews_job ON reviews(job_id,created_at);''')

    @contextmanager
    def db(self):
        c = sqlite3.connect(self.path, timeout=10); c.row_factory = sqlite3.Row
        c.execute('PRAGMA journal_mode=WAL')
        try:
            with c: yield c
        finally: c.close()

    def _decode(self, row):
        r = dict(row); r['dimensions'] = json.loads(r['dimensions']); return r

    def submit(self, job, docx_sha256, pdf_sha256, reviewer, attribution_score, dimensions, comment=''):
        """Validate one review against the schema; the caller binds hashes."""
        reviewer = (reviewer or '').strip()
        if not reviewer: raise ValueError('REVIEWER_REQUIRED')
        if not isinstance(attribution_score, int) or not 0 <= attribution_score <= 5:
            raise ValueError('ATTRIBUTION_SCORE_0_TO_5')
        normalized = {}
        for name in REVIEW_DIMENSIONS:
            dim = (dimensions or {}).get(name)
            if not isinstance(dim, dict) or dim.get('status') not in ('PASS', 'FAIL'):
                raise ValueError(f'DIMENSION_{name.upper()}_PASS_OR_FAIL_REQUIRED')
            normalized[name] = {'status': dim['status'], 'comment': str(dim.get('comment', ''))[:2000]}
        rid = 'REV-' + uuid.uuid4().hex[:20]
        with self.db() as c:
            c.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (rid, job['id'], docx_sha256, pdf_sha256, reviewer, now(),
                       attribution_score, json.dumps(normalized, ensure_ascii=False),
                       str(comment or '')[:4000], now()))
        return self.get(rid)

    def get(self, review_id):
        with self.db() as c:
            row = c.execute('SELECT * FROM reviews WHERE id=?', (review_id,)).fetchone()
        if row is None: raise KeyError('REVIEW_NOT_FOUND')
        return self._decode(row)

    def list_for_job(self, job_id):
        with self.db() as c:
            return [self._decode(r) for r in c.execute(
                'SELECT * FROM reviews WHERE job_id=? ORDER BY created_at DESC', (job_id,))]

    def latest_valid(self, job, current_hashes):
        """Newest review whose bound hashes equal the current artifact hashes.
        A FAIL verdict is still a valid review; only content drift expires it."""
        for review in self.list_for_job(job['id']):
            bound = {'docx': review['docx_sha256'], 'pdf': review['pdf_sha256']}
            if bound == current_hashes:
                review['valid'] = True
                return review
        return None
