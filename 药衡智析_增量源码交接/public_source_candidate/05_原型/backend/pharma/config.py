from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / '05_原型'
# Project-scoped configuration, never execute shell fragments from .env.
_env=APP/'.env'
if _env.is_file():
    for line in _env.read_text(encoding='utf-8').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line:continue
        key,value=line.split('=',1);key=key.strip()
        if key.startswith('PHARMA_') or key in ('RPA_BASE_URL','GLM_API_KEY','ZHIPU_API_KEY'):
            os.environ.setdefault(key,value.strip().strip('"').strip("'"))

RUNTIME = Path(os.environ.get('PHARMA_RUNTIME_DIR',str(APP / '.runtime')))
RUNTIME.mkdir(parents=True, exist_ok=True)
PACKAGE = Path(os.environ.get('PHARMA_DATA_PACKAGE',str(ROOT / '00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据')))
DB_PATH = RUNTIME / 'app.sqlite3'
ARTIFACTS = Path(os.environ.get('PHARMA_ARTIFACTS_DIR',str(ROOT / '07_交付/业务报告')))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
RPA_BASE_URL = os.environ.get('RPA_BASE_URL', 'http://127.0.0.1:8090').rstrip('/')
