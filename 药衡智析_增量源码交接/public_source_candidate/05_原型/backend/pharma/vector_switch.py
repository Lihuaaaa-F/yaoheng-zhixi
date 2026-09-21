"""向量模型切换：本地脚本校验 + 数据分析模型 API 适配评估 + 知识库重建。

合同（模型配置 · 向量模型子项）：
- 成功 → “向量模型切换成功”，随后知识检索即用新模型；
- 失败 → “向量模型切换失败，（数据分析模型API返回的切换失败原因）”；脚本层
  失败（路径不存在、资产缺失、样本编码失败、重建失败）按对应步骤报错。

向量模型仅支持本地推理（CPU ONNX，Xenova/transformers.js 布局：
model_quantized.onnx + tokenizer.json）。数据分析模型在切换中承担“适配评估”：
读取脚本探得的模型元数据（文件、维度、样本编码），返回 JSON 结论
{adaptable, dimension, pooling, normalize, query_prefix, reason}——程序再按结论
完成指纹登记与知识库重建；模型说不可适配即失败，程序不硬切。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from . import model_settings


class SwitchFailure(Exception):
    def __init__(self, step: str, reason: str):
        super().__init__(f'{step}报错：{reason}')
        self.step = step
        self.reason = reason


def _probe_local(path: Path) -> dict[str, Any]:
    """本地脚本校验：目录资产 + 样本编码，返回模型元数据（供分析模型评估）。"""
    if not path.is_dir():
        raise SwitchFailure('本地校验', f'路径不存在或不是目录：{path}')
    files = {name: (path / name).is_file() for name in
             ('model_quantized.onnx', 'model.onnx', 'onnx/model_quantized.onnx',
              'tokenizer.json', 'config.json', 'special_tokens_map.json')}
    has_onnx = files.get('model_quantized.onnx') or files.get('model.onnx') or files.get('onnx/model_quantized.onnx')
    if not has_onnx:
        raise SwitchFailure('本地校验',
                            '缺少 ONNX 模型文件（需 model_quantized.onnx 或 model.onnx；'
                            '本系统使用 CPU ONNX 推理，不加载 PyTorch 权重）')
    if not files.get('tokenizer.json'):
        raise SwitchFailure('本地校验', '缺少 tokenizer.json（需 Xenova/transformers.js 布局的分词器文件）')
    config: dict[str, Any] = {}
    if files.get('config.json'):
        try:
            config = json.loads((path / 'config.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            config = {}
    # 样本编码：真实加载模型跑两条文本，取维度与有限性
    try:
        from .knowledge import CpuEmbedding
        embedding = CpuEmbedding(path)
        vectors = embedding.encode(['产品成本分析', '药材价格行情'], query=False)
        dimension = len(vectors[0]) if vectors else None
        finite = all(isinstance(x, float) for row in vectors for x in row)
    except Exception as exc:  # noqa: BLE001
        raise SwitchFailure('本地校验', f'样本编码失败：{type(exc).__name__}: {str(exc)[:180]}')
    if not dimension or not finite:
        raise SwitchFailure('本地校验', '样本编码结果为空或含非有限值')
    return {'path': str(path), 'name': path.name, 'files': files,
            'declared_hidden_size': config.get('hidden_size'), 'architectures': config.get('architectures'),
            'model_type': config.get('model_type'), 'probe_dimension': dimension,
            'fingerprint': model_settings.embedding_fingerprint(path)}


def _model_adaptation(probe: dict[str, Any]) -> dict[str, Any]:
    """数据分析模型 API 适配评估；不可适配时抛出携带 API 原因的失败。"""
    from .narrative import ModelGateway
    gateway = ModelGateway.for_route('analysis')
    if not gateway.key:
        raise SwitchFailure('数据分析模型API', '未配置数据分析模型，无法完成向量模型适配评估'
                                             '（请先在“模型配置·数据分析模型”完成配置）')
    system = ('你是向量检索模型的适配评估器。输入是本地向量模型（CPU ONNX）的探测元数据。'
              '判断它能否作为中文语义检索嵌入模型服务本制药成本分析系统。'
              '只返回JSON对象 {"adaptable": bool, "dimension": int, "pooling": str, '
              '"normalize": bool, "query_prefix": str, "reason": str}。'
              'reason 用一句中文说明；不可适配时 reason 必须给出具体原因。')
    user = json.dumps(probe, ensure_ascii=False)
    try:
        raw, _usage, _identity = gateway.complete(system, user, operation='vector_switch')
        from .import_pipeline import _parse_json_object
        data = _parse_json_object(raw)
    except Exception as exc:  # noqa: BLE001
        raise SwitchFailure('数据分析模型API', f'评估调用失败：{type(exc).__name__}: {str(exc)[:200]}')
    if not data.get('adaptable'):
        reason = str(data.get('reason') or '模型评估未给出原因')[:300]
        raise SwitchFailure('数据分析模型API', f'API返回不可适配：{reason}')
    return {'dimension': data.get('dimension') or probe['probe_dimension'],
            'pooling': str(data.get('pooling') or 'cls')[:40],
            'normalize': bool(data.get('normalize', True)),
            'query_prefix': str(data.get('query_prefix') or '为这个句子生成表示以用于检索相关文章：')[:80],
            'api_reason': str(data.get('reason') or '')[:200], 'model': gateway.model}


def run_vector_switch(store, job):
    job_id = job['id']; result = job['result']; payload = job['input']
    raw_path = str(payload.get('path') or '').strip()

    def step(pct, detail):
        store.update(job_id, 'VECTOR_SWITCH', result, progress=pct, detail=detail)

    previous = model_settings._load().get('vector_model', {})
    try:
        step(5, '本地脚本校验：模型资产与样本编码…')
        probe = _probe_local(Path(raw_path))
        step(25, f'本地校验通过：{probe["name"]}（探测维度 {probe["probe_dimension"]}），'
                 f'调用数据分析模型评估适配…')
        adaptation = _model_adaptation(probe)
        step(45, f'适配评估通过（{adaptation["api_reason"] or "API评估可适配"}），'
                 f'写入配置并重建知识索引…')
        if os.environ.get('PHARMA_EMBEDDING_DIR', '').strip():
            raise SwitchFailure('配置写入', '环境变量 PHARMA_EMBEDDING_DIR 已显式指定向量模型目录'
                                             '且优先级高于页面设置；请清除该环境变量后重试')
        model_settings.set_vector_model(raw_path)
        from .knowledge import Knowledge
        knowledge = Knowledge()

        def build_progress(pct, detail):
            step(45 + 45 * pct / 100, detail)

        build_result = knowledge.build(progress=build_progress)
        if build_result.get('status') == 'FAILED':
            raise SwitchFailure('知识库重建', '知识库构建失败：'
                              + '；'.join(str(f.get('reason', f)) for f in (build_result.get('failures') or [])[:3]))
        step(93, '验证新模型语义检索…')
        search = knowledge.search('产品成本 分析', mode='vector', limit=3)
        if search.get('status') == 'FAILED':
            raise SwitchFailure('检索验证', str(search.get('reason') or '向量检索返回失败')[:200])
        result['vector_model'] = model_settings.vector_status()
        result['adaptation'] = adaptation
        result['knowledge'] = {k: build_result.get(k) for k in ('status', 'knowledge_version', 'chunks', 'vector_error')}
        result['message'] = '向量模型切换成功'
        result['message_detail'] = (f'已切换至 {probe["name"]}（维度 {adaptation["dimension"]}），'
                                    f'知识索引已重建（{build_result.get("chunks", 0)} 段）并通过语义检索验证。'
                                    + ('注意：向量索引降级（' + str(build_result.get('vector_error')) + '）' if build_result.get('vector_error') else ''))
        store.update(job_id, 'SUCCEEDED' if not build_result.get('vector_error') else 'DEGRADED', result,
                     progress=100, detail='向量模型切换成功')
    except SwitchFailure as exc:
        # 回滚配置：写回前值，避免半切换状态
        try:
            if previous:
                model_settings.set_vector_model(str(previous.get('path') or ''))
            else:
                model_settings.clear_vector_model()
        except Exception:
            pass
        message = f'向量模型切换失败，{exc.step}报错：{exc.reason}'
        store.update(job_id, 'FAILED', result, error=message, detail=message)
    except Exception as exc:  # noqa: BLE001
        message = f'向量模型切换失败，{type(exc).__name__}报错：{str(exc)[:300]}'
        store.update(job_id, 'FAILED', result, error=message, detail=message)
        import traceback
        traceback.print_exc()
