"""Explicit Git checkout identity, or a public-source-only archive fingerprint."""
from pathlib import Path
import hashlib
import os
import subprocess


def _trusted_git_root(project_root):
    if (project_root/'.git').exists():
        return project_root
    # This is the repository's documented layout, not a search through HOME.
    if (project_root.name=='public_source_candidate'
            and project_root.parent.name=='药衡智析_增量源码交接'
            and (project_root.parent.parent/'.git').exists()):
        return project_root.parent.parent
    return None


def source_files(project_root):
    app=project_root/'05_原型'
    def plain_path(p):
        return not any(part.is_symlink() for part in (p,*p.parents) if part.is_relative_to(project_root))
    trees={app/'backend':{'.py'},app/'industry_packs':{'.py','.json'},
           app/'scripts':{'.py','.sh'},app/'frontend/src':{'.ts','.tsx','.js','.jsx','.css','.json','.svg'}}
    for tree,suffixes in trees.items():
        if not tree.is_dir() or not plain_path(tree):continue
        for folder,dirs,files in os.walk(tree,followlinks=False):
            dirs[:]=sorted(d for d in dirs if not d.startswith('.') and d not in ('__pycache__','node_modules','dist','runtime','private') and not (Path(folder)/d).is_symlink())
            for name in sorted(files):
                p=Path(folder)/name
                if not name.startswith('.') and p.suffix in suffixes and not p.is_symlink():yield p
    for name in ('requirements.txt','requirements.lock','requirements-docs.lock',
                 'frontend/package.json','frontend/package-lock.json','frontend/index.html','frontend/vite.config.ts','frontend/tsconfig.json'):
        p=app/name
        if p.is_file() and plain_path(p):yield p


def code_revision(project_root):
    project_root=Path(project_root).resolve()
    git_root=_trusted_git_root(project_root)
    if git_root is not None:
        # Only invoke Git at a verified local .git marker (directory or worktree
        # gitfile), with inherited discovery overrides removed.
        env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
        return subprocess.check_output(['git','-C',str(git_root),'rev-parse','--verify','HEAD'],cwd=git_root,env=env,text=True).strip()
    digest=hashlib.sha256()
    for p in sorted(source_files(project_root)):
        digest.update(p.relative_to(project_root).as_posix().encode());digest.update(b'\0')
        digest.update(hashlib.sha256(p.read_bytes()).digest())
    return 'source:'+digest.hexdigest()


def revision_record(project_root):
    revision=code_revision(project_root)
    kind='source' if revision.startswith('source:') else 'git'
    return {'revision':revision,'revision_kind':kind,'commit':revision if kind=='git' else None}
