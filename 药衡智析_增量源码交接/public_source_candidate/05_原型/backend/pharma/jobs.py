"""SQLite 持久任务队列；单 worker 在安全检查点恢复。"""
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
import hashlib,json,sqlite3,uuid
from .config import DB_PATH,ARTIFACTS

STAGES=['VALIDATING','COMPUTING','RETRIEVING','GENERATING','RENDERING_DOCX','CONVERTING_PDF','VERIFYING']
TERMINAL=('SUCCEEDED','DEGRADED','FAILED')
def stamp():return datetime.now().astimezone().isoformat()

class JobStore:
    def __init__(self,path=DB_PATH):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:c.executescript('''CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,body TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,cache_key TEXT UNIQUE,kind TEXT NOT NULL,status TEXT NOT NULL,stage TEXT NOT NULL,input TEXT NOT NULL,result TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,error TEXT);
        CREATE TABLE IF NOT EXISTS job_events(id INTEGER PRIMARY KEY,job_id TEXT,stage TEXT,at TEXT);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,job_id TEXT,path TEXT NOT NULL,sha256 TEXT NOT NULL,format TEXT NOT NULL);''')
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=15);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL')
        try:
            with c:yield c
        finally:c.close()
    def snapshot(self,body):
        with self.db() as c:c.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)',(body['snapshot_id'],json.dumps(body,ensure_ascii=False),stamp()))
        return body
    def get_snapshot(self,id):
        with self.db() as c:r=c.execute('SELECT body FROM snapshots WHERE id=?',(id,)).fetchone()
        if not r:raise KeyError('SNAPSHOT_NOT_FOUND')
        return json.loads(r['body'])
    def enqueue(self,kind,payload,cache_key=None):
        id=uuid.uuid4().hex
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            if cache_key:
                old=c.execute('SELECT id,status FROM jobs WHERE cache_key=?',(cache_key,)).fetchone()
                if old and old['status'] != 'FAILED':return self.get(old['id'])
                if old:c.execute('UPDATE jobs SET cache_key=NULL WHERE id=?',(old['id'],))
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?,?,?,?)',(id,cache_key,kind,'QUEUED','VALIDATING',json.dumps(payload,ensure_ascii=False),'{}',stamp(),stamp(),None))
        return self.get(id)
    def _decode(self,row):
        if row is None:raise KeyError('JOB_NOT_FOUND')
        d=dict(row)
        for k in ('input','result'):d[k]=json.loads(d[k])
        return d
    def get(self,id):
        with self.db() as c:return self._decode(c.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone())
    def list(self):
        with self.db() as c:return [self._decode(r) for r in c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 100')]
    def next(self):
        with self.db() as c:
            r=c.execute("SELECT * FROM jobs WHERE status NOT IN ('SUCCEEDED','DEGRADED','FAILED') ORDER BY created LIMIT 1").fetchone()
            return self._decode(r) if r else None
    def update(self,id,stage,result=None,error=None):
        with self.db() as c:
            c.execute('UPDATE jobs SET status=?,stage=?,result=COALESCE(?,result),error=?,updated=? WHERE id=?',(stage if stage in TERMINAL else 'RUNNING',stage,json.dumps(result,ensure_ascii=False) if result is not None else None,error,stamp(),id))
            c.execute('INSERT INTO job_events(job_id,stage,at) VALUES(?,?,?)',(id,stage,stamp()))
    def history(self,id):
        with self.db() as c:return [dict(r) for r in c.execute('SELECT stage,at FROM job_events WHERE job_id=? ORDER BY id',(id,))]
    def artifact(self,job_id,record,format):
        id=job_id+'-'+format;path=Path(record['path']).resolve()
        if not path.is_relative_to(ARTIFACTS.resolve()):raise ValueError('ARTIFACT_OUTSIDE_ROOT')
        with self.db() as c:c.execute('INSERT OR REPLACE INTO artifacts VALUES(?,?,?,?,?)',(id,job_id,str(path),record['sha256'],format))
        return {'artifact_id':id,**{k:v for k,v in record.items() if k!='path'}}
    def artifact_path(self,id,preview=False):
        with self.db() as c:r=c.execute('SELECT * FROM artifacts WHERE id=?',(id,)).fetchone()
        if not r:raise KeyError('ARTIFACT_NOT_FOUND')
        status=self.get(r['job_id'])['status']
        if status=='FAILED':raise KeyError('ARTIFACT_JOB_FAILED')
        # preview=True serves the already-registered bytes of a running job,
        # explicitly labelled as an unreviewed draft; never a half-written file.
        if not preview and status not in ('SUCCEEDED','DEGRADED'):raise ValueError('ARTIFACT_NOT_FINAL_RETRY_AFTER_JOB_COMPLETION')
        path=Path(r['path']).resolve()
        if not path.is_relative_to(ARTIFACTS.resolve()) or not path.is_file():raise KeyError('ARTIFACT_MISSING')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('ARTIFACT_HASH_MISMATCH')
        return path
