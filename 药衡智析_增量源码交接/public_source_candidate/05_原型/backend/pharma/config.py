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
# 竞赛上下文的补充知识目录（2026-09-21 修复 #7：行情/基准 CSV 未入 RAG、
# 异常处理记录与对标基线缺失）。仓库自有文件，题包原件保持只读；文件哈希
# 进入知识版本指纹，增删改自动重建索引。行业包（显式 source_files/context）
# 不受影响。
KNOWLEDGE_SUPPLEMENT_DIR = Path(os.environ.get('PHARMA_KNOWLEDGE_SUPPLEMENT_DIR',
    str(ROOT / 'competition_configuration/knowledge_supplement')))
# 中药二厂合成明细目录（2026-09-21 修复 #19，用户授权"构建标注合成明细"）：
# 题包二厂仅有成本汇总；本目录 CSV 由 scripts/generate_synthetic_plant2_details.py
# 按一厂结构比例生成、Decimal 精确校准至二厂汇总（audit 全通过）。文件哈希进入
# 数据快照指纹；置 PHARMA_SYNTHETIC_DETAIL_DIR='' 可完全停用（回到纯题包口径）。
SYNTHETIC_DETAIL_DIR = Path(os.environ.get('PHARMA_SYNTHETIC_DETAIL_DIR',
    str(ROOT / 'competition_configuration/synthetic_detail_中药二厂'))) \
    if os.environ.get('PHARMA_SYNTHETIC_DETAIL_DIR', 'default') != '' else None
SYNTHETIC_DETAIL_FACTORIES = {'中药二厂'} if SYNTHETIC_DETAIL_DIR is not None else set()
DB_PATH = RUNTIME / 'app.sqlite3'
ARTIFACTS = Path(os.environ.get('PHARMA_ARTIFACTS_DIR',str(ROOT / '07_交付/业务报告')))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
RPA_BASE_URL = os.environ.get('RPA_BASE_URL', 'http://127.0.0.1:8090').rstrip('/')
