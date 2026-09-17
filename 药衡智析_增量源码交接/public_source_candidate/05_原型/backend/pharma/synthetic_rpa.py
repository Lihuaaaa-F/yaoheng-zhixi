"""Public independent simulator. No private mock implementation is distributed."""
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
import sqlite3,json
from .config import RUNTIME
app=FastAPI(title='Independent synthetic RPA simulator')
DB=RUNTIME/'synthetic_rpa.sqlite3'
class Task(BaseModel):
    task_id:str;task_title:str;assignee:dict;source:dict;priority:str;deadline:str;created_at:str;suggestion:str;notify_method:str='wechat'
def connect():
    db=sqlite3.connect(DB);db.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,body TEXT)');return db
@app.get('/health')
def health():return {'status':'ok','simulation':True}
@app.post('/api/rpa/tasks')
def create(task:Task):
    at=datetime.now().astimezone().isoformat();body=task.model_dump()
    body.update(status='sent',notify_status={'wechat':f"已发送至 {task.assignee['name']}({task.assignee['department']})",'sent_at':at},status_history=[{'status':'sent','time':at}],simulation=True)
    with connect() as db:
        try:db.execute('INSERT INTO tasks VALUES (?,?)',(task.task_id,json.dumps(body)))
        except sqlite3.IntegrityError:raise HTTPException(400,'Duplicate task')
    return {'code':200,'data':body}
@app.get('/api/rpa/tasks/{task_id}')
def get(task_id:str):
    with connect() as db:r=db.execute('SELECT body FROM tasks WHERE id=?',(task_id,)).fetchone()
    if not r:raise HTTPException(404,'Task not found')
    return {'code':200,'data':json.loads(r[0])}
