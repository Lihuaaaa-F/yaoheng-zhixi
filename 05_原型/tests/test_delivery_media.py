import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('repository_verifier',Path(__file__).resolve().parents[2]/'tools/verify_repository.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_missing_video_cannot_be_declared_complete(tmp_path):
    current={'competition_ready':True,'video':{'status':'PENDING_USER_RECORDING'},'ppt':{'status':'CONDITIONAL_FINAL_STAGE'}}
    assert module.verify_media(current,tmp_path)==['video:必交物尚未交付']
    current['competition_ready']=False
    assert module.verify_media(current,tmp_path)==[]


def test_final_stage_requires_actual_ppt(tmp_path):
    current={'competition_ready':True,'delivery_stage':'final','video':{'status':'DELIVERED','path':'demo.mp4'},'ppt':{'status':'DELIVERED','path':'slides.pptx'}}
    (tmp_path/'demo.mp4').write_bytes(b'delivery fixture')
    assert module.verify_media(current,tmp_path)==['ppt:交付文件缺失']
