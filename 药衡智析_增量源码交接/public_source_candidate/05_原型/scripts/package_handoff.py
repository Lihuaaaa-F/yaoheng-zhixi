"""Export only an audited committed Git tree; never include private local files."""
from pathlib import Path
import argparse,subprocess
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True).strip())
paths=subprocess.check_output(['git','ls-tree','-rz','--name-only','HEAD'],cwd=repo,text=True).split('\0')
for path in paths:
 if any(x in path for x in ('team_internal/','00_赛题原始资料/','01_数据/','02_知识库/','06_评测/','07_交付/','.runtime/')) or path.endswith(('.sqlite3','.pdf','.docx','.zip')):raise SystemExit('Unsafe tracked release path: '+path)
args.output.parent.mkdir(parents=True,exist_ok=True)
subprocess.run(['git','archive','--format=zip','--output',str(args.output.resolve()),'HEAD'],cwd=repo,check=True)
print('Exported committed public source only:',args.output)
