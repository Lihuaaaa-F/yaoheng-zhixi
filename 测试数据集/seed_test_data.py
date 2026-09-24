# -*- coding: utf-8 -*-
"""把测试数据集一键导入运行中的“药衡智析”后端（默认 http://127.0.0.1:8765）。

流程：上传业务数据（含行业参考）→ 知识文档 → 报告模板 → 触发统一解析发布 →
触发知识库构建。全部走公开 API，等价于页面手工操作。

用法：
    python seed_test_data.py                       # 使用默认后端地址
    python seed_test_data.py http://127.0.0.1:9000 # 指定后端地址

注意：解析/建库是后台任务，脚本会轮询到终态；成功后打印 context_id，
可直接在页面分析该测试企业。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import urllib.request
import json

HERE = Path(__file__).resolve().parent
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8765'

BUSINESS_DIR = HERE / '业务数据'
INDUSTRY_DIR = HERE / '行业参考数据'
KNOWLEDGE_DIR = HERE / '知识文档'
TEMPLATE_DIR = HERE / '报告模板'
# 解析发布要求企业内全部业务文件一起校验；成本汇总与预算是分析主键，
# 行业参考为辅助区块数据。一次全传，一次解析。
ORDERED_TYPES = [
    ('成本汇总_2025', 'cost_summary'), ('成本汇总_2026', 'cost_summary'),
    ('原材料消耗明细', 'material_detail'), ('制造费用明细', 'manufacturing_detail'),
    ('人工工时明细', 'labor_detail'), ('预算数据', 'budget'),
    ('行业成本基准', 'industry_reference'),
]


def http_json(path: str, payload: dict | None = None, method: str = 'GET', timeout: int = 60):
    request = urllib.request.Request(BASE + path, method=method)
    body = None
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        request.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(request, body, timeout=timeout) as response:
        return json.load(response)


def upload(kind: str, data_type: str, file: Path):
    boundary = '----YaohengTestSeed'
    content = file.read_bytes()
    body = b''
    for name, value in (('kind', kind), ('data_type', data_type)):
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{file.name}"\r\n'
             'Content-Type: application/octet-stream\r\n\r\n').encode() + content + b'\r\n'
    body += f'--{boundary}--\r\n'.encode()
    request = urllib.request.Request(BASE + '/api/imports/uploads', body, method='POST')
    request.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def wait_job(job_id: str, label: str, timeout_s: int = 900) -> dict:
    start = time.time()
    while time.time() - start < timeout_s:
        job = http_json(f'/api/jobs/{job_id}')
        status = job.get('status')
        detail = str(job.get('detail') or '')[:120]
        print(f'  [{label}] {status} {job.get("progress", "")}% {detail}')
        if status in ('SUCCEEDED', 'DEGRADED', 'FAILED'):
            return job
        time.sleep(3)
    raise SystemExit(f'{label} 超时未完成')


def main() -> None:
    health = http_json('/health')
    print('后端正常：', health.get('service'), health.get('status'))

    # 自适应策略（工作区=单企业本地安装）：
    # 1) 后端尚未绑定企业（全新环境）：整套装入“测试药厂”测试数据集（业务+行业参考+知识+模板）。
    # 2) 后端已绑定其他企业（如“示例药厂（导入）”）：为不破坏既有工作区，
    #    只增量补充 行业参考数据 + 知识文档（同一企业口径继续生效）。
    workspace = http_json('/api/workspace')
    bound = bool(workspace.get('context_id'))
    print('工作区状态：', workspace.get('status'), '· 已绑定：', workspace.get('enterprise_name') or '（无）')

    uploaded: dict[str, str] = {}
    if not bound:
        print('== 全新环境：上传业务数据（含行业参考） ==')
        for keyword, data_type in ORDERED_TYPES:
            search_dir = INDUSTRY_DIR if data_type == 'industry_reference' else BUSINESS_DIR
            matches = sorted(search_dir.glob('测试数据_*.csv'))
            file = next((f for f in matches if keyword.replace('_', '') in f.name.replace('_', '')), None)
            if file is None:
                raise SystemExit(f'找不到业务文件：{keyword}（目录：{search_dir}）')
            saved = upload('business', data_type, file)
            uploaded[data_type] = saved['id']
            print(' ', file.name, '->', saved['id'])
    else:
        print('== 已有企业工作区：仅增量上传行业参考数据 ==')
        matches = sorted(INDUSTRY_DIR.glob('测试数据_*.csv'))
        file = matches[0]
        saved = upload('business', 'industry_reference', file)
        uploaded['industry_reference'] = saved['id']
        print(' ', file.name, '->', saved['id'])
    print('== 上传知识文档 ==')
    knowledge_ids = []
    for file in sorted(KNOWLEDGE_DIR.glob('测试数据_*.txt')):
        saved = upload('knowledge', 'industry' if '行业' in file.name else 'product', file)
        knowledge_ids.append(saved['id'])
        print(' ', file.name, '->', saved['id'])
    print('== 上传报告模板 ==')
    template_ids = []
    for file in sorted(TEMPLATE_DIR.glob('测试数据_*.docx')):
        saved = upload('template', 'monthly', file)
        template_ids.append(saved['id'])
        print(' ', file.name, '->', saved['id'])

    print('== 触发统一解析发布 ==')
    parse = http_json('/api/data/parse', {} if bound else {'enterprise_name': '测试药厂'}, method='POST')
    job = wait_job(parse['job_id'], '解析')
    if job['status'] == 'FAILED':
        raise SystemExit('解析失败：' + str(job.get('error'))[:300])
    context_id = (job.get('result') or {}).get('published', {}).get('context_id', '') or workspace.get('context_id', '')
    print('发布上下文：', context_id)

    if knowledge_ids:
        print('== 触发知识库构建 ==')
        build = http_json('/api/kb/build', {}, method='POST')
        kb_job = wait_job(build['job_id'], '建库')
        print('知识库状态：', (kb_job.get('result') or {}).get('status'))
    print('完成。context_id =', context_id)


if __name__ == '__main__':
    main()
