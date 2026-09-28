#!/usr/bin/env python3
"""Explicit, small runtime probes. No secrets or business data are emitted."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
if os.environ.get('PHARMA_PYTHON') and Path(os.environ['PHARMA_PYTHON']).resolve()!=Path(sys.executable).resolve():
    raise SystemExit(subprocess.call([os.environ['PHARMA_PYTHON']]+sys.argv))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from pharma.narrative import ModelGateway
import httpx

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='model_probe.json');ap.add_argument('--expected-model');a=ap.parse_args()
    g=ModelGateway();r={'model':g.model,'endpoint':g.base_url,'protocol':g.provider,'credential_present':bool(g.key),'cost':'UNKNOWN','checked_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'official_docs':'https://api-docs.deepseek.com/' if 'deepseek.com' in g.base_url else 'https://docs.z.ai/api-reference/llm/chat-completion','probes':{}}
    if a.expected_model and g.model!=a.expected_model:raise SystemExit('Configured model does not match expected model')
    if '/coding/' in g.base_url:print('注意：主端点为Coding Plan端点（用户2026-09-18授权的暂定回退政策，主端点额度耗尽时自动切换）')
    if not g.key:
        r['status']='BLOCKED';r['reason']='MODEL_KEY_NOT_SET; application account/endpoint and billing must be checked on teammate machine'
        for k in ('text','structured_response','tools','stream','rate_limit','timeout'):r['probes'][k]={'status':'NOT_RUN','reason':'应用凭据缺失'}
    else:
        bodies={
          'text':{'messages':[{'role':'user','content':'只回复：已连接。'}]},
          'structured_response':{'messages':[{'role':'user','content':'只输出JSON对象，键status值ok。'}],'response_format':{'type':'json_object'}},
          'tools':{'messages':[{'role':'user','content':'请调用ping工具，message为ok。'}],'tools':[{'type':'function','function':{'name':'ping','description':'连接测试，不执行外部操作','parameters':{'type':'object','properties':{'message':{'type':'string'}},'required':['message']}}}]},
          'stream':{'messages':[{'role':'user','content':'只回复：ok。'}],'stream':True}}
        for name,body in bodies.items():
            start=time.monotonic()
            try:
                with httpx.Client(timeout=httpx.Timeout(90,connect=15)) as client:
                    res=client.post(g.base_url+'/chat/completions',headers=g._headers(),json={'model':g.model,'max_tokens':4096,'thinking':{'type':'enabled'},'reasoning_effort':'low',**body})
                item={'http_status':res.status_code,'elapsed_seconds':round(time.monotonic()-start,3),'status':'FAIL'}
                if res.status_code==200:
                    if name=='stream':item['status']='PASS' if 'data: [DONE]' in res.text else 'FAIL'
                    else:
                        data=res.json();message=data['choices'][0]['message'];item['returned_model']=data.get('model');item['usage']=data.get('usage');ok=data.get('model')==g.model
                        if name=='structured_response':ok=ok and json.loads(message['content'])=={'status':'ok'}
                        elif name=='tools':ok=ok and bool(message.get('tool_calls'))
                        else:ok=ok and bool(message.get('content'))
                        item['status']='PASS' if ok else 'FAIL'
                if res.status_code==429:r['probes']['rate_limit']={'status':'OBSERVED','http_status':429}
                r['probes'][name]=item
                if res.status_code in (401,403,404,429):break
            except Exception as exc:r['probes'][name]={'status':'FAIL','reason':type(exc).__name__,'elapsed_seconds':round(time.monotonic()-start,3)}
        r['probes'].setdefault('rate_limit',{'status':'NOT_RUN','reason':'未主动施压；真实额度由账号后台核对，429处理另有本地契约测试'})
        r['probes']['timeout']={'status':'PENDING','reason':'真实超时未主动触发；本地transport故障契约另测'}
        r['status']='PASS' if all(r['probes'].get(k,{}).get('status')=='PASS' for k in bodies) else 'PARTIAL'
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
