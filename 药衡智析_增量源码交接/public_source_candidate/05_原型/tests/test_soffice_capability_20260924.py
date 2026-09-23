"""pdf_service 能力探测合同（2026-09-24）：探测必须与转换器实际可用性一致。

原缺陷：capabilities 用 shutil.which('libreoffice')，Windows 安装的二进制是
soffice.exe 且通常不在 PATH——转换器（convert_pdf 会探测 Program Files）明明可用，
能力预览却永远 degraded。
"""
import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from pharma import api, reports

APP = Path(api.APP)
client = TestClient(api.app)


def _soffice_installed_independently() -> bool:
    """独立事实源：不经过被测代码，直接看文件系统与 PATH。"""
    if shutil.which('libreoffice') or shutil.which('soffice'):
        return True
    for base in (os.environ.get('PROGRAMFILES', r'C:\Program Files'),
                 os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')):
        if (Path(base) / 'LibreOffice' / 'program' / 'soffice.exe').exists():
            return True
    return False


def test_pdf_export_capability_matches_real_converter():
    installed = _soffice_installed_independently()
    cat = client.get('/api/industry/catalog').json()
    # 空数据环境（CI 冷缓存）首个上下文可能是赛题上下文（capabilities 为空）
    # ——取第一个含能力清单的上下文；均无则本测试不适用。
    with_caps = [c for c in cat['contexts'] if c.get('capabilities')]
    if not with_caps:
        import pytest; pytest.skip('当前环境无带能力清单的数据上下文')
    pdf = [c for c in with_caps[0]['capabilities'] if c['id'] == 'pdf_export'][0]
    assert (pdf['status'] == 'available') == installed, \
        f'soffice 实际安装={installed}，能力预览却报 {pdf["status"]}（{pdf["reason"]}）'


def test_convert_pdf_probe_finds_the_same_binary():
    exe = reports.soffice_exe()
    if _soffice_installed_independently():
        assert exe and Path(exe).exists()
    else:
        assert exe is None
