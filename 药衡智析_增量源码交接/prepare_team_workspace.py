"""Explicit release/original manifest validation; never verify a dev tree as a release.
An already merged Git clone needs no prepare operation. Private restoration uses
an external source and only original resource prefixes, never old code/runtime.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
ALLOWED=('00_赛题原始资料/','01_数据/00_原始/','02_知识库/00_原始/')
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['workspace','release','originals'],default='workspace')
    p.add_argument('--source',type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--destination',type=Path)
    a=p.parse_args()
    if a.mode=='workspace':print('Git开发工作区无需prepare；使用当前代码与独立原件清单。');return
    if not a.source or not a.manifest:p.error('source and manifest required')
    entries=json.loads(a.manifest.read_text());source=a.source.resolve()
    for rel,expected in entries.items():
        path=(source/rel).resolve()
        if not path.is_relative_to(source):raise ValueError('MANIFEST_PATH_ESCAPE')
        if a.mode=='originals' and not rel.startswith(ALLOWED):raise ValueError('NON_ORIGINAL_IN_MANIFEST:'+rel)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('MANIFEST_MISMATCH:'+rel)
    if a.destination:
        if a.mode!='originals':p.error('Only originals may be restored')
        for rel,expected in entries.items():
            target=a.destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest()==expected:continue
                target=target.with_name(target.name+'.incoming-'+expected[:8])
            shutil.copy2(source/rel,target)
    print('Verified',len(entries),a.mode)
if __name__=='__main__':main()
