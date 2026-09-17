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
    from .reports import render_docx,convert_pdf,assess_report
    id=job['id'];result=job['result'];payload=job['input']
    try:
        store.update(id,'VALIDATING',result)
        if job['kind']=='import':
            from .ingestion import ingest
            result['manifest']=ingest();store.update(id,'SUCCEEDED',result);return
        if job['kind']=='kb':
            result['knowledge']=Knowledge().build();store.update(id,'SUCCEEDED' if result['knowledge']['status']=='PASS' else 'DEGRADED',result);return
        versions=payload.get('versions',{})
        from .reports import TEMPLATE,RENDERER_VERSION
        from .narrative import ModelGateway,PROMPT_VERSION,VALIDATOR_VERSION
        from .knowledge import PARSER_VERSION,RETRIEVER_VERSION,EMBEDDING_SHA,terminology_hash
        from .ingestion import ingest
        from .context_services import retrieval_policy_version
        gateway=ModelGateway()
        snapshot=store.get_snapshot(payload['snapshot_id'])
        synthetic=bool(snapshot.get('context_id') and snapshot['context_id']!='pharmaceutical:competition')
        from .industry import resolve_context
        if snapshot.get('context_id') and resolve_context(snapshot['context_id']).model_dump()!=snapshot.get('analysis_context'):raise ValueError('CONTEXT_VERSION_CHANGED_RESUBMIT')
        for key,current in [('renderer',RENDERER_VERSION),('model',gateway.model),('protocol',gateway.provider),('endpoint',gateway.base_url),('prompt',PROMPT_VERSION)]:
            if versions.get(key) and versions[key]!=current:raise ValueError(key.upper()+'_VERSION_CHANGED_RESUBMIT')
        # A legacy job without these bindings cannot reuse partial/completed
        # results under a different validation or knowledge parsing contract.
        for key,current in [('retrieval_policy',retrieval_policy_version(snapshot.get('analysis_context') or {})),('validator',VALIDATOR_VERSION),('parser',PARSER_VERSION),('terminology',terminology_hash()),('retriever',RETRIEVER_VERSION),('embedding',EMBEDDING_SHA)]:
            if versions.get(key)!=current:raise ValueError(key.upper()+'_VERSION_CHANGED_RESUBMIT')
        if not synthetic and versions.get('template') and hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()!=versions['template']:
            raise ValueError('TEMPLATE_VERSION_CHANGED_RESUBMIT')
        # resolve_context above binds source knowledge; retrieval records its
        # separate index/embedding/retriever version in the evidence bundle.
        store.update(id,'COMPUTING',result)
        if 'snapshot' not in result:result['snapshot']=store.get_snapshot(payload['snapshot_id'])
        snapshot=result['snapshot'];snapshot['template_version']=payload.get('versions',{}).get('template','UNKNOWN');store.update(id,'RETRIEVING',result)
        if 'evidence' not in result:
            from .context_services import retrieve
            result['evidence']=retrieve(snapshot,snapshot['product']+' 工序 批次 成本 维修 单耗 核查')
        store.update(id,'GENERATING',result)
        if 'benchmark' not in result:
            if synthetic:
                from .industry import catalog as scoped_catalog,benchmark_reference
                factories=scoped_catalog(snapshot['context_id'])['factories']
                other=next((x for x in factories if x!=snapshot['factory']),None)
                if other:
                    cross_snapshot,result['benchmark']=benchmark_reference(snapshot['context_id'],snapshot['product'],snapshot['month'],snapshot['factory'],other,snapshot['analysis_type'],snapshot['basis'])
                    snapshot['benchmark_context']=cross_snapshot.get('benchmark_context',{})
                    snapshot['metrics'].update({k:v for k,v in cross_snapshot['metrics'].items() if k.startswith('benchmark:')})
                else:result['benchmark']={'status':'UNAVAILABLE','reason':'缺少第二工厂'}
            else:
                if ingest()['snapshot_id']!=snapshot.get('data_version'):raise ValueError('DATA_VERSION_CHANGED_RESUBMIT')
                from .metrics import catalog
                factories=catalog()['factories'];other=next((x for x in factories if x!=snapshot['factory']),None)
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
