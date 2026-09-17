"""Archive identity must never discover a surrounding user's Git repository."""
from pathlib import Path
import subprocess
from pharma import revision


def archive(tmp_path):
    root=tmp_path/'archive';backend=root/'05_原型/backend/pharma';backend.mkdir(parents=True)
    (backend/'sample.py').write_text('VALUE = 1\n')
    return root


def test_source_revision_ignores_parent_git_private_data_and_runtime(tmp_path,monkeypatch):
    root=archive(tmp_path);(tmp_path/'.git').mkdir()
    def no_git(*args,**kwargs):raise AssertionError('must not search parent Git')
    monkeypatch.setattr(subprocess,'check_output',no_git)
    first=revision.revision_record(root)
    assert first['revision'].startswith('source:') and first['commit'] is None and first['revision_kind']=='source'
    for name in ['05_原型/.env','05_原型/.runtime/data.json','00_赛题原始资料/secret.json','07_交付/业务报告/report.docx','05_原型/frontend/dist/bundle.js']:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('PRIVATE_NOT_SOURCE')
    secret=root/'05_原型/.env';leak=root/'05_原型/backend/pharma/leak.py'
    # Windows 普通权限无法创建符号链接；无法构造该攻击面时跳过对应断言，
    # 其余“私有数据不入指纹”的验证在任何平台都必须成立。
    try:leak.symlink_to(secret)
    except (OSError,NotImplementedError):leak=None
    banned=('.env','secret.json','report.docx','bundle.js')+(( 'leak.py',) if leak else ())
    original=Path.read_bytes
    def public_only(path):
        assert path.name not in banned
        return original(path)
    monkeypatch.setattr(Path,'read_bytes',public_only)
    assert revision.revision_record(root)==first
    (root/'05_原型/backend/pharma/sample.py').write_text('VALUE = 2\n')
    assert revision.code_revision(root)!=first['revision']


def test_explicit_git_root_returns_git_revision(tmp_path):
    root=archive(tmp_path)
    subprocess.run(['git','init',str(root)],check=True,capture_output=True)
    subprocess.run(['git','-C',str(root),'add','05_原型/backend/pharma/sample.py'],check=True)
    subprocess.run(['git','-C',str(root),'-c','user.name=Synthetic','-c','user.email=synthetic@example.invalid','commit','-m','synthetic'],check=True,capture_output=True)
    value=revision.revision_record(root)
    assert value['revision_kind']=='git' and len(value['commit'])==40 and value['revision']==value['commit']
