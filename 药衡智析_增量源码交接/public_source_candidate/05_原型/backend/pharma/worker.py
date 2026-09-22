from pathlib import Path
import json,os,time,traceback,hashlib
from .config import RUNTIME,ARTIFACTS
from .jobs import JobStore
from .actions import ActionStore
from .locks import try_exclusive

def process_job(store,job):
    from .metrics import benchmark,benchmark_analysis
    from .knowledge import Knowledge
    from .narrative import generate
    from .reports import render_docx,convert_pdf,assess_report,working_template
    id=job['id'];result=job['result'];payload=job['input']
    try:
        store.update(id,'VALIDATING',result)
        if job['kind']=='import':
            from .ingestion import ingest
            result['manifest']=ingest();store.update(id,'SUCCEEDED',result);return
        if job['kind']=='kb':
            from .import_pipeline import run_kb_build
            run_kb_build(store,job);return
        if job['kind']=='data_parse':
            from .import_pipeline import run_data_parse
            run_data_parse(store,job);return
        if job['kind']=='template_parse':
            from .import_pipeline import run_template_parse
            run_template_parse(store,job);return
        if job['kind']=='vector_switch':
            from .vector_switch import run_vector_switch
            run_vector_switch(store,job);return
        versions=payload.get('versions',{})
        from .reports import TEMPLATE
        from .narrative import ModelGateway
        from .versions import soft_items,hard_items
        from .ingestion import ingest
        gateway=ModelGateway.for_route('analysis')  # 版本核对与 generate() 实际网关同源（fix4）
        snapshot=store.get_snapshot(payload['snapshot_id'])
        synthetic=bool(snapshot.get('context_id') and snapshot['context_id']!='pharmaceutical:competition')
        from .industry import resolve_context
        if snapshot.get('context_id') and resolve_context(snapshot['context_id']).model_dump()!=snapshot.get('analysis_context'):raise ValueError('CONTEXT_VERSION_CHANGED_RESUBMIT')
        # 版本键清单单一来源 versions.py（修复 #21）：软项缺省容忍、变化拒收；
        # 硬项缺失即拒收，旧任务不能在异合同下复用结果。
        for key,current in soft_items(gateway):
            if versions.get(key) and versions[key]!=current:raise ValueError(key.upper()+'_VERSION_CHANGED_RESUBMIT')
        for key,current in hard_items(snapshot):
            if versions.get(key)!=current:raise ValueError(key.upper()+'_VERSION_CHANGED_RESUBMIT')
        if not synthetic and versions.get('template') and hashlib.sha256(working_template(snapshot.get('analysis_type','monthly'))[0].read_bytes()).hexdigest()!=versions['template']:
            raise ValueError('TEMPLATE_VERSION_CHANGED_RESUBMIT')
        # resolve_context above binds source knowledge; retrieval records its
        # separate index/embedding/retriever version in the evidence bundle.
        store.update(id,'COMPUTING',result)
        if 'snapshot' not in result:result['snapshot']=store.get_snapshot(payload['snapshot_id'])
        snapshot=result['snapshot'];snapshot['template_version']=payload.get('versions',{}).get('template','UNKNOWN');store.update(id,'RETRIEVING',result)
        if 'evidence' not in result:
            # 知识源幂等校验（2026-09-21 修复）：build() 内部按源文件指纹判断，
            # 源未变化时秒级返回；补充知识目录增删改后报告链路自动纳入新版本，
            # 不再依赖手动触发构建（实测旧版本会在检索侧静默沿用）。
            Knowledge().build()
            from .context_services import retrieve
            result['evidence']=retrieve(snapshot,snapshot['product']+' 工序 批次 成本 维修 单耗 核查')
        store.update(id,'GENERATING',result)
        if 'benchmark' not in result:
            if synthetic:
                from .industry import catalog as scoped_catalog,benchmark_reference
                factories=scoped_catalog(snapshot['context_id'])['factories']
                from .metrics import benchmark_partner
                other=benchmark_partner(snapshot['factory'], snapshot['product'])
                if other not in factories: other=next((x for x in factories if x!=snapshot['factory']),None)
                if other:
                    cross_snapshot,result['benchmark']=benchmark_reference(snapshot['context_id'],snapshot['product'],snapshot['month'],snapshot['factory'],other,snapshot['analysis_type'],snapshot['basis'])
                    snapshot['benchmark_context']=cross_snapshot.get('benchmark_context',{})
                    snapshot['metrics'].update({k:v for k,v in cross_snapshot['metrics'].items() if k.startswith('benchmark:')})
                else:result['benchmark']={'status':'UNAVAILABLE','reason':'缺少第二工厂'}
            else:
                if ingest()['snapshot_id']!=snapshot.get('data_version'):raise ValueError('DATA_VERSION_CHANGED_RESUBMIT')
                from .metrics import catalog,benchmark_partner
                factories=catalog()['factories'];other=benchmark_partner(snapshot['factory'], snapshot['product'])
                if other:
                    cross_snapshot,result['benchmark']=benchmark_analysis(snapshot['product'],snapshot['month'],snapshot['factory'],other,analysis_type=snapshot['analysis_type'])
                    snapshot['benchmark_context']=cross_snapshot['benchmark_context']
                    snapshot['metrics'].update({k:v for k,v in cross_snapshot['metrics'].items() if k.startswith('benchmark:')})
                else:result['benchmark']={'status':'UNAVAILABLE','reason':'缺少第二工厂'}
        if 'narrative' not in result:result['narrative']=generate(snapshot,result['evidence'])
        store.update(id,'RENDERING_DOCX',result)
        folder=ARTIFACTS/id;folder.mkdir(parents=True,exist_ok=True)
        output=folder/'report.docx'
        if 'benchmark' not in result:
            if ingest()['snapshot_id']!=snapshot.get('data_version'):raise ValueError('DATA_VERSION_CHANGED_RESUBMIT')
            result['benchmark']=benchmark(snapshot['product'],snapshot['month'],analysis_type=snapshot['analysis_type'])
        if 'docx' not in result:
            docx=render_docx(snapshot,result['narrative'],result['evidence'],output,result['benchmark'])
            result['docx']=store.artifact(id,docx,'docx')
        store.update(id,'CONVERTING_PDF',result)
        if 'pdf' not in result:
            pdf=convert_pdf(output)
            result['pdf']=store.artifact(id,pdf,'pdf') if pdf['status']=='PASS' else pdf
        # PDF export refreshes the DOCX table of contents; register the final bytes.
        result['docx']=store.artifact(id,{**result['docx'],'path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},'docx')
        audit=folder/'machine_audit.json'
        if audit.exists():result['audit']=store.artifact(id,{'status':'PASS','scope':'machine_audit','path':str(audit),'sha256':hashlib.sha256(audit.read_bytes()).hexdigest()},'json')
        store.update(id,'VERIFYING',result)
        result['acceptance']=assess_report(result)
        result['execution_status']='COMPLETED'
        result['generation_mode']=result['narrative'].get('generation_mode','rules')
        result['human_review_status']='PENDING'
        result['capability_status']='PASS' if all(v.get('status')=='PASS' for k,v in result['acceptance'].items() if isinstance(v,dict) and k not in ('section_completeness','readability','visual_quality')) else 'DEGRADED'
        complete=result['acceptance']['overall']=='PASS'
        result['input_versions']={'data':snapshot.get('data_version'),'formula':snapshot['formula_version'],'knowledge':result['evidence'].get('knowledge_version'),'model':result['narrative'].get('model'),'prompt':result['narrative'].get('prompt_version')}
        tmp=folder/'record.tmp.json';tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));tmp.replace(folder/'record.json')
        store.update(id,'SUCCEEDED' if complete else 'DEGRADED',result)
    except Exception as exc:
        store.update(id,'FAILED',result,type(exc).__name__+': '+str(exc)[:700])
        # Exceptions never contain credentials: gateways redact at their boundary.
        traceback.print_exc()

def dispatch_loop(stop):
    """Outbox and heartbeat remain responsive while report/model work blocks."""
    actions=ActionStore()
    while not stop.is_set():
        (RUNTIME/'worker.heartbeat').write_text(str(time.time()))
        for item in actions.pending():
            try:actions.deliver_one(item['action_id'])
            except Exception as exc:
                actions._state(item['action_id'],'DELIVERY_UNKNOWN',error='worker:'+type(exc).__name__)
                traceback.print_exc()
        stop.wait(.5)

def main():
    from threading import Event,Thread
    lock=try_exclusive(RUNTIME/'worker.lock')
    if lock is None:raise SystemExit('已有本项目worker')
    stop=Event();dispatcher=Thread(target=dispatch_loop,args=(stop,),daemon=True);dispatcher.start()
    store=JobStore()
    try:
        while True:
            job=store.next()
            if job:process_job(store,job)
            else:time.sleep(.5)
    finally:
        stop.set();dispatcher.join(timeout=12)

if __name__=='__main__':main()
