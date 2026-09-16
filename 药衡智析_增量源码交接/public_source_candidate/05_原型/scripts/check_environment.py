#!/usr/bin/env python3
"""Environment readiness: interpreter resolution, dependency compatibility,
frontend build freshness, fonts and data package presence."""
import hashlib, json, os, platform, shutil, subprocess, sys
from pathlib import Path
APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP/'backend'))

def resolve_python():
    if os.environ.get('PHARMA_PYTHON'): return os.environ['PHARMA_PYTHON']
    for candidate in (APP/'.venv/bin/python', APP/'.venv/Scripts/python.exe'):
        if candidate.exists(): return str(candidate)
    return sys.executable

def frontend_input_hash():
    paths = []
    for pattern in ('frontend/src', 'frontend/public'):
        paths += [p for p in (APP/pattern).rglob('*') if p.is_file()] if (APP/pattern).exists() else []
    for name in ('frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json','frontend/vite.config.ts','frontend/index.html'):
        if (APP/name).exists(): paths.append(APP/name)
    h = hashlib.sha256()
    for p in sorted(paths):
        h.update(str(p.relative_to(APP)).replace('\\','/').encode()); h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest(), len(paths)

def main():
    resolved = resolve_python()
    deps = subprocess.run([resolved, str(APP/'scripts/check_dependencies.py')], capture_output=True, text=True)
    try: deps_report = json.loads(deps.stdout)
    except ValueError: deps_report = {'status': 'DEPS_CHECK_FAILED', 'stderr': deps.stderr[-500:]}
    input_hash, input_count = frontend_input_hash()
    dist = APP/'frontend/dist'
    recorded = (dist/'.build-inputs').read_text().strip() if (dist/'.build-inputs').is_file() else None
    font = shutil.which('fc-match')
    font_result = subprocess.check_output([font,'Noto Sans CJK SC'],text=True).strip() if font else 'NOT_APPLICABLE_ON_THIS_PLATFORM'
    runtime_dir = os.environ.get('PHARMA_RUNTIME_DIR', str(APP/'.runtime'))
    data_package = Path(os.environ.get('PHARMA_DATA_PACKAGE', str(ROOT/'00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据')))
    r = {'python': sys.version.split()[0], 'python_executable': resolved, 'system': platform.platform(),
         'dependency_report': deps_report, 'commands': {k: shutil.which(k) for k in ('node','npm','libreoffice','soffice','pdftoppm')},
         'runtime': runtime_dir, 'data_package_present': data_package.is_dir(),
         'frontend': {'dist_present': (dist/'index.html').is_file(), 'build_inputs_tracked': input_count,
                      'dist_matches_sources': (dist/'index.html').is_file() and recorded == input_hash,
                      'current_input_hash': input_hash[:12], 'dist_input_hash': (recorded or '')[:12]},
         'font': font_result,
         'project_truetype_fonts': all((APP/'assets/fonts'/f).is_file() for f in ('NotoSansSC-Regular.ttf','NotoSansSC-Bold.ttf','OFL.txt')),
         'locks': {k: (APP/k).is_file() for k in ('requirements.lock','frontend/package-lock.json')},
         'note': 'PDF导出在Linux用libreoffice；Windows验收须另行安装LibreOffice/soffice后再测'}
    deps_ok = deps_report.get('status') == 'PASS'
    r['status'] = 'PASS' if deps_ok and r['data_package_present'] and r['frontend']['dist_matches_sources'] else 'MISSING_OR_STALE'
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if '--strict' in sys.argv and r['status'] != 'PASS': raise SystemExit(1)

if __name__ == '__main__':
    main()
