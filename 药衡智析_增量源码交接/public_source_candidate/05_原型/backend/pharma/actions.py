"""用户确认、事务 outbox 与题包原 mock 的可靠模拟发送。"""
from pathlib import Path
from datetime import datetime, timedelta
from contextlib import contextmanager
import hashlib,json,sqlite3,uuid,re
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .config import DB_PATH,RPA_BASE_URL

def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

class ExecutableAction(BaseModel):
    """One contract at draft, merged edit and confirmation boundaries."""
    model_config=ConfigDict(extra='forbid')
    task_title:str=Field(min_length=1,max_length=100)
    suggestion:str=Field(min_length=1)
    priority:Literal['high','medium','low']
    deadline:date
    assignee:dict
    source:dict
    verification_target:str=Field(min_length=1)
    expected_evidence:list[str]=Field(min_length=1)
    responsible_role:str=Field(min_length=1)
    deadline_basis:str=Field(min_length=1)

    @field_validator('*',mode='before')
    @classmethod
    def concrete(cls,value):
        def check(v):
            if isinstance(v,str):
                if not v.strip() or re.search(r'\[\[.*?\]\]|\{\{.*?\}\}',v):raise ValueError('UNRESOLVED_OR_EMPTY_ACTION_FIELD')
            elif isinstance(v,list):
                for x in v:check(x)
            elif isinstance(v,dict):
                for x in v.values():
                    if x is not None:check(x)
        check(value);return value

    @field_validator('assignee')
    @classmethod
    def assignee_complete(cls,value):
        if not all(isinstance(value.get(k),str) and value[k].strip() for k in ('name','department')):raise ValueError('REQUIRED_ASSIGNEE')
        return value

    @field_validator('source')
    @classmethod
    def source_complete(cls,value):
        if not all(isinstance(value.get(k),str) and value[k].strip() for k in ('analysis_type','analysis_month','product','finding')):raise ValueError('REQUIRED_SOURCE')
        return value

def validate_action(payload,metadata):
    return ExecutableAction.model_validate({**{k:payload[k] for k in ('task_title','suggestion','priority','deadline','assignee','source')},**action_details(metadata)})

def validate_edit_types(changes):
    if not isinstance(changes,dict):raise ValueError('ACTION_EDIT_OBJECT_REQUIRED')
    for key,value in changes.items():
        if key=='assignee':
            if not isinstance(value,dict):raise ValueError('ASSIGNEE_OBJECT_REQUIRED')
        elif key=='expected_evidence':
            if not isinstance(value,list) or any(not isinstance(x,str) for x in value):raise ValueError('EVIDENCE_STRING_LIST_REQUIRED')
        elif not isinstance(value,str):raise ValueError('ACTION_FIELD_STRING_REQUIRED:'+key)

def confirmed_payload_matches(payload,remote):
    return isinstance(remote,dict) and all(k in remote and remote[k]==v for k,v in payload.items())

def notification_proven(remote):
    if not isinstance(remote,dict):return False
    notify=remote.get('notify_status')
    if isinstance(notify,dict):
        status=notify.get('wechat');at=notify.get('sent_at')
        # Original mock protocol is a recipient-specific Chinese receipt.
        if isinstance(status,str) and re.fullmatch(r'已发送至 .+\(.+\)',status) and isinstance(at,str) and at.strip():return True
    history=remote.get('status_history',[])
    return isinstance(history,list) and any(isinstance(x,dict) and x.get('status')=='sent' and isinstance(x.get('time'),str) and bool(x['time'].strip()) for x in history)

def protocol_data(body):
    if not isinstance(body,dict) or type(body.get('code')) is not int or not isinstance(body.get('data'),dict):raise ValueError('RPA_PROTOCOL_ERROR')
    data=body['data']
    if data.get('status') not in ('received','sent','confirmed','in_progress','completed'):raise ValueError('RPA_PROTOCOL_STATUS')
    if not isinstance(data.get('task_id'),str):raise ValueError('RPA_PROTOCOL_TASK_ID')
    if data.get('notify_status') is not None and not isinstance(data['notify_status'],dict):raise ValueError('RPA_PROTOCOL_NOTIFY')
    if 'status_history' in data and (not isinstance(data['status_history'],list) or any(not isinstance(x,dict) for x in data['status_history'])):raise ValueError('RPA_PROTOCOL_HISTORY')
    return data

def action_details(meta):
    keys=('verification_target','expected_evidence','responsible_role','deadline_basis')
    return {k:meta.get(k) for k in keys}

def action_identity(payload,meta):
    return digest({'payload':payload,'action_details':action_details(meta)})

def now():return datetime.now().astimezone().isoformat()

class ActionStore:
    def __init__(self,path=DB_PATH):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.db() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY,business_hash TEXT UNIQUE,payload TEXT NOT NULL,payload_hash TEXT NOT NULL,status TEXT NOT NULL,metadata TEXT NOT NULL,remote TEXT,updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS outbox(action_id TEXT PRIMARY KEY,confirmed_hash TEXT NOT NULL,state TEXT NOT NULL,attempts INTEGER NOT NULL DEFAULT 0,last_error TEXT);
            CREATE TABLE IF NOT EXISTS action_events(id INTEGER PRIMARY KEY,action_id TEXT,state TEXT,at TEXT,detail TEXT);''')
    @contextmanager
    def db(self):
        c=sqlite3.connect(self.path,timeout=10);c.row_factory=sqlite3.Row
        c.execute('PRAGMA journal_mode=WAL');c.execute('PRAGMA foreign_keys=ON')
        try:
            with c:yield c
        finally:c.close()
    def _decode(self,row):
        if row is None:raise KeyError('ACTION_NOT_FOUND')
        r=dict(row)
        for k in ('payload','metadata','remote'):r[k]=json.loads(r[k]) if r[k] else None
        remote=r.get('remote') or {}
        r['responsibility_confirmation']=r['metadata'].get('responsibility_confirmation')
        r['delivery']={'http_accepted':r['status'] in ('SENT','ACCEPTED'),'notification': 'SIMULATED_SENT' if r['status'] in ('SENT','ACCEPTED') and notification_proven(remote) else 'UNKNOWN','remediation':remote.get('status') if remote.get('status') in ('confirmed','in_progress','completed') else 'NOT_CONFIRMED'}
        return r
    def get(self,action_id):
        with self.db() as c:return self._decode(c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
    def list(self):
        with self.db() as c:return [self._decode(r) for r in c.execute('SELECT * FROM actions ORDER BY updated DESC')]
    def draft(self,snapshot,finding,assignee,suggestion,priority='medium',verification_target=None,expected_evidence=None,responsible_role=None,deadline_basis=None):
        if priority not in ('high','medium','low'):raise ValueError('INVALID_PRIORITY')
        validate_edit_types({'finding':finding,'suggestion':suggestion,'assignee':assignee})
        if not finding.strip() or not suggestion.strip() or not assignee.get('name') or not assignee.get('department'):raise ValueError('REQUIRED_FIELDS')
        assignee={k:v for k,v in assignee.items() if k in ('name','department','role')};assignee.setdefault('role',None)
        action_meta={'verification_target':verification_target,'expected_evidence':expected_evidence,'responsible_role':responsible_role,'deadline_basis':deadline_basis}
        business=digest({'action_meta':action_meta,'context':snapshot.get('analysis_context'),'snapshot_id':snapshot['snapshot_id'],'finding':finding,'assignee':assignee,'suggestion':suggestion,'priority':priority})
        task_id='YH-'+business[:24]
        payload={'task_id':task_id,'task_title':finding[:100],'assignee':assignee,'source':{'analysis_type':snapshot['analysis_type'],'analysis_month':snapshot['month'],'product':snapshot['product'],'finding':finding+'；分析期间：'+snapshot.get('period',{}).get('start',snapshot['month'])+' 至 '+snapshot.get('period',{}).get('end',snapshot['month'])},'priority':priority,'deadline':(datetime.now()+timedelta(days=7)).strftime('%Y-%m-%d'),'created_at':now(),'suggestion':suggestion,'notify_method':'wechat'}
        validate_action(payload,action_meta)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT * FROM actions WHERE business_hash=?',(business,)).fetchone()
            if old:return self._decode(old)
            if c.execute('SELECT 1 FROM actions WHERE id=?',(task_id,)).fetchone():
                task_id='YH-'+uuid.uuid4().hex[:24];payload['task_id']=task_id
            c.execute('INSERT INTO actions VALUES(?,?,?,?,?,?,?,?)',(task_id,business,json.dumps(payload,ensure_ascii=False),action_identity(payload,action_meta),'DRAFT',json.dumps({'context_id':snapshot.get('context_id'),'analysis_context':snapshot.get('analysis_context'),'snapshot_id':snapshot['snapshot_id'],'period':snapshot.get('period'),'simulation':True,**action_meta,'deadline_policy':'草稿默认建议七日内复核，用户确认前可修改；非既定业务期限'},ensure_ascii=False),None,now()))
        return self.get(task_id)
    def edit(self,action_id,changes):
        validate_edit_types(changes)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');a=self._decode(c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
            if a['status'] not in ('DRAFT',):raise ValueError('已确认内容不可编辑；请重新生成草稿')
            allowed={'task_title','suggestion','priority','assignee','deadline','snapshot_id','finding','verification_target','expected_evidence','responsible_role','deadline_basis'}
            if set(changes)-allowed:raise ValueError('UNSUPPORTED_EDIT_FIELDS')
            if changes.get('snapshot_id',a['metadata']['snapshot_id'])!=a['metadata']['snapshot_id']:raise ValueError('SNAPSHOT_CHANGE_REQUIRES_NEW_DRAFT')
            if 'finding' in changes:
                finding=changes['finding'].strip()
                if not finding:raise ValueError('REQUIRED_FINDING')
                a['payload']['task_title']=finding[:100]
                period=a['metadata'].get('period') or {}
                a['payload']['source']['finding']=finding+'；分析期间：'+period.get('start',a['payload']['source']['analysis_month'])+' 至 '+period.get('end',a['payload']['source']['analysis_month'])
            for key in ('task_title','suggestion','priority','assignee','deadline'):
                if key in changes:a['payload'][key]=changes[key]
            if a['payload']['priority'] not in ('high','medium','low'):raise ValueError('INVALID_PRIORITY')
            if not a['payload']['assignee'].get('name') or not a['payload']['assignee'].get('department'):raise ValueError('REQUIRED_ASSIGNEE')
            a['payload']['assignee'].setdefault('role',None)
            for key in ('verification_target','expected_evidence','responsible_role','deadline_basis'):
                if key in changes:a['metadata'][key]=changes[key]
            if not a['payload']['suggestion'].strip():raise ValueError('REQUIRED_SUGGESTION')
            validate_action(a['payload'],a['metadata'])
            business=digest({'context':a['metadata'].get('analysis_context'),'action_meta':action_details(a['metadata']),'snapshot_id':a['metadata']['snapshot_id'],'finding':a['payload']['source']['finding'].split('；分析期间：')[0],'assignee':a['payload']['assignee'],'suggestion':a['payload']['suggestion'],'priority':a['payload']['priority']})
            duplicate=c.execute('SELECT id FROM actions WHERE business_hash=? AND id<>?',(business,action_id)).fetchone()
            if duplicate:raise ValueError('DUPLICATE_DRAFT_USE_EXISTING:'+duplicate['id'])
            c.execute('UPDATE actions SET payload=?,payload_hash=?,business_hash=?,metadata=?,updated=? WHERE id=?',(json.dumps(a['payload'],ensure_ascii=False),action_identity(a['payload'],a['metadata']),business,json.dumps(a['metadata'],ensure_ascii=False),now(),action_id))
        return self.get(action_id)
    def confirm(self,action_id,payload_hash):
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');a=self._decode(c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
            validate_action(a['payload'],a['metadata'])
            if payload_hash!=a['payload_hash']:raise ValueError('PAYLOAD_CHANGED_RECONFIRM_REQUIRED')
            if a['status']=='DRAFT':
                c.execute('INSERT INTO outbox(action_id,confirmed_hash,state) VALUES(?,?,?)',(action_id,payload_hash,'QUEUED'))
                c.execute('UPDATE actions SET status=?,updated=? WHERE id=?',('QUEUED',now(),action_id))
                c.execute('INSERT INTO action_events(action_id,state,at,detail) VALUES(?,?,?,?)',(action_id,'CONFIRMED_BY_USER',now(),payload_hash))
        return self.get(action_id)
    def acknowledge(self,action_id,confirmed_by,comment=''):
        """A named human acknowledgement, distinct from outbox confirmation."""
        if not isinstance(confirmed_by,str) or not confirmed_by.strip():raise ValueError('HUMAN_NAME_REQUIRED')
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            a=self._decode(c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
            if a['status'] not in ('SENT','ACCEPTED'):raise ValueError('ACKNOWLEDGEMENT_REQUIRES_DELIVERY')
            if a['metadata'].get('responsibility_confirmation'):return a
            a['metadata']['responsibility_confirmation']={'status':'CONFIRMED','confirmed_by':confirmed_by.strip(),'confirmed_at':now(),'comment':str(comment)[:2000],'source':'human_entry','remediation_completed':False}
            c.execute('UPDATE actions SET metadata=?,updated=? WHERE id=?',(json.dumps(a['metadata'],ensure_ascii=False),now(),action_id))
        return self.get(action_id)
    def pending(self):
        with self.db() as c:return [dict(r) for r in c.execute("SELECT * FROM outbox WHERE state IN ('QUEUED','SENDING')")]
    def _state(self,action_id,state,remote=None,error=None):
        with self.db() as c:
            c.execute('UPDATE actions SET status=?,remote=?,updated=? WHERE id=?',(state,json.dumps(remote,ensure_ascii=False) if remote else None,now(),action_id))
            c.execute('UPDATE outbox SET state=?,last_error=? WHERE action_id=?',(state,error,action_id))
            c.execute('INSERT INTO action_events(action_id,state,at,detail) VALUES(?,?,?,?)',(action_id,state,now(),error))
        return self.get(action_id)
    def _protocol_error(self,a,error):
        # Preserve previously proved state and payload; quarantine unknown sends.
        state=a['status'] if a['status'] in ('SENT','ACCEPTED') else 'DELIVERY_UNKNOWN'
        return self._state(a['id'],state,a.get('remote'),error)
    def _query_failed(self,a,error):
        a['metadata']['last_query']={'status':'FAILED','at':now(),'error':error}
        with self.db() as c:c.execute('UPDATE actions SET metadata=? WHERE id=?',(json.dumps(a['metadata'],ensure_ascii=False),a['id']))
        return self._protocol_error(a,error)
    def _reconcile(self,a,client,base_url,already_sent=False):
        import httpx
        try:
            r=client.get(base_url+'/api/rpa/tasks/'+a['id']);body=r.json()
            if r.status_code==200:
                remote=protocol_data(body)
                if body['code']!=200:return self._protocol_error(a,'RPA_PROTOCOL_BUSINESS_STATUS')
                same=confirmed_payload_matches(a['payload'],remote)
                if not same:return self._state(a['id'],'CONFLICT',remote,'远端同ID payload 冲突')
                if remote.get('status') in ('sent','received','confirmed','in_progress','completed'):
                    if notification_proven(a.get('remote')) and not notification_proven(remote):remote['notify_status']=a['remote'].get('notify_status',{})
                    return self._state(a['id'],'SENT' if notification_proven(remote) else 'ACCEPTED',remote)
            return self._query_failed(a,'远端不存在或结果无法确认；停止自动重发')
        except ValueError:return self._query_failed(a,'RPA_PROTOCOL_ERROR')
        except httpx.HTTPError:return self._query_failed(a,'查询失败；停止自动重发')
    def deliver_one(self,action_id,client=None,base_url=RPA_BASE_URL):
        import httpx
        if client is None:
            with httpx.Client(timeout=httpx.Timeout(10,connect=3)) as actual:return self.deliver_one(action_id,actual,base_url)
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE');a=self._decode(c.execute('SELECT * FROM actions WHERE id=?',(action_id,)).fetchone())
            ob=c.execute('SELECT * FROM outbox WHERE action_id=?',(action_id,)).fetchone()
            if not ob or a['status']=='DRAFT':raise ValueError('USER_CONFIRMATION_REQUIRED')
            if ob['confirmed_hash']!=a['payload_hash']:raise ValueError('PAYLOAD_CHANGED_RECONFIRM_REQUIRED')
            if a['status'] not in ('QUEUED','SENDING'):return a
            recovered=a['status']=='SENDING'
            c.execute("UPDATE actions SET status='SENDING' WHERE id=?",(action_id,));c.execute("UPDATE outbox SET state='SENDING',attempts=attempts+1 WHERE action_id=?",(action_id,))
        if recovered:return self._reconcile(a,client,base_url)
        try:
            r=client.post(base_url+'/api/rpa/tasks',json=a['payload'])
            try:body=r.json()
            except ValueError:body={}
            if r.status_code==422:return self._state(action_id,'FAILED',None,'HTTP_422:参数被原mock拒绝')
            try:data=protocol_data(body)
            except ValueError:return self._reconcile(a,client,base_url)
            if r.status_code==200 and body.get('code')==200 and confirmed_payload_matches(a['payload'],data) and data.get('status')=='sent' and notification_proven(data):
                data['tracking_url']=base_url+'/api/rpa/tasks/'+action_id
                return self._state(action_id,'SENT',data)
            return self._reconcile(a,client,base_url)
        except httpx.HTTPError:return self._reconcile(a,client,base_url)
    def refresh(self,action_id,client=None,base_url=RPA_BASE_URL):
        import httpx
        if client is None:
            with httpx.Client(timeout=8) as actual:return self.refresh(action_id,actual,base_url)
        a=self.get(action_id)
        if a['status'] not in ('SENT','REMOTE_UNKNOWN','DELIVERY_UNKNOWN','ACCEPTED'):return a
        return self._reconcile(a,client,base_url,a['status'] in ('SENT','REMOTE_UNKNOWN'))
