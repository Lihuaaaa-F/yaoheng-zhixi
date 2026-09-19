from contextlib import asynccontextmanager
from typing import Literal
from pathlib import Path
import hashlib,json,time,os
from fastapi import FastAPI,HTTPException,Request,Query
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from .config import APP,RUNTIME,ROOT
from .jobs import JobStore
from .actions import ActionStore
from .metrics import benchmark_analysis

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
    from .config import RPA_BASE_URL
    from .local_validation import require_loopback
    simulation=os.getenv('PHARMA_RPA_SIMULATION')=='1'
    try:require_loopback(RPA_BASE_URL)
    except ValueError:simulation=False
    return {'rpa_mode':'local_simulator' if simulation else 'unverified','rpa_base_url':RPA_BASE_URL,'status':'ok','service':'药衡智析','worker':{'alive':age is not None and age<180,'heartbeat_age_seconds':age},'simulation':simulation}
def selected_context(context_id=None):
    from .industry import context_catalog
    return context_id or context_catalog()['default_context_id']

def scoped_analysis(req):
    from .industry import analyze_reference, catalog as scoped_catalog
    cid=selected_context(req.context_id)
    options=scoped_catalog(cid)
    params=req.model_dump(exclude={'context_id','run_id'})
    params['factory']=params['factory'] or options['factories'][0]
    params['product']=params['product'] or options['products'][0]
    return analyze_reference(cid,**params)

def resolved_analysis(context_id,factory,product,month,analysis_type='monthly',basis='unit'):
    """GET 型端点的选择解析：缺省值取当前上下文目录，与 POST 口径一致。"""
    from .industry import analyze_reference, catalog as scoped_catalog
    cid=selected_context(context_id)
    options=scoped_catalog(cid)
    return analyze_reference(cid,factory=factory or options['factories'][0],product=product or options['products'][0],
        month=month or options['months'][-1],analysis_type=analysis_type,basis=basis)

@app.get('/api/industry/catalog')
def industry_catalog():
    from .industry import context_catalog
    return context_catalog()

@app.get('/api/catalog')
def get_catalog(context_id:str|None=None):
    from .industry import catalog as scoped_catalog
    return {**scoped_catalog(selected_context(context_id)),'demo_assignee':{'name':'待分配','department':'成本管理部'}}
@app.post('/api/analyses')
def analysis(req:AnalysisRequest):
    from .dashboard import focus_analysis
    snapshot=store.snapshot(scoped_analysis(req))
    enabled=os.getenv('PHARMA_AUTO_EXPLAIN','false').lower() in ('1','true','yes')
    available=False
    if enabled:
        from .narrative import ModelGateway
        available=bool(ModelGateway().key)
    focus=focus_analysis(snapshot,enabled=enabled,model_available=available,
        latest_job=store.latest_report_for_snapshot(snapshot['snapshot_id']) if enabled else None,
        enqueue=lambda:_enqueue_report(ReportRequest(**req.model_dump()))[0])
    return {**snapshot,'focus':focus}

@app.get('/api/dashboard/heatmap')
def dashboard_heatmap(context_id:str|None=None,factory:str|None=None,
    month:str=Query(pattern=r'^20\d{2}-(0[1-9]|1[0-2])$'),basis:Literal['unit','total']='unit'):
    from .dashboard import product_month_grid
    from .industry import catalog as scoped_catalog
    cid=selected_context(context_id)
    options=scoped_catalog(cid)
    return product_month_grid(cid,factory or options['factories'][0],month,basis,options=options)
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
def _generation_versions(snapshot,req):
    """报告生成输入指纹：任何影响产物的组件版本变化都会使缓存失效。"""
    from .reports import TEMPLATE,normalize_template,RENDERER_VERSION
    from .narrative import PROMPT_VERSION,VALIDATOR_VERSION,ModelGateway
    from .context_services import retrieval_policy_version
    from .knowledge import PARSER_VERSION,RETRIEVER_VERSION,EMBEDDING_SHA,terminology_hash
    if snapshot['context_id']=='pharmaceutical:competition':
        if not TEMPLATE.exists():normalize_template()
        template_version=hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()
    else:template_version=snapshot['analysis_context']['template_version']
    gateway=ModelGateway()
    return {'retrieval_policy':retrieval_policy_version(snapshot['analysis_context']),'renderer':RENDERER_VERSION,
        'snapshot':snapshot['snapshot_id'],'knowledge':snapshot['analysis_context']['knowledge_snapshot'],
        'template':template_version,'prompt':PROMPT_VERSION,'validator':VALIDATOR_VERSION,
        'parser':PARSER_VERSION,'terminology':terminology_hash(),'model':gateway.model,'protocol':gateway.provider,
        'endpoint':gateway.base_url,'context':snapshot['analysis_context'],'model_available':bool(gateway.key),
        'generation_parameters':{'max_tokens':os.getenv('PHARMA_MODEL_MAX_TOKENS','8192'),
            'reasoning_effort':os.getenv('PHARMA_MODEL_REASONING_EFFORT','low'),'max_repairs':gateway.max_repairs},
        'retriever':RETRIEVER_VERSION,'embedding':EMBEDDING_SHA,
        'retrieval_parameters':{'mode':'hybrid','weight_policy':'lexical-anchor:0.75/0.25;otherwise:0.5/0.5','reranker':'none','limit':8},
        'run_id':req.run_id}

def _enqueue_report(req:ReportRequest):
    """报告任务入队：POST /api/reports 与 Agent 决策执行共用同一路径。"""
    snapshot=store.snapshot(scoped_analysis(req))
    versions=_generation_versions(snapshot,req)
    key=hashlib.sha256(json.dumps(versions,sort_keys=True).encode()).hexdigest()
    from .revision import revision_record
    revision=revision_record(ROOT)
    j=store.enqueue('report',{'snapshot_id':snapshot['snapshot_id'],'context_id':snapshot['context_id'],
        'factory':snapshot.get('factory'),'product':snapshot.get('product'),'month':snapshot.get('month'),
        'analysis_type':snapshot.get('analysis_type'),'basis':snapshot.get('basis'),
        'versions':versions,'run_id':req.run_id,**revision},key)
    return j,snapshot

@app.post('/api/reports',status_code=202)
def report(req:ReportRequest):
    j,_=_enqueue_report(req)
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
    result['human_review_status']='PENDING' if not review else ('PASS' if all(acceptance[k]['status']=='PASS' for k in ('section_completeness','readability','visual_quality')) else 'FAIL')
    result['execution_status']='COMPLETED'
    result['capability_status']='PASS' if all(v.get('status')=='PASS' for k,v in acceptance.items() if isinstance(v,dict) and k not in ('section_completeness','readability','visual_quality')) else 'DEGRADED'
    status='SUCCEEDED' if acceptance['overall']=='PASS' else 'DEGRADED'
    result['acceptance_review_binding']={'review_id':review['id'] if review else None,'artifact_hashes':hashes}
    with store.db() as c:c.execute('UPDATE jobs SET status=?,stage=?,result=? WHERE id=?',(status,status,json.dumps(result,ensure_ascii=False),job_id))
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

# ---- 赛题加分项端点：成本预测 / Agent自主决策 / 知识图谱 / 多模型路由 ----

# GET 型端点的月份参数与 POST 合同同校验
def _month_query():
    return Query(default=None, pattern=r'^20\d{2}-(0[1-9]|1[0-2])$')

@app.get('/api/forecast')
def forecast(context_id:str|None=None,factory:str|None=None,product:str|None=None,month:str|None=_month_query(),
             analysis_type:Literal['monthly','quarterly','special']='monthly',basis:Literal['unit','total']='unit',
             horizon:int=3):
    """成本预测：对当前口径快照的趋势序列做 Holt 外推，附实验性波动范围。"""
    from .forecasting import forecast_snapshot
    snapshot=store.snapshot(resolved_analysis(context_id,factory,product,month,analysis_type,basis))
    return forecast_snapshot(snapshot,horizon=horizon)

@app.get('/api/agent/decision')
def agent_decision(context_id:str|None=None,factory:str|None=None,product:str|None=None,month:str|None=_month_query(),
                   analysis_type:Literal['monthly','quarterly','special']='monthly',basis:Literal['unit','total']='unit',
                   with_advisory:bool=False):
    """Agent 自主决策：确定性判断“生成报告/仅更新看板”。

    with_advisory 默认关闭（GET 不应默认消耗模型预算）；前端展示说明时显式开启。
    """
    from .decision import evaluate,advise,DecisionStore
    snapshot=store.snapshot(resolved_analysis(context_id,factory,product,month,analysis_type,basis))
    evaluation=evaluate(snapshot,store.list_reports())
    if with_advisory:evaluation=advise(evaluation,snapshot)
    decision_id=DecisionStore().append(evaluation)
    return {'decision_id':decision_id,**evaluation}

@app.post('/api/agent/decision/{decision_id}/apply')
def apply_decision(decision_id:int):
    """按决策执行：REPORT_NEEDED 时入队报告任务并回写台账；重复应用幂等拒绝。"""
    from .decision import DecisionStore
    ledger=DecisionStore()
    record=ledger.get(decision_id)
    if not record:raise KeyError('DECISION_NOT_FOUND')
    if record['decision']!='REPORT_NEEDED':raise ValueError('DECISION_NOT_REPORT_NEEDED')
    if record['applied_job_id']:raise ValueError('DECISION_ALREADY_APPLIED:'+record['applied_job_id'])
    selection=json.loads(record['selection'])
    j,_=_enqueue_report(ReportRequest(**selection))
    ledger.bind_job(decision_id,j['id'])
    return {'job_id':j['id'],'status':j['status'],'cache_source_time':j['created']}

@app.get('/api/kb/graph')
def kb_graph(context_id:str|None=None):
    """知识图谱：产品-药材-工序结构与来源，供检索增强与前端可视化。"""
    from .industry import resolve_context
    from .graph import graph_for_context
    cid=selected_context(context_id)
    context=resolve_context(cid).model_dump()
    graph=graph_for_context(context).load()
    return {**graph,'context_id':cid}

@app.get('/api/model/routes')
def model_routes():
    """多模型协作路由状态：各任务路由的实际模型与回退情况。"""
    from .narrative import ModelGateway
    return ModelGateway.routes_status()

if (APP/'frontend/dist').is_dir():app.mount('/',StaticFiles(directory=APP/'frontend/dist',html=True),name='ui')
