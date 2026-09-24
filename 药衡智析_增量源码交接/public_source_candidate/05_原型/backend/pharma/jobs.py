"""SQLite 持久任务队列；单 worker 在安全检查点恢复。"""
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
import hashlib,json,sqlite3,uuid
from .config import DB_PATH,ARTIFACTS
from .sqlite_utils import enable_wal

STAGES=['VALIDATING','COMPUTING','RETRIEVING','GENERATING','RENDERING_DOCX','CONVERTING_PDF','VERIFYING']
TERMINAL=('SUCCEEDED','DEGRADED','FAILED')
def stamp():return datetime.now().astimezone().isoformat()

class JobStore:
    def __init__(self,path=DB_PATH):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:c.executescript('''CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY,body TEXT NOT NULL,created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,cache_key TEXT UNIQUE,kind TEXT NOT NULL,status TEXT NOT NULL,stage TEXT NOT NULL,input TEXT NOT NULL,result TEXT NOT NULL,created TEXT NOT NULL,updated TEXT NOT NULL,error TEXT,progress INTEGER,detail TEXT);
        CREATE TABLE IF NOT EXISTS job_events(id INTEGER PRIMARY KEY,job_id TEXT,stage TEXT,at TEXT,detail TEXT);
        CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,job_id TEXT,path TEXT NOT NULL,sha256 TEXT NOT NULL,format TEXT NOT NULL);''')
        # 旧库就地迁移：进度条列（2026-09-22 三模块改版，数据中心解析流水线用）
        with self.db() as c:
            for column,ddl in (('progress','ALTER TABLE jobs ADD COLUMN progress INTEGER'),
                               ('detail','ALTER TABLE jobs ADD COLUMN detail TEXT'),
                               ('event_detail','ALTER TABLE job_events ADD COLUMN detail TEXT')):
                try:c.execute(ddl)
                except sqlite3.OperationalError:pass
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=15);c.row_factory=sqlite3.Row
        try:
            enable_wal(c)
            with c:yield c
        finally:c.close()
    def snapshot(self,body):
        with self.db() as c:c.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?)',(body['snapshot_id'],json.dumps(body,ensure_ascii=False),stamp()))
        return body
    def get_snapshot(self,id):
        with self.db() as c:r=c.execute('SELECT body FROM snapshots WHERE id=?',(id,)).fetchone()
        if not r:raise KeyError('SNAPSHOT_NOT_FOUND')
        return json.loads(r['body'])
    def enqueue(self,kind,payload,cache_key=None,retry=False):
        id=uuid.uuid4().hex;initial={}
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            if cache_key:
                old=c.execute('SELECT * FROM jobs WHERE cache_key=?',(cache_key,)).fetchone()
                if old and old['status'] != 'FAILED':
                    previous=self._decode(old)
                    retryable=retry and previous['kind']=='report' and previous['status']=='DEGRADED'
                    if not retryable and (previous['status'] not in TERMINAL or previous['kind']!='report' or self.artifacts_healthy(previous)):
                        return previous
                    # 重试（fix5）：服务恢复后允许对 DEGRADED 报告重新尝试；旧任务
                    # 保留在历史中，新任务复用已验证的确定性计算结果。
                    if retryable:
                        payload={**payload,'retry_of':old['id'],'retry_reason':'DEGRADED_RETRY_REQUESTED'}
                        c.execute('INSERT INTO job_events(job_id,stage,at) VALUES(?,?,?)',(old['id'],'CACHE_INVALIDATED_RETRY',stamp()))
                    else:
                        payload={**payload,'repair_of':old['id'],'repair_reason':'ARTIFACT_MISSING_OR_HASH_MISMATCH'}
                        c.execute('INSERT INTO job_events(job_id,stage,at) VALUES(?,?,?)',(old['id'],'CACHE_INVALIDATED_ARTIFACT',stamp()))
                    # Re-render only; validated calculations and explanations retain provenance.
                    initial={k:v for k,v in previous['result'].items() if k in ('snapshot','evidence','benchmark')}
                    if previous['result'].get('narrative',{}).get('status')=='PASS':initial['narrative']=previous['result']['narrative']
                    initial['repair_provenance']={'source_job_id':old['id'],'reason':payload.get('repair_reason') or payload['retry_reason']}
                if old:c.execute('UPDATE jobs SET cache_key=NULL WHERE id=?',(old['id'],))
            c.execute('INSERT INTO jobs(id,cache_key,kind,status,stage,input,result,created,updated,progress,detail) '
                      'VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                      (id,cache_key,kind,'QUEUED','VALIDATING',json.dumps(payload,ensure_ascii=False),
                       json.dumps(initial,ensure_ascii=False),stamp(),stamp(),0,None))
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
    def list_jobs(self,context_id=None,limit=100,offset=0):
        """先按业务范围查询、再分页：指定企业的历史任务不受全局截断影响（fix7）。"""
        limit=max(1,min(int(limit),500));offset=max(0,int(offset))
        with self.db() as c:
            if context_id is None:
                rows=c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT ? OFFSET ?',(limit,offset)).fetchall()
            else:
                rows=c.execute("SELECT * FROM jobs WHERE json_extract(input,'$.context_id')=? ORDER BY created DESC LIMIT ? OFFSET ?",(context_id,limit,offset)).fetchall()
            return [self._decode(r) for r in rows]
    def list_reports(self,limit=300):
        """报告任务专用查询：决策引擎据此判断口径匹配报告，不受通用列表截断影响。"""
        with self.db() as c:return [self._decode(r) for r in c.execute('SELECT * FROM jobs WHERE kind=? ORDER BY created DESC LIMIT ?',('report',limit))]
    def latest_report_for_snapshot(self,snapshot_id):
        with self.db() as c:
            row=c.execute("SELECT * FROM jobs WHERE kind='report' AND json_extract(input,'$.snapshot_id')=? ORDER BY created DESC LIMIT 1",(snapshot_id,)).fetchone()
        return self._decode(row) if row else None
    def artifacts_healthy(self,job):
        for fmt in ('docx','pdf'):
            item=job.get('result',{}).get(fmt,{})
            if item.get('status')!='PASS' or not item.get('artifact_id'):return False
            try:
                path=self.artifact_path(item['artifact_id'])
                if hashlib.sha256(path.read_bytes()).hexdigest()!=item.get('sha256'):return False
            except (OSError,ValueError,KeyError):return False
        return True
    def next(self):
        with self.db() as c:
            r=c.execute("SELECT * FROM jobs WHERE status NOT IN ('SUCCEEDED','DEGRADED','FAILED') ORDER BY created LIMIT 1").fetchone()
            return self._decode(r) if r else None
    def update(self,id,stage,result=None,error=None,progress=None,detail=None):
        """更新任务状态；progress(0-100)+detail(当前进度内容) 供前端进度条轮询。

        progress=None 表示本阶段未给出新百分比（保留上次值）；终态时进度强制收敛
        （SUCCEEDED/DEGRADED=100，FAILED 保留出错的百分比便于定位）。
        """
        status=stage if stage in TERMINAL else 'RUNNING'
        if progress is None and status in ('SUCCEEDED','DEGRADED'):progress=100
        with self.db() as c:
            c.execute('UPDATE jobs SET status=?,stage=?,result=COALESCE(?,result),error=?,'
                      'progress=COALESCE(?,progress),detail=COALESCE(?,detail),updated=? WHERE id=?',
                      (status,stage,json.dumps(result,ensure_ascii=False) if result is not None else None,
                       error,progress,detail,stamp(),id))
            c.execute('INSERT INTO job_events(job_id,stage,at,detail) VALUES(?,?,?,?)',(id,stage,stamp(),detail))
    def history(self,id):
        with self.db() as c:return [dict(r) for r in c.execute('SELECT stage,at,detail FROM job_events WHERE job_id=? ORDER BY id',(id,))]
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
