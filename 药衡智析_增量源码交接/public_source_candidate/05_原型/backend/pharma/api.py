from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path
import hashlib,json,time,os
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from .config import APP,RUNTIME,ROOT
from .jobs import JobStore
from .actions import ActionStore
from .metrics import analyze,benchmark,benchmark_analysis,catalog

store=JobStore();actions=ActionStore()
app=FastAPI(title='药衡智析',version='0.1.0')
class AnalysisRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    context_id:str|None=None
    factory:str|None=None;product:str|None=None;month:str=Field(default='2026-05',pattern=r'^20\d{2}-(0[1-9]|1[0-2])$')
    analysis_type:Literal['monthly','quarterly','special']='monthly';basis:Literal['unit','total']='unit'
class ReportRequest(AnalysisRequest):
    run_id:str|None=Field(default=None,pattern=r'^[A-Za-z0-9_-]{1,80}$')

class SearchRequest(BaseModel):
    context_id:str|None=None
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
def selected_context(context_id=None):
    from .industry import context_catalog
    return context_id or context_catalog()['default_context_id']

def scoped_analysis(req):
    from .industry import analyze_reference,catalog as scoped_catalog
    cid=selected_context(req.context_id)
    options=scoped_catalog(cid)
    params=req.model_dump(exclude={'context_id','run_id'})
    params['factory']=params['factory'] or options['factories'][0]
    params['product']=params['product'] or options['products'][0]
    return analyze_reference(cid,**params)

@app.get('/api/industry/catalog')
def industry_catalog():
    from .industry import context_catalog
    return context_catalog()

@app.get('/api/catalog')
def get_catalog(context_id:str|None=None):
    from .industry import catalog as scoped_catalog
    return {**scoped_catalog(selected_context(context_id)),'demo_assignee':{'name':'待分配','department':'成本管理部'}}
@app.post('/api/analyses')
def analysis(req:AnalysisRequest):return store.snapshot(scoped_analysis(req))
@app.get('/api/analyses/{id}')
def get_analysis(id:str):return store.get_snapshot(id)
@app.get('/api/benchmarks')
def get_benchmark(product:str,month:str,left:str,right:str,analysis_type:Literal['monthly','quarterly','special']='monthly',basis:Literal['unit','total']='unit',context_id:str|None=None):
    from .knowledge import Knowledge
    from .narrative import generate
    cid=selected_context(context_id)
    if left==right:raise ValueError('COMPARISON_REQUIRES_TWO_FACTORIES')
    if cid=='pharmaceutical:competition':
        snapshot,result=benchmark_analysis(product,month,left,right,analysis_type=analysis_type)
        from .industry import resolve_context
        context=resolve_context(cid)
        snapshot.update(context_id=cid,analysis_context=context.model_dump(),context_hash=context.context_hash)
        from .context_services import retrieve
        retrieved=retrieve(snapshot,product+' 工艺 收率 设备 差异',limit=5)
    else:
        from .industry import benchmark_reference
        snapshot,result=benchmark_reference(cid,product,month,left,right,analysis_type,basis)
        from .context_services import retrieve
        retrieved=retrieve(snapshot,product+' 工序 批次 单耗 核查')
    result['context_id']=cid
    result['snapshot_id']=store.snapshot(snapshot)['snapshot_id']
    # 同一文档同一位置的重复分片只保留首个，避免界面出现重复证据条目
    seen=set();unique=[]
    for e in retrieved.get('evidence',[]):
        key=(e.get('source'),e.get('location') or e.get('page'))
        if key in seen:continue
        seen.add(key);unique.append(e)
    retrieved['evidence']=unique
    result['evidence']=retrieved
    result['narrative']=generate(snapshot,result['evidence'])
    result['hypotheses']=[{**f,'hypothesis':f['rendered_text']} for f in result['narrative']['findings']]
    return result
@app.post('/api/reports',status_code=202)
def report(req:ReportRequest):
    from .reports import TEMPLATE,normalize_template,RENDERER_VERSION
    from .narrative import PROMPT_VERSION,VALIDATOR_VERSION,ModelGateway
    from .knowledge import Knowledge
    snapshot=store.snapshot(scoped_analysis(req))
    if snapshot['context_id']=='pharmaceutical:competition':
        if not TEMPLATE.exists():normalize_template()
        template_version=hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
    else:template_version=snapshot['analysis_context']['template_version']
    gateway=ModelGateway()
    versions={'renderer':RENDERER_VERSION,'snapshot':snapshot['snapshot_id'],'knowledge':snapshot['analysis_context']['knowledge_snapshot'],'template':template_version,'prompt':PROMPT_VERSION,'validator':VALIDATOR_VERSION,'parser':__import__('pharma.knowledge',fromlist=['PARSER_VERSION']).PARSER_VERSION,'terminology':__import__('pharma.knowledge',fromlist=['terminology_hash']).terminology_hash(),'model':gateway.model,'protocol':gateway.provider,'endpoint':gateway.base_url,'context':snapshot['analysis_context'],'model_available':bool(gateway.key),'generation_parameters':{'max_tokens':os.getenv('PHARMA_MODEL_MAX_TOKENS','8192'),'reasoning_effort':os.getenv('PHARMA_MODEL_REASONING_EFFORT','low'),'max_repairs':gateway.max_repairs},'retriever':__import__('pharma.knowledge',fromlist=['RETRIEVER_VERSION']).RETRIEVER_VERSION,'embedding':__import__('pharma.knowledge',fromlist=['EMBEDDING_SHA']).EMBEDDING_SHA,'retrieval_parameters':{'mode':'hybrid','weight_policy':'lexical-anchor:0.75/0.25;otherwise:0.5/0.5','reranker':'none','limit':8},'run_id':req.run_id}
    key=hashlib.sha256(json.dumps(versions,sort_keys=True).encode()).hexdigest()
    from .revision import revision_record
    revision=revision_record(ROOT)
    j=store.enqueue('report',{'snapshot_id':snapshot['snapshot_id'],'context_id':snapshot['context_id'],'versions':versions,'run_id':req.run_id,**revision},key)
    return {'job_id':j['id'],'status':j['status'],'cache_source_time':j['created']}
@app.get('/api/jobs')
def jobs(context_id:str|None=None):return [j for j in store.list() if context_id is None or j['input'].get('context_id')==context_id]
@app.get('/api/jobs/{id}')
def job(id:str):return {**store.get(id),'history':store.history(id)}
@app.get('/api/artifacts/{id}')
def artifact(id:str,preview:bool=False):
    p=store.artifact_path(id,preview=preview)
    if preview:
        return FileResponse(p,filename='草稿预览_未审核_'+id+p.suffix,headers={'X-Artifact-Preview':'draft-unreviewed'})
    return FileResponse(p,filename='药衡智析_'+id+p.suffix)

def _current_hashes(job,strict=False):
    hashes={}
    for fmt in ('docx','pdf'):
        artifact=job.get('result',{}).get(fmt,{})
        aid=artifact.get('artifact_id')
        if not aid:
            hashes[fmt]=None
            continue
        try:
            path=store.artifact_path(aid)
            actual=hashlib.sha256(path.read_bytes()).hexdigest()
            if actual!=artifact.get('sha256'):raise ValueError('ARTIFACT_HASH_MISMATCH')
            hashes[fmt]=actual
        except (ValueError,KeyError):
            if strict:raise
            # A stale artifact has no valid bound version until regenerated.
            hashes[fmt]='STALE'
    return hashes

def _submit_review(job_id,req):
    job=store.get(job_id)
    if job['status'] not in ('SUCCEEDED','DEGRADED'):raise ValueError('REVIEW_TARGET_NOT_FINAL')
    hashes=_current_hashes(job,strict=True)
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
    if 'STALE' in hashes.values():
        acceptance['file_openable']={'status':'FAIL','reason':'产物内容变化，旧审核已过期'}
        acceptance['overall']='FAIL'
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
def kb(context_id:str|None=None):
    cid=selected_context(context_id)
    if cid!='pharmaceutical:competition':
        from .industry import resolve_context,retrieve_reference
        docs=retrieve_reference(resolve_context(cid),'')
        return {'status':'READY','context_id':cid,'documents':docs,'notice':'独立合成知识，非行业基准'}
    from .knowledge import Knowledge
    k=Knowledge()
    return k.status() if hasattr(k,'status') else {'status':'READY','notice':'本地页码证据；查询结果含版本','documents':[]}
@app.post('/api/kb/search')
def kb_search(req:SearchRequest):
    from .knowledge import Knowledge
    params=req.model_dump();cid=selected_context(params.pop('context_id'))
    if cid!='pharmaceutical:competition':
        from .context_services import retrieve
        from .industry import analyze_reference
        return retrieve(analyze_reference(cid,product=req.product,month=req.month),req.query)
    month=params.pop('month');params['period']={'start':month,'end':month} if month else None
    return Knowledge().search(**params)
@app.post('/api/actions')
def draft(req:ActionRequest):return actions.draft(store.get_snapshot(req.snapshot_id),req.finding,req.assignee.model_dump(),req.suggestion,req.priority,verification_target=req.verification_target,expected_evidence=req.expected_evidence,responsible_role=req.responsible_role,deadline_basis=req.deadline_basis)
@app.get('/api/actions')
def list_actions(context_id:str|None=None):return [a for a in actions.list() if context_id is None or a['metadata'].get('context_id')==context_id]
@app.put('/api/actions/{id}')
def edit_action(id:str,changes:dict):return actions.edit(id,changes)
@app.post('/api/actions/{id}/confirm')
def confirm(id:str,req:ConfirmRequest):return actions.confirm(id,req.payload_hash)
@app.post('/api/actions/{id}/refresh')
def refresh(id:str):return actions.refresh(id)
class AcknowledgementRequest(BaseModel):
    confirmed_by:str=Field(min_length=1,max_length=80)
    comment:str=Field(default='',max_length=2000)

@app.post('/api/actions/{id}/acknowledge')
def acknowledge(id:str,req:AcknowledgementRequest):
    return actions.acknowledge(id,req.confirmed_by,req.comment)

@app.get('/api/actions/{id}')
def get_action(id:str):return actions.get(id)

if (APP/'frontend/dist').is_dir():app.mount('/',StaticFiles(directory=APP/'frontend/dist',html=True),name='ui')
