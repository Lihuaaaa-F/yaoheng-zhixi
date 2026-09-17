"""Canonical fingerprints used by bootstrap and environment verification."""
from pathlib import Path
import hashlib
APP = Path(__file__).resolve().parents[1]
def frontend_input_hash(app=APP):
    paths = [p for name in ('src','public') for p in (app/'frontend'/name).rglob('*') if p.is_file()]
    paths += [app/'frontend'/name for name in ('package.json','package-lock.json','tsconfig.json','vite.config.ts','index.html') if (app/'frontend'/name).is_file()]
    h=hashlib.sha256()
    for p in sorted(set(paths)):
        h.update(p.relative_to(app).as_posix().encode()); h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest(),len(paths)
def lock_hash(app=APP):
    return hashlib.sha256((app/'frontend/package-lock.json').read_bytes()).hexdigest()
if __name__ == '__main__':
    import sys
    print(lock_hash() if '--lock' in sys.argv else frontend_input_hash()[0])
