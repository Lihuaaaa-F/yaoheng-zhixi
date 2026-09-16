from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path
import hashlib,json,time
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from .config import APP,RUNTIME
from .jobs import JobStore
from .actions import ActionStore
from .metrics import analyze,benchmark,benchmark_analysis,catalog

store=JobStore();actions=ActionStore()
app=FastAPI(title='药衡智析',version='0.1.0')
class AnalysisRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    factory:str='中药一厂';product:str='银黄口服液';month:str=Field(default='2026-05',pattern=r'^20\d{2}-(0[1-9]|1[0-2])$')
    analysis_type:Literal['monthly','quarterly','special']='monthly';basis:Literal['unit','total']='unit'
class SearchRequest(BaseModel):
    query:str=Field(min_length=1,max_length=500);product:str|None=None;mode:Literal['bm25','vector','hybrid']='hybrid'
    month:str|None=None;factory:str|None=None;specification:str|None=None;document_version:str|None=None
class Assignee(BaseModel):
    name:str=Field(min_length=1,max_length=80);department:str=Field(min_length=1,max_length=80);role:str|None=None
class ActionRequest(BaseModel):
    snapshot_id:str;finding:str=Field(min_length=1,max_length=2000);assignee:Assignee;suggestion:str=Field(min_length=1,max_length=2000);priority:Literal['high','medium','low']='medium'
    verification_target:str=Field(min_length=1,max_length=1000);expected_evidence:list[str]=Field(min_length=1);responsible_role:str=Field(min_length=1,max_length=100);deadline_basis:str=Field(min_length=1,max_length=1000)
class ConfirmRequest(BaseModel):payload_hash:str
class ReviewDimension(BaseModel):
    model_config=ConfigDict(extra='forbid')
    status:Literal['PASS','FAIL'];comment:str=''
class ReviewRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    reviewer:str=Field(min_length=1,max_length=80);attribution_score:int=Field(ge=0,le=5)
    section_completeness:ReviewDimension;readability:ReviewDimension;visual_quality:ReviewDimension
    comment:str=''
class ReviewImportEntry(BaseModel):
    model_config=ConfigDict(extra='forbid')
    job_id:str=Field(min_length=8,max_length=64);review:ReviewRequest
class ReviewImport(BaseModel):
    model_config=ConfigDict(extra='forbid')
    entries:list[ReviewImportEntry]=Field(min_length=1,max_length=50)

@app.exception_handler(ValueError)
async def value_error(request,exc):return JSONResponse(status_code=422,content={'error':{'code':'VALIDATION_ERROR','message':str(exc)},'status':'FAILED'})
@app.exception_handler(KeyError)
async def key_error(request,exc):return JSONResponse(status_code=404,content={'error':{'code':'NOT_FOUND','message':str(exc)},'status':'FAILED'})
@app.get('/health')
def health():
    h=RUNTIME/'worker.heartbeat';age=time.time()-float(h.read_text()) if h.exists() else None
    return {'status':'ok','service':'药衡智析','worker':{'alive':age is not None and age<180,'heartbeat_age_seconds':age},'simulation':True}
@app.get('/api/catalog')
def get_catalog():return {**catalog(),'demo_assignee':{'name':'待分配','department':'成本管理部'}}
@app.post('/api/analyses')
def analysis(req:AnalysisRequest):return store.snapshot(analyze(**req.model_dump()))
@app.get('/api/analyses/{id}')
def get_analysis(id:str):return store.get_snapshot(id)
@app.get('/api/benchmarks')
def get_benchmark(product:str,month:str,left:str='中药二厂',right:str='中药一厂'):
    from .knowledge import Knowledge
    from .narrative import generate
    snapshot,result=benchmark_analysis(product,month,left,right)
    result['evidence']=Knowledge().search(product+' 工艺 收率 设备 差异',product=product,limit=5)
    result['narrative']=generate(snapshot,result['evidence'])
    result['hypotheses']=[{**f,'hypothesis':f['rendered_text']} for f in result['narrative']['findings']]
    return result
@app.post('/api/reports',status_code=202)
def report(req:AnalysisRequest):
    from .reports import TEMPLATE,normalize_template,RENDERER_VERSION
    from .narrative import PROMPT_VERSION,ModelGateway
    from .knowledge import Knowledge
    if not TEMPLATE.exists():normalize_template()
    snapshot=store.snapshot(analyze(**req.model_dump()))
    template_version=hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
    gateway=ModelGateway()
    versions={'renderer':RENDERER_VERSION,'snapshot':snapshot['snapshot_id'],'knowledge':Knowledge().version,'template':template_version,'prompt':PROMPT_VERSION,'model':gateway.model,'protocol':gateway.provider,'endpoint':gateway.base_url}
    key=hashlib.sha256(json.dumps(versions,sort_keys=True).encode()).hexdigest()
    j=store.enqueue('report',{'snapshot_id':snapshot['snapshot_id'],'versions':versions},key)
    return {'job_id':j['id'],'status':j['status'],'cache_source_time':j['created']}
@app.get('/api/jobs')
def jobs():return store.list()
@app.get('/api/jobs/{id}')
def job(id:str):return {**store.get(id),'history':store.history(id)}
@app.get('/api/artifacts/{id}')
def artifact(id:str,preview:bool=False):
    p=store.artifact_path(id,preview=preview)
    if preview:
        return FileResponse(p,filename='草稿预览_未审核_'+id+p.suffix,headers={'X-Artifact-Preview':'draft-unreviewed'})
    return FileResponse(p,filename='药衡智析_'+id+p.suffix)

def _current_hashes(job):
    result=job.get('result',{})
    return {'docx':result.get('docx',{}).get('sha256'),'pdf':result.get('pdf',{}).get('sha256')}

def _submit_review(job_id,req):
    job=store.get(job_id)
    if job['status'] not in ('SUCCEEDED','DEGRADED'):raise ValueError('REVIEW_TARGET_NOT_FINAL')
    hashes=_current_hashes(job)
    if not hashes['docx']:raise ValueError('REVIEW_TARGET_HAS_NO_DOCX_ARTIFACT')
    dims={'section_completeness':req.section_completeness.model_dump(),'readability':req.readability.model_dump(),'visual_quality':req.visual_quality.model_dump()}
    from .reviews import ReviewStore
    review=ReviewStore().submit(job,hashes['docx'],hashes['pdf'],req.reviewer,req.attribution_score,dims,req.comment)
    return {'review':review,'acceptance':_recalc_acceptance(job_id)}

def _recalc_acceptance(job_id):
    from .reports import assess_report
    from .reviews import ReviewStore
    reviews=ReviewStore()
    job=store.get(job_id)
    hashes=_current_hashes(job)
    review=reviews.latest_valid(job,hashes)
    acceptance=assess_report(job['result'],review=review)
    result=job['result'];result['acceptance']=acceptance
    result['acceptance_review_binding']={'review_id':review['id'] if review else None,'artifact_hashes':hashes}
    with store.db() as c:c.execute('UPDATE jobs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),job_id))
    expired=[{'review_id':r['id'],'reviewed_at':r['reviewed_at'],'reason':'产物哈希已变化，审核过期'} for r in reviews.list_for_job(job_id) if (r['docx_sha256'],r['pdf_sha256'])!=(hashes['docx'],hashes['pdf'])]
    return {'status':acceptance['overall'],'acceptance':acceptance,'active_review':(review or {}).get('id'),'expired_reviews':expired}

@app.post('/api/reports/{job_id}/reviews',status_code=201)
def submit_review(job_id:str,req:ReviewRequest):return _submit_review(job_id,req)
@app.get('/api/reports/{job_id}/reviews')
def list_reviews(job_id:str):
    from .reviews import ReviewStore
    store.get(job_id);hashes=_current_hashes(store.get(job_id))
    return {'current_artifact_hashes':hashes,'reviews':[{**r,'valid_for_current_artifacts':(r['docx_sha256'],r['pdf_sha256'])==(hashes['docx'],hashes['pdf'])} for r in ReviewStore().list_for_job(job_id)]}
@app.get('/api/reports/{job_id}/acceptance')
def report_acceptance(job_id:str):
    store.get(job_id)
    return _recalc_acceptance(job_id)
@app.post('/api/reviews/import',status_code=201)
def import_reviews(payload:ReviewImport):
    imported,errors=[],[]
    for index,entry in enumerate(payload.entries):
        try:imported.append({'job_id':entry.job_id,'result':_submit_review(entry.job_id,entry.review)})
        except (ValueError,KeyError) as exc:errors.append({'index':index,'job_id':entry.job_id,'error':str(exc)})
    return {'imported':imported,'errors':errors}
@app.post('/api/imports',status_code=202)
def imports():return {'job_id':store.enqueue('import',{})['id']}
@app.post('/api/kb/build',status_code=202)
def kb_build():return {'job_id':store.enqueue('kb',{})['id']}
@app.get('/api/kb')
def kb():
    from .knowledge import Knowledge
    k=Knowledge()
    return k.status() if hasattr(k,'status') else {'status':'READY','notice':'本地页码证据；查询结果含版本','documents':[]}
@app.post('/api/kb/search')
def kb_search(req:SearchRequest):
    from .knowledge import Knowledge
    params=req.model_dump();month=params.pop('month');params['period']={'start':month,'end':month} if month else None
    return Knowledge().search(**params)
@app.post('/api/actions')
def draft(req:ActionRequest):return actions.draft(store.get_snapshot(req.snapshot_id),req.finding,req.assignee.model_dump(),req.suggestion,req.priority,verification_target=req.verification_target,expected_evidence=req.expected_evidence,responsible_role=req.responsible_role,deadline_basis=req.deadline_basis)
@app.get('/api/actions')
def list_actions():return actions.list()
@app.put('/api/actions/{id}')
def edit_action(id:str,changes:dict):return actions.edit(id,changes)
@app.post('/api/actions/{id}/confirm')
def confirm(id:str,req:ConfirmRequest):return actions.confirm(id,req.payload_hash)
@app.post('/api/actions/{id}/refresh')
def refresh(id:str):return actions.refresh(id)
@app.get('/api/actions/{id}')
def get_action(id:str):return actions.get(id)

if (APP/'frontend/dist').is_dir():app.mount('/',StaticFiles(directory=APP/'frontend/dist',html=True),name='ui')
