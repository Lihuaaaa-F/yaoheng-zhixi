#!/usr/bin/env python3
"""Download only missing pinned retrieval assets; verify bytes before publication."""
import hashlib,json,os,sys,urllib.request
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP/'backend'))
from pharma.config import RUNTIME
root=APP.parent;manifest=json.loads((root/'docs/embedding_manifest.json').read_text())
external=bool(os.getenv('PHARMA_EMBEDDING_DIR'))
target=Path(os.getenv('PHARMA_EMBEDDING_DIR',str(RUNTIME/'models/bge-small-zh-v1.5')));target.mkdir(parents=True,exist_ok=True)
for name,meta in manifest['files'].items():
 p=target/name
 if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==meta['sha256']:print(name,'verified existing');continue
 if external or '--check-only' in sys.argv:
  raise SystemExit('EMBEDDING_BLOCKED: missing or incompatible asset; external files are never overwritten: '+name)
 remote='onnx/'+name if name.endswith('.onnx') else name
 # 镜像源（PHARMA_EMBEDDING_MIRROR=1）：内容与官方同一哈希校验，仅换分发主机。
 host='https://hf-mirror.com' if os.getenv('PHARMA_EMBEDDING_MIRROR')=='1' else 'https://huggingface.co'
 url=host+'/'+manifest['repo']+'/resolve/'+manifest['revision']+'/'+remote
 temp=p.with_suffix(p.suffix+'.download')
 with urllib.request.urlopen(url,timeout=90) as response,temp.open('wb') as f:
  while block:=response.read(1024*1024):f.write(block)
 if hashlib.sha256(temp.read_bytes()).hexdigest()!=meta['sha256']:raise SystemExit('Asset hash mismatch: '+name)
 temp.replace(p);print(name,'downloaded and verified')
