#!/usr/bin/env python3
"""Verify dependency compatibility and real capability, not just importability.

Exit 0 = all pins satisfied and capability probes pass; the JSON report always
prints so bootstrap can distinguish "missing" from "wrong version" from
"imports but cannot do the job"."""
import importlib.util
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]

# import name → (distribution name, capability probe)
PROBES = {
    'fastapi': ('fastapi', None),
    'pydantic': ('pydantic', lambda: __import__('pydantic').TypeAdapter(int).validate_python('42') == 42),
    'uvicorn': ('uvicorn', None),
    'duckdb': ('duckdb', lambda: __import__('duckdb').connect().execute('select 42').fetchone()[0] == 42),
    'chromadb': ('chromadb', None),
    'llama_index.core': ('llama-index-core', None),
    'docx': ('python-docx', None),
    'pymupdf': ('pymupdf', lambda: __import__('pymupdf').Document().is_pdf),
    'httpx': ('httpx', None),
    'pytest': ('pytest', None),
    'jieba': ('jieba', lambda: bool(list(__import__('jieba').cut('成本分析')))),
    'onnxruntime': ('onnxruntime', lambda: bool(__import__('onnxruntime').InferenceSession)),
    'tokenizers': ('tokenizers', None),
    'matplotlib': ('matplotlib', lambda: __import__('matplotlib').use('Agg') or True),
    'multipart': ('python-multipart', None),
}


def lock_pins(path):
    pins = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if '==' in line and not line.startswith('#'):
            name, version = line.split('==', 1)
            pins[name.strip().lower().replace('_', '-')] = version.strip()
    return pins


def main():
    from importlib import metadata
    report = {'python': sys.version.split()[0], 'executable': sys.executable,
              'missing': [], 'incompatible': [], 'capability_failures': [], 'ok': []}
    pins = lock_pins(APP / 'requirements.lock') if (APP / 'requirements.lock').is_file() else {}
    for module, (dist, probe) in PROBES.items():
        try:
            installed = metadata.version(dist)
        except metadata.PackageNotFoundError:
            report['missing'].append({'module': module, 'distribution': dist})
            continue
        entry = {'module': module, 'distribution': dist, 'installed': installed}
        if probe is not None:
            try:
                if importlib.util.find_spec(module) is None:
                    raise ImportError('module not importable')
                if probe() is not True: raise RuntimeError("capability probe returned false")
            except Exception as exc:
                entry['probe_error'] = type(exc).__name__ + ': ' + str(exc)[:120]
                report['capability_failures'].append(entry)
                continue
        pin = pins.get(dist.lower())
        if pin and installed != pin:
            entry['locked'] = pin
            report['incompatible'].append(entry)
            continue
        report['ok'].append(module)
    try:
        import sqlite3
        with sqlite3.connect(':memory:') as db:
            db.execute('CREATE VIRTUAL TABLE fts_probe USING fts5(body)')
            db.execute("INSERT INTO fts_probe VALUES ('synthetic')")
            assert db.execute("SELECT count(*) FROM fts_probe WHERE fts_probe MATCH 'synthetic'").fetchone()[0] == 1
        report['fts5'] = 'PASS'
    except Exception as exc:
        report['capability_failures'].append({'module':'sqlite3.fts5','probe_error':str(exc)})
    report['status'] = 'PASS' if not (report['missing'] or report['incompatible'] or report['capability_failures']) else 'MISSING_OR_INCOMPATIBLE'
    print(json.dumps(report, ensure_ascii=False, indent=1))
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
