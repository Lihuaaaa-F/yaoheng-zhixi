from pathlib import Path
import json,os,time,traceback,hashlib
from .config import RUNTIME,ARTIFACTS
from .jobs import JobStore
from .actions import ActionStore
from .locks import try_exclusive

def process_job(store,job):
    from .metrics import analyze,benchmark,benchmark_analysis
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
        from .narrative import ModelGateway,PROMPT_VERSION
        from .ingestion import ingest
        gateway=ModelGateway()
        for key,current in [('renderer',RENDERER_VERSION),('model',gateway.model),('protocol',gateway.provider),('endpoint',gateway.base_url),('prompt',PROMPT_VERSION)]:
            if versions.get(key) and versions[key]!=current:raise ValueError(key.upper()+'_VERSION_CHANGED_RESUBMIT')
        if versions.get('template') and hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()!=versions['template']:
            raise ValueError('TEMPLATE_VERSION_CHANGED_RESUBMIT')
        if versions.get('knowledge') and Knowledge().version!=versions['knowledge']:
            raise ValueError('KNOWLEDGE_VERSION_CHANGED_RESUBMIT')
        store.update(id,'COMPUTING',result)
        if 'snapshot' not in result:result['snapshot']=store.get_snapshot(payload['snapshot_id'])
        snapshot=result['snapshot'];snapshot['template_version']=payload.get('versions',{}).get('template','UNKNOWN');store.update(id,'RETRIEVING',result)
        if 'evidence' not in result:
            query=snapshot['product']+' 提取收率 单耗 工艺参数'
            if snapshot['product']=='六味地黄胶囊':query='胶囊填充机 维修 停机'
            result['evidence']=Knowledge().search(query,product=snapshot['product'],limit=5,factory=snapshot['factory'],period=snapshot['period'],specification=snapshot.get('specification'))
        store.update(id,'GENERATING',result)
        if 'benchmark' not in result:
            if ingest()['snapshot_id']!=snapshot.get('data_version'):raise ValueError('DATA_VERSION_CHANGED_RESUBMIT')
            cross_snapshot,result['benchmark']=benchmark_analysis(snapshot['product'],snapshot['month'],analysis_type=snapshot['analysis_type'])
            snapshot['benchmark_context']=cross_snapshot['benchmark_context']
            snapshot['metrics'].update({k:v for k,v in cross_snapshot['metrics'].items() if k.startswith('benchmark:')})
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
        complete=result['acceptance']['overall']=='PASS'
        result['input_versions']={'data':snapshot.get('data_version'),'formula':snapshot['formula_version'],'knowledge':result['evidence'].get('knowledge_version'),'model':result['narrative'].get('model'),'prompt':result['narrative'].get('prompt_version')}
        tmp=folder/'record.tmp.json';tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2));tmp.replace(folder/'record.json')
        store.update(id,'SUCCEEDED' if complete else 'DEGRADED',result)
    except Exception as exc:
        store.update(id,'FAILED',result,type(exc).__name__+': '+str(exc)[:700])
        # Exceptions never contain credentials: gateways redact at their boundary.
        traceback.print_exc()

def main():
    lock=try_exclusive(RUNTIME/'worker.lock')
    if lock is None:raise SystemExit('已有本项目worker')
    store=JobStore();actions=ActionStore()
    while True:
        (RUNTIME/'worker.heartbeat').write_text(str(time.time()))
        for item in actions.pending():
            try:actions.deliver_one(item['action_id'])
            except Exception as exc:
                actions._state(item['action_id'],'DELIVERY_UNKNOWN',error='worker:'+type(exc).__name__)
                traceback.print_exc()
        job=store.next()
        if job:process_job(store,job)
        else:time.sleep(.5)

if __name__=='__main__':main()
