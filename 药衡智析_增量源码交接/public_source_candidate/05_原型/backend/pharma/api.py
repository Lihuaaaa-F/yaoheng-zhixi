from contextlib import asynccontextmanager
from typing import Any, Literal
from pathlib import Path
import hashlib,json,time,os
from fastapi import FastAPI,File,Form,HTTPException,Request,Query,UploadFile
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from .config import APP,RUNTIME,ROOT
from .jobs import JobStore
from .actions import ActionStore
from .metrics import benchmark_analysis

store=JobStore();actions=ActionStore()
app=FastAPI(title='药衡智析',version='0.1.0')
# 可选 API 鉴权（2026-09-21 修复 #4）：默认（本地演示，端口仅绑 127.0.0.1）
# 不设置 token、行为不变；部署到局域网/公网时设置 PHARMA_API_TOKEN 环境变量，
# 所有 /api/* 请求须携带 X-API-Token 头。/health 与静态页面豁免。
@app.middleware('http')
async def optional_token_guard(request,call_next):
    token=os.getenv('PHARMA_API_TOKEN','').strip()
    if token and (request.url.path.startswith('/api') or request.url.path in ('/docs','/redoc','/openapi.json')):
        import secrets
        provided=request.headers.get('x-api-token','')
        if not secrets.compare_digest(provided.encode('utf-8'),token.encode('utf-8')):
            return JSONResponse(status_code=401,content={'error':{'code':'UNAUTHORIZED','message':'缺少或错误的 X-API-Token'},'status':'FAILED'})
    return await call_next(request)
class AnalysisRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    context_id:str|None=None
    factory:str|None=None;product:str|None=None;month:str=Field(default='2026-05',pattern=r'^20\d{2}-(0[1-9]|1[0-2])$')
    analysis_type:Literal['monthly','quarterly','special']='monthly';basis:Literal['unit','total']='unit'
class ReportRequest(AnalysisRequest):
    run_id:str|None=Field(default=None,pattern=r'^[A-Za-z0-9_-]{1,80}$')
    retry:bool=False  # 对 DEGRADED 报告明确重试：旧任务保留，新任务复用可用计算结果

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
    params=req.model_dump(exclude={'context_id','run_id','retry'})
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
    # 赛题 5.2.3：要素环比严格超过±10%自动生成重点分析段落——默认开启自动
    # 模型解释（2026-09-22 起；入队按版本指纹幂等，重复浏览不重复计费）。
    # 未配置模型时自动降级为确定性变化说明，不发起调用。置
    # PHARMA_AUTO_EXPLAIN=0 可关闭。
    enabled=os.getenv('PHARMA_AUTO_EXPLAIN','true').lower() in ('1','true','yes')
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
    """报告生成输入指纹：任何影响产物的组件版本变化都会使缓存失效。

    版本键清单单一来源 versions.py（修复 #21）：本函数与 worker 的重提交
    校验从同一组 soft/hard 清单派生，新增键不再双份维护。
    """
    from .reports import TEMPLATE,normalize_template,working_template
    from .narrative import ModelGateway
    from .versions import soft_items,hard_items
    if snapshot['context_id']=='pharmaceutical:competition':
        template_file,_map=working_template(snapshot.get('analysis_type','monthly'))
        if template_file==TEMPLATE and not TEMPLATE.exists():normalize_template()
        template_version=hashlib.sha256(template_file.read_bytes()).hexdigest()
    else:template_version=snapshot['analysis_context']['template_version']
    gateway=ModelGateway.for_route('analysis')  # 与 generate() 实际网关同源（fix4）
    versions={**dict(soft_items(gateway)),**dict(hard_items(snapshot)),
        'snapshot':snapshot['snapshot_id'],'knowledge':snapshot['analysis_context']['knowledge_snapshot'],
        'template':template_version,'context':snapshot['analysis_context'],'model_available':bool(gateway.key),
        'generation_parameters':{'max_tokens':os.getenv('PHARMA_MODEL_MAX_TOKENS','8192'),
            'reasoning_effort':os.getenv('PHARMA_MODEL_REASONING_EFFORT','low'),'max_repairs':gateway.max_repairs},
        'retrieval_parameters':{'mode':'hybrid','weight_policy':'lexical-anchor:0.75/0.25;otherwise:0.5/0.5','reranker':'none','limit':8},
        'run_id':req.run_id}
    return versions

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
        'versions':versions,'run_id':req.run_id,**revision},key,retry=bool(getattr(req,'retry',False)))
    return j,snapshot

@app.post('/api/reports',status_code=202)
def report(req:ReportRequest):
    j,_=_enqueue_report(req)
    return {'job_id':j['id'],'status':j['status'],'cache_source_time':j['created']}
@app.get('/api/jobs')
def jobs(context_id:str|None=None,limit:int=Query(default=100,ge=1,le=500),offset:int=Query(default=0,ge=0)):
    # 范围过滤在 SQL 内先于分页执行，避免企业历史任务被全局截断后过滤丢失（fix7）。
    return store.list_jobs(context_id=context_id,limit=limit,offset=offset)
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

# ---- 数据中心 v2：类型化上传、原始预览、解析流水线（进度经 /api/jobs/{id} 轮询） ----
def _reject_active_parse(kind:str):
    for existing in store.list_jobs(limit=60):
        if existing['kind']==kind and existing['status'] in ('QUEUED','RUNNING'):
            raise ValueError(f'PARSE_ALREADY_RUNNING:{existing["id"]}')

class DataParseRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    enterprise_name:str=Field(default='',max_length=80)
    quantity_unit:str=Field(default='',max_length=12)
class VectorSwitchRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    path:str=Field(min_length=2,max_length=400)

@app.post('/api/data/parse',status_code=202)
def data_parse(req:DataParseRequest):
    """解析数据：全部待解析业务文件进入一条流水线（预处理→映射→质检→归因→发布）。"""
    from . import data_import
    waiting=data_import.waiting_imports('business')
    if not waiting:raise ValueError('NO_WAITING_BUSINESS_IMPORTS')
    _reject_active_parse('data_parse')
    j=store.enqueue('data_parse',{'import_ids':[r['id'] for r in waiting],**req.model_dump()})
    for record in waiting:data_import.mark_import_status(record,'PARSING',{'parse_job':j['id']})
    return {'job_id':j['id'],'status':j['status'],'import_count':len(waiting)}

@app.post('/api/kb/build',status_code=202)
def kb_build():
    """构建知识索引：解析全部待解析知识文档并入向量知识库全流程。"""
    from . import data_import
    waiting=data_import.waiting_imports('knowledge')
    _reject_active_parse('kb')
    j=store.enqueue('kb',{'import_ids':[r['id'] for r in waiting],'rebuild':True})
    for record in waiting:data_import.mark_import_status(record,'PARSING',{'parse_job':j['id']})
    return {'job_id':j['id'],'status':j['status'],'import_count':len(waiting)}

@app.post('/api/templates/parse',status_code=202)
def template_parse():
    """解析报告模板：全部待解析模板经结构检查/语义绑定分析后安装。"""
    from . import data_import
    waiting=data_import.waiting_imports('template')
    if not waiting:raise ValueError('NO_WAITING_TEMPLATE_IMPORTS')
    _reject_active_parse('template_parse')
    j=store.enqueue('template_parse',{'import_ids':[r['id'] for r in waiting]})
    for record in waiting:data_import.mark_import_status(record,'PARSING',{'parse_job':j['id']})
    return {'job_id':j['id'],'status':j['status'],'import_count':len(waiting)}

@app.get('/api/templates')
def templates():
    from .reports import installed_templates
    return {'templates':installed_templates()}

# ---- 数据中心：用户自助接入（上传→预览→映射→质检→能力预览→发布） ----
class ImportMappingRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    mapping:dict[str,str]={};save_as:str=Field(default='',max_length=60)
class ImportValidateRequest(ImportMappingRequest):
    options:dict[str,Any]={}
class ImportPublishRequest(ImportValidateRequest):
    enterprise_name:str=Field(default='',max_length=80);pack_id:str=Field(default='',max_length=40)
    quantity_unit:str=Field(default='件',max_length=12)
class KnowledgePublishRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    options:dict[str,Any]={}

@app.post('/api/imports/uploads',status_code=201)
async def import_upload(kind:str=Form(...),data_type:str=Form(''),file:UploadFile=File(...)):
    from . import data_import
    payload=await file.read()
    return data_import.create_upload(kind,file.filename or 'upload.bin',payload,data_type)
@app.get('/api/imports/{import_id}/preview')
def import_preview(import_id:str):
    """预览上传的原始文件（表格/文本/内嵌PDF），只读无副作用。"""
    from . import data_import
    return data_import.preview_original(data_import.get_import(import_id))
@app.get('/api/imports/{import_id}/file')
def import_file(import_id:str):
    from . import data_import
    path=data_import.original_path(data_import.get_import(import_id))
    return FileResponse(path,filename=data_import.get_import(import_id)['filename'],
                        headers={'Content-Disposition':f'inline; filename="{path.name}"'})
@app.get('/api/imports')
def import_list(kind:str|None=None):
    from . import data_import
    return data_import.list_imports(kind)
@app.get('/api/imports/{import_id}')
def import_detail(import_id:str):
    from . import data_import
    return data_import.get_import(import_id)
@app.post('/api/imports/{import_id}/mapping')
def import_mapping(import_id:str,req:ImportMappingRequest):
    from . import data_import
    record=data_import.get_import(import_id)
    if req.save_as:
        headers=record['meta'].get('preview',{}).get('headers') or []
        if not headers:raise ValueError('MAPPING_REQUIRES_TABLE_PREVIEW')
        data_import.save_mapping(headers,req.mapping,req.save_as)
    return {'saved':bool(req.save_as),'suggested':data_import.suggest_mapping(headers) if req.save_as else None}
@app.post('/api/imports/{import_id}/validate')
def import_validate(import_id:str,req:ImportValidateRequest):
    from . import data_import
    record=data_import.get_import(import_id)
    if record['kind']!='business':raise ValueError('VALIDATE_REQUIRES_BUSINESS_IMPORT')
    result=data_import.validate_business(record,req.mapping,req.options)
    from . import data_import as di
    return di._save(record,{**record['meta'],'last_validation':result})
@app.post('/api/imports/{import_id}/publish',status_code=201)
def import_publish(import_id:str,req:ImportPublishRequest):
    from . import data_import
    record=data_import.get_import(import_id)
    if record['kind']=='business':
        result=data_import.publish_business(record,req.mapping,req.options,req.enterprise_name,req.pack_id,req.quantity_unit)
    elif record['kind']=='knowledge':
        result=data_import.publish_knowledge(record,req.options)
    else:
        raise ValueError('TEMPLATE_USES_CHECK_ENDPOINT')
    return data_import._save(record,{**record['meta'],'published':result})
@app.post('/api/imports/{import_id}/template-check')
def import_template_check(import_id:str):
    from . import data_import
    record=data_import.get_import(import_id)
    if record['kind']!='template':raise ValueError('TEMPLATE_CHECK_REQUIRES_TEMPLATE_IMPORT')
    return data_import.check_template(record)
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
        # 用户选择的工厂与检索模式必须贯穿请求、检索与结果（fix2）：
        # 工厂进入分析快照（适用性过滤据此生效），mode 传入检索执行。
        snapshot=analyze_reference(cid,factory=req.factory,product=req.product,month=req.month)
        result=retrieve(snapshot,req.query,mode=req.mode)
        result['requested_scope']={'factory':snapshot.get('factory'),'product':snapshot.get('product'),'mode':req.mode}
        return result
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
    evaluation=evaluate(snapshot,store.list_reports(),artifact_health=store.artifacts_healthy)
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

# ---- 系统设置：模型连接（API 与后台任务读同一份配置；密钥不回显） ----
class ModelSettingsPayload(BaseModel):
    model_config=ConfigDict(extra='forbid')
    connections:dict[str,dict[str,Any]]

@app.get('/api/settings/models')
def get_model_settings():
    from . import model_settings
    return model_settings.status()
@app.put('/api/settings/models')
def put_model_settings(req:ModelSettingsPayload):
    from . import model_settings
    return model_settings.save_settings(req.model_dump())
@app.post('/api/settings/models/test')
def test_model_settings(route:str='analysis',overrides:dict[str,Any]|None=None):
    from . import model_settings
    return model_settings.test_connection(route,overrides)
@app.get('/api/settings/models/list')
def list_model_settings(route:str='analysis',base_url:str|None=None,key_file:str|None=None):
    from . import model_settings
    overrides={'base_url':base_url,'key_file':key_file} if (base_url or key_file) else None
    return model_settings.list_remote_models(route,overrides)

@app.get('/api/settings/models/presets')
def model_presets():
    """厂商预填充：API/本地厂商清单、模型档位与角色限制规则（前端关联选项数据源）。"""
    from .model_registry import presets_payload
    return presets_payload()

@app.get('/api/settings/vector-model')
def vector_model_status():
    from . import model_settings
    return model_settings.vector_status()

@app.post('/api/settings/vector-model/switch',status_code=202)
def vector_model_switch(req:VectorSwitchRequest):
    """向量模型切换：脚本校验+数据分析模型适配评估+知识库重建（进度任务）。"""
    _reject_active_parse('vector_switch')
    j=store.enqueue('vector_switch',{'path':req.path})
    return {'job_id':j['id'],'status':j['status']}

if (APP/'frontend/dist').is_dir():app.mount('/',StaticFiles(directory=APP/'frontend/dist',html=True),name='ui')
