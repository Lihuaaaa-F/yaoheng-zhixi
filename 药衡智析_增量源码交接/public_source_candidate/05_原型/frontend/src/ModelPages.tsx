import { useEffect, useState } from 'react';
import { api } from './api';
import ModelConfigForm from './ModelConfigForm';
import JobProgress from './JobProgress';

export function ExtractionModel() {
  return <div>
    <ModelConfigForm route="extraction" />
    <p className="muted" style={{ padding: '0 4px' }}>辅助字段映射；未配置时使用规则。发布前请核对字段与单位。</p>
  </div>;
}

export function AnalysisModel() {
  return <div>
    <ModelConfigForm route="analysis" />
    <p className="muted" style={{ padding: '0 4px' }}>用于成本归因与报告分析；未配置时使用规则解释。</p>
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
    <p className="muted">用于本地语义检索。切换前验证模型，完成后重建知识索引。</p>
    {error && <div className="error" role="alert">{error}</div>}
    {info && <div className="vector-status">
      <dl className="task-details">
        <dt>当前模型</dt><dd>{info.name}{info.is_default ? '（内置默认）' : ''}</dd>
        <dt>模型目录</dt><dd title={info.path}>{String(info.path ?? '').split(/[\\/]/).filter(Boolean).at(-1) ?? info.path}{info.is_default ? '' : ''}</dd>
        <dt>资产状态</dt><dd>ONNX {info.onnx_present ? '✓' : '缺失'} · 分词器 {info.tokenizer_present ? '✓' : '缺失'}{info.dimension ? ` · 维度 ${info.dimension}` : ''}</dd>
      </dl>
    </div>}
    <div className="filters" style={{ marginTop: 12 }}>
      <label className="grow">本地模型目录
        <input aria-label="本地模型目录" value={path} onChange={e => setPath(e.target.value)} placeholder="D:\models\bge-small-zh-v1.5" /></label>
      <button className="primary" disabled={busy || !path.trim() || !!jobId} onClick={confirm}>{busy ? '提交中…' : '确认'}</button>
    </div>
    <p className="muted">目录需包含 ONNX 模型和 tokenizer.json。</p>
    {jobId && <JobProgress jobId={jobId} label="向量模型切换" onDone={job => {
      setResult(job); setJobId(''); void load();
    }} />}
    {result && (result.status === 'FAILED'
      ? <div className="error" role="alert">{result.error}</div>
      : <div className="notice" role="status"><strong>{result.result?.message ?? '向量模型切换成功'}</strong>{result.result?.message_detail ? <> · {result.result.message_detail}</> : null}</div>)}
  </section>;
}
