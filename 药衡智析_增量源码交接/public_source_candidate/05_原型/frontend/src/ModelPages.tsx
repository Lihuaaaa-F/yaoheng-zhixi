import { useEffect, useState } from 'react';
import { api } from './api';
import ModelConfigForm from './ModelConfigForm';
import JobProgress from './JobProgress';

export function ExtractionModel() {
  return <div>
    <ModelConfigForm route="extraction" />
    <p className="muted" style={{ padding: '0 4px' }}>数据提取模型用于：业务数据字段映射建议、知识/模板解析辅助等轻量任务（赛题加分项“多模型协作：数据提取用小模型”）。未配置时导入流程确定性回退（预设映射），不阻塞使用。</p>
  </div>;
}

export function AnalysisModel() {
  return <div>
    <ModelConfigForm route="analysis" />
    <p className="muted" style={{ padding: '0 4px' }}>数据分析模型用于：报告分析文本、看板归因、对标拆原因、整改任务生成、导入归因推测与向量模型适配评估（赛题基础项“大模型”）。未配置时报告降级为规则化解释。</p>
  </div>;
}

/** 向量模型：仅本地（无 API 选项）；默认填充当前本地向量模型信息；手动输入
 * 本地路径后点“确认”，由脚本+数据分析模型完成适配与知识库重建。 */
export function VectorModel() {
  const [info, setInfo] = useState<any>(null);
  const [path, setPath] = useState('');
  const [jobId, setJobId] = useState('');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const load = () => api('/settings/vector-model').then(x => { setInfo(x); if (!path) setPath(x.path ?? ''); })
    .catch(e => setError(e instanceof Error ? e.message : String(e)));
  useEffect(() => { void load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);
  const confirm = async () => {
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await api('/settings/vector-model/switch', { path });
      setJobId(response.job_id);
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  return <section className="panel vector-model">
    <h2>向量模型（仅本地）</h2>
    <p className="muted">向量模型用于知识库语义检索（本地 CPU ONNX 推理），不提供任何 API 选项。默认填充当前使用模型的目录与资产信息；输入新的本地模型目录后点击“确认”，系统将执行：本地脚本校验（资产与样本编码）→ 数据分析模型 API 适配评估 → 知识库重建 → 语义检索验证。</p>
    {error && <div className="error" role="alert">{error}</div>}
    {info && <div className="vector-status">
      <dl className="task-details">
        <dt>当前模型</dt><dd>{info.name}{info.is_default ? '（内置默认）' : ''}</dd>
        <dt>模型目录</dt><dd>{info.path}</dd>
        <dt>资产状态</dt><dd>ONNX {info.onnx_present ? '✓' : '缺失'} · 分词器 {info.tokenizer_present ? '✓' : '缺失'}{info.dimension ? ` · 维度 ${info.dimension}` : ''}</dd>
        <dt>资产指纹</dt><dd>{String(info.fingerprint ?? '').slice(0, 16)}…（进入知识版本，切换自动重建）</dd>
      </dl>
    </div>}
    <div className="filters" style={{ marginTop: 12 }}>
      <label className="grow">本地模型目录（Xenova/transformers.js 布局：model_quantized.onnx + tokenizer.json）
        <input aria-label="本地模型目录" value={path} onChange={e => setPath(e.target.value)} placeholder="D:\\models\\bge-small-zh-v1.5" /></label>
      <button className="primary" disabled={busy || !path.trim() || !!jobId} onClick={confirm}>{busy ? '提交中…' : '确认'}</button>
    </div>
    {jobId && <JobProgress jobId={jobId} label="向量模型切换" onDone={job => {
      setResult(job); setJobId(''); void load();
    }} />}
    {result && (result.status === 'FAILED'
      ? <div className="error" role="alert">{result.error}</div>
      : <div className="notice" role="status"><strong>{result.result?.message ?? '向量模型切换成功'}</strong>{result.result?.message_detail ? <> · {result.result.message_detail}</> : null}</div>)}
  </section>;
}
