#!/usr/bin/env python3
import json,sys,hashlib,subprocess,shutil,os
from pathlib import Path
import fitz
if os.environ.get('PHARMA_PYTHON') and Path(os.environ['PHARMA_PYTHON']).resolve()!=Path(sys.executable).resolve():
    raise SystemExit(subprocess.call([os.environ['PHARMA_PYTHON']]+sys.argv))
root=Path(__file__).resolve().parents[2]
manifest=Path(sys.argv[1]) if len(sys.argv)>1 else root/'06_评测/incremental_20260916/scenario_reports.json'
manifest=manifest.resolve()
out=manifest.parent/('pages_delivery' if 'delivery' in manifest.stem else 'pages_release' if 'release' in manifest.stem else 'pages_final' if 'final' in manifest.stem else 'pages');out.mkdir(exist_ok=True)
use_poppler=bool(shutil.which('pdftoppm'))
records=[]
for item in json.loads(manifest.read_text()):
 path=root/'07_交付/业务报告'/item['job_id']/'report.pdf'
 folder=out/item['scenario'];folder.mkdir(exist_ok=True)
 with fitz.open(path) as d:
  for i,page in enumerate(d):
   image=folder/f'page-{i+1:02}.png'
   if use_poppler:
    subprocess.run(['pdftoppm','-f',str(i+1),'-singlefile','-r','120','-png',str(path),str(image.with_suffix(''))],check=True,capture_output=True)
   else:
    page.get_pixmap(dpi=120).save(str(image))
   records.append({'scenario':item['scenario'],'page':i+1,'image':str(image.relative_to(root)),'image_sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'pdf_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'text_length':len(page.get_text()),'renderer':'Poppler pdftoppm' if use_poppler else 'PyMuPDF fallback','visual_agent_review':'PENDING','human_review':'PENDING'})
(out/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2));print('Rendered',len(records),'pages with',('Poppler' if use_poppler else 'PyMuPDF fallback'))
