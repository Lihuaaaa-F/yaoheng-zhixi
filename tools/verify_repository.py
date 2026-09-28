"""核验正式交付入口、人工记录和样本关联，不替代业务验收。"""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parents[1]
def verify_media(current, root):
    errors=[]
    stage=current.get('delivery_stage','preliminary')
    for kind, required in (('video',True),('ppt',stage=='final')):
        item=current.get(kind)
        if not isinstance(item,dict):
            errors.append(kind+':须记录真实状态、路径和适用阶段');continue
        status=item.get('status');relative=item.get('path')
        if status=='DELIVERED':
            if not relative or not (root/relative).is_file():errors.append(kind+':交付文件缺失')
        elif required and current.get('competition_ready'):
            errors.append(kind+':必交物尚未交付')
        elif status not in ('MISSING','PENDING_USER_RECORDING','CONDITIONAL_FINAL_STAGE'):
            errors.append(kind+':状态无效')
        if required and status=='CONDITIONAL_FINAL_STAGE':errors.append(kind+':当前阶段不能记为条件项')
    return errors


def verify():
    errors=[];docs=ROOT/'docs'
    current=json.loads((docs/'current_run.json').read_text())
    record=json.loads((docs/current['human_review_record']).read_text())
    rows=[r for r in record['records'] if r['scenario'] in current['required_scenarios']]
    if {r['scenario'] for r in rows}!=set(current['required_scenarios']):errors.append('必测场景不完整')
    for row in rows:
        score=row.get('attribution_score')
        if type(score) is not int or not 0<=score<=5 or not row.get('reviewer'):errors.append('人工评价字段不完整')
        for fmt,relative in row['files'].items():
            file=docs/'evaluation'/relative
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=row['hashes'][fmt]:errors.append('评测样本不匹配:'+relative)
    errors.extend(verify_media(current,ROOT))
    if current.get('competition_ready') and current['status']!='PASS':errors.append('未完成验证不能声称全部交付通过')
    paths=[ROOT/'README.md',ROOT/'CONTRIBUTING.md',docs/'技术方案.md',docs/'环境与部署.md',docs/'evaluation_report.md',docs/'forecast/README.md']
    for document in paths:
        content=re.sub(r'```.*?```','',document.read_text(),flags=re.S)
        for link in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)',content):
            target=urlsplit(link)
            if target.scheme or target.netloc or not target.path:continue
            if not (document.parent/unquote(target.path)).exists():errors.append(f'{document.name}:断链:{link}')
    return errors
if __name__=='__main__':
    try:errors=verify()
    except (OSError,KeyError,ValueError,TypeError) as e:errors=[str(e)]
    print(json.dumps({'status':'FAIL' if errors else 'PASS','scope':'交付导航与评测关联','errors':errors},ensure_ascii=False,indent=2))
    raise SystemExit(bool(errors))
