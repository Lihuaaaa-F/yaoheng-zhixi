#!/usr/bin/env python3
"""Package current effective sources and separated internal evidence, with manifests."""
import hashlib,json,shutil,tempfile,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'07_交付/可运行源码交接包';OUT.mkdir(exist_ok=True)
release=json.loads((ROOT/'06_评测/incremental_20260916/scenario_reports_delivery.json').read_text())
valid_page_images={str((ROOT/x['image']).resolve()) for x in json.loads((ROOT/'06_评测/incremental_20260916/pages_delivery/manifest.json').read_text())}
exclude={'.runtime','.venv','node_modules','__pycache__','.pytest_cache','.agents','.codex','.git','99_隔离区'}
public_dirs=['05_原型/assets','05_原型/backend','05_原型/frontend','05_原型/scripts','docs']
internal_dirs=['00_赛题原始资料','01_数据','02_知识库','03_研究','04_方案与文档','06_评测/incremental_20260916','06_评测/dual_model','06_评测/run_20260917_local','06_评测/run_20260917_glm_live','06_评测/verify_20260917_defect_fixes','06_评测/unpack_receipts','05_原型/tests','90_工具']

def copytree(source,dest):
 for p in source.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(source)
  if any(x in exclude for x in rel.parts) or p.name=='.env' or p.name.endswith(('.pyc','.tsbuildinfo')):continue
  # Keep failure records, not obsolete generated artifacts or layout prototypes.
  if any(x in ('layout_probe','pages','pages_final','pages_release','downloads') for x in rel.parts):continue
  if 'pages_delivery' in rel.parts and p.suffix=='.png' and str(p.resolve()) not in valid_page_images:continue
  q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)

def copyfile(rel,dest):
 p=ROOT/rel;q=dest/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)

with tempfile.TemporaryDirectory(prefix='pharma-package-',dir=None if __import__('os').name=='nt' else '/tmp') as tmp:
 stage=Path(tmp)/'药衡智析_增量源码交接';stage.mkdir()
 public=stage/'public_source_candidate';internal=stage/'team_internal';public.mkdir();internal.mkdir()
 for rel in public_dirs:copytree(ROOT/rel,public/rel)
 for rel in ('README.md','AGENTS.md','CONTEXT.md','05_原型/requirements.txt','05_原型/requirements.lock','05_原型/.env.example'):copyfile(rel,public)
 # Public candidate must not carry raw business data or private audit evidence.
 for p in list((public/'docs').glob('*.json')):
  if p.name not in ('embedding_manifest.json',):p.unlink()
 for rel in internal_dirs:copytree(ROOT/rel,internal/rel)
 for rel in ('07_交付/artifact.json','07_交付/药析证链_制药成本智能分析一等奖方案.html'):copyfile(rel,internal)
 copyfile('06_评测/golden.json',internal)  # tests/test_metrics.py 的独立golden，随包携带
 local_run=json.loads((ROOT/'06_评测/run_20260917_local/scenario_reports.json').read_text())
 for item in local_run:copytree(ROOT/('07_交付/业务报告/'+item['job_id']),internal/('07_交付/业务报告/'+item['job_id']))
 for item in release:
  rel='07_交付/业务报告/'+item['job_id'];copytree(ROOT/rel,internal/rel)
 # Baseline evidence remains evidence; never represent it as executable source.
 baseline=internal/'04_baseline';baseline.mkdir()
 for name in ('scenario_reports.json','verification.json','retrieval_results.json'):
  p=ROOT/'06_评测'/name
  if p.exists():shutil.copy2(p,baseline/name)
 # The original machine's first-run scenario_reports.json was never packaged;
 # the delivered manifest carries the same S2 job whose artifacts exist here.
 original=json.loads((ROOT/'06_评测/incremental_20260916/scenario_reports_delivery.json').read_text())
 s2=next((x for x in original if x.get('scenario')=='S2'),None)
 if s2:
  for name in ('record.json','report.docx','report.pdf'):
   p=ROOT/'07_交付/业务报告'/s2['job_id']/name
   if p.exists():shutil.copy2(p,baseline/('S2_'+name))
 (baseline/'README.md').write_text('本目录是原S2失败与旧评测证据，不是可运行源码。原件未改名为GLM运行。完整恢复基线在原工作机pharma_recovery_baselines目录。\n')
 # Embed the safe merge script (verified manifest, missing-only copy, conflict
 # side-copies); the historical overwrite version must never ship again.
 (stage/'prepare_team_workspace.py').write_text((ROOT/'90_工具'/'prepare_team_workspace_safe.py').read_text(encoding='utf-8'))
 (stage/'README.md').write_text('''# 药衡智析增量源码交接

1. public_source_candidate 是公开源码**候选**；未发布，不含题包/报告/知识原文。公开前还需队内审查授权。
2. team_internal 仅供参赛队内部，含原题包、知识、工作模板、当前样例和真实证据；不得公开。
3. 在包根目录运行 `python3 prepare_team_workspace.py`，然后进入public_source_candidate。合并后的工作副本含内部资料。
4. 读 `docs/ZCODE_HANDOFF.md`，运行 `bash 05_原型/scripts/bootstrap.sh` 与 `bash 05_原型/scripts/start.sh`。
5. 包不含密钥、个人配置、venv、node_modules、缓存与旧版生成产物。检索模型按固定manifest下载或显式外置复用。
6. GLM应用实调缺凭据，真人归因/可读性/版式待评。文件生成成功不代表报告验收成功。
7. 当前验证证据位于team_internal/06_评测/incremental_20260916；历史失败证据在04_baseline及本轮history日志，不可覆盖。
''')
 files={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
 # The baseline must actually pin the immutable originals (merged into the
 # working copy by prepare_team_workspace.py), not just source files.
 baseline_map={str(p.relative_to(public)):hashlib.sha256(p.read_bytes()).hexdigest() for p in public.rglob('*') if p.is_file()}
 for originals in ('00_赛题原始资料','01_数据/00_原始','02_知识库/00_原始'):
  for p in (ROOT/originals).rglob('*'):
   if p.is_file():baseline_map[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 (public/'docs/baseline.json').write_text(json.dumps(baseline_map,ensure_ascii=False,indent=2))
 files={str(p.relative_to(stage)):hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.rglob('*') if p.is_file()}
 (stage/'SHA256.json').write_text(json.dumps(files,ensure_ascii=False,indent=2))
 archive=OUT/'药衡智析_可运行源码交接包.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in stage.rglob('*'):
   if p.is_file():z.write(p,arcname=str(Path(stage.name)/p.relative_to(stage)))
 candidate=OUT/'药衡智析_公开源码候选包.zip'
 with zipfile.ZipFile(candidate,'w',zipfile.ZIP_DEFLATED) as z:
  for p in public.rglob('*'):
   if p.is_file():z.write(p,arcname=str(Path('public_source_candidate')/p.relative_to(public)))
 result={'status':'PACKAGED_NOT_ACCEPTED','files':len(files),'archives':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (archive,candidate)},'excluded':['credentials','personal_configuration','venv','node_modules','runtime_cache','obsolete_outputs'],'runtime_acceptance':'see unpack_acceptance.json'}
 (OUT/'package_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
