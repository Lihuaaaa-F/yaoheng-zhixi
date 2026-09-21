import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import FilePreview from './FilePreview';
import JobProgress from './JobProgress';

/** 数据中心共享：上传（类型分流）→ 导入列表（类型/文件名/格式/预览）→
 * 一键解析按钮 → 进度条 → 成功/失败提示。三个子项仅按钮与提示语不同。 */
export const IMPORT_STATUS_LABELS: Record<string, string> = {
  UPLOADED: '待解析', PARSING: '解析中', PARSED: '已解析', PARSE_FAILED: '解析失败', PUBLISHED: '已发布',
};

export function useImports(kind: string) {
  const [imports, setImports] = useState<any[]>([]);
  const [error, setError] = useState('');
  const refresh = useCallback(() => api(`/imports?kind=${kind}`).then(x => {
    setImports(Array.isArray(x) ? x : []); setError('');
  }).catch(e => setError(e instanceof Error ? e.message : String(e))), [kind]);
  useEffect(() => { void refresh(); }, [refresh]);
  return { imports, importsError: error, refresh };
}

export async function uploadTypedFile(kind: string, dataType: string, file: File): Promise<any> {
  const form = new FormData();
  form.append('kind', kind);
  form.append('data_type', dataType);
  form.append('file', file);
  const response = await fetch('/api/imports/uploads', { method: 'POST', body: form });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message ?? data?.detail ?? `上传失败（HTTP ${response.status}）`);
  return data;
}

export function ImportUploadPanel({ kind, types, onUploaded, hint }: {
  kind: string; types: { id: string; label: string; accept: string; note?: string }[];
  onUploaded: () => void; hint: string;
}) {
  const [dataType, setDataType] = useState(types[0]?.id ?? '');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const active = types.find(t => t.id === dataType);
  const doUpload = async () => {
    if (!file) { setError('请先选择文件'); return; }
    setBusy(true); setError(''); setMessage('');
    try {
      await uploadTypedFile(kind, dataType, file);
      setMessage(`已上传：${file.name}（${active?.label}），进入下方列表等待解析。`);
      setFile(null);
      onUploaded();
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  return <section className="panel">
    <h2>导入数据</h2>
    <p className="muted">{hint}</p>
    <div className="filters import-filters">
      <label>数据类型<select aria-label="数据类型" value={dataType} onChange={e => setDataType(e.target.value)}>
        {types.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
      </select></label>
      <label>选择文件<input type="file" accept={active?.accept ?? '*'} onChange={e => setFile(e.target.files?.[0] ?? null)} /></label>
      <button className="primary" disabled={busy || !file} onClick={doUpload}>{busy ? '上传中…' : '上传'}</button>
    </div>
    {active?.note && <p className="muted" style={{ whiteSpace: 'normal' }}>{active.note}</p>}
    {error && <div className="error" role="alert">{error}</div>}
    {message && <div className="notice" role="status">{message}</div>}
  </section>;
}

export const KIND_LABELS: Record<string, string> = { business: '业务数据', knowledge: '知识资料', template: '报告模板' };
export const DATA_TYPE_LABELS: Record<string, string> = {
  cost_summary: '成本汇总数据', material_detail: '原材料消耗明细', manufacturing_detail: '制造费用明细',
  labor_detail: '人工工时明细', budget: '预算数据',
  product: '产品知识', industry: '行业知识', enterprise: '企业内部知识',
  monthly: '月度成本分析', quarterly: '季度成本分析', special: '专题分析',
};

export function ImportListTable({ imports, onPreview, emptyText }: {
  imports: any[]; onPreview: (id: string) => void; emptyText: string;
}) {
  const typeLabel = (record: any) => record.meta?.data_type_label
    ?? DATA_TYPE_LABELS[record.meta?.data_type] ?? KIND_LABELS[record.kind] ?? record.kind;
  if (!imports.length) return <p className="empty">{emptyText}</p>;
  return <div className="table-scroll"><table>
    <thead><tr><th>数据类型</th><th>文件名</th><th>文件格式</th><th>大小</th><th>状态</th><th>上传时间</th><th>操作</th></tr></thead>
    <tbody>{imports.map((r, i) => <tr key={r.id ?? i}>
      <td>{typeLabel(r)}</td>
      <td title={r.meta?.parse_error ?? r.meta?.parsed?.context_id ?? ''}>{r.filename}</td>
      <td>{(r.meta?.suffix ?? '').toUpperCase() || '—'}</td>
      <td>{((r.size ?? 0) / 1024).toFixed(1)} KB</td>
      <td><span className="badge" data-status={r.status}>{IMPORT_STATUS_LABELS[r.status] ?? r.status}</span>
        {r.status === 'PARSE_FAILED' && <p className="muted error-inline">{(r.meta?.parse_error ?? '').slice(0, 120)}</p>}</td>
      <td className="muted">{(r.created ?? '').slice(0, 19).replace('T', ' ')}</td>
      <td><button onClick={() => onPreview(r.id)}>预览</button></td>
    </tr>)}</tbody>
  </table></div>;
}

/** 单页导入工作流：上传面板 + 待解析列表 + 解析按钮 + 进度 + 终态提示。 */
export default function ImportWorkflow({ kind, types, parsePath, parseLabel, successPrefix, failPrefix,
  parseBody, hint, listTitle, extra }: {
  kind: string; types: { id: string; label: string; accept: string; note?: string }[];
  parsePath: string; parseLabel: string; successPrefix: string; failPrefix: string;
  parseBody?: () => any; hint: string; listTitle: string; extra?: (record: any) => any;
}) {
  const { imports, importsError, refresh } = useImports(kind);
  const [previewId, setPreviewId] = useState('');
  const [jobId, setJobId] = useState('');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const waiting = imports.filter(r => r.status === 'UPLOADED' || r.status === 'PARSE_FAILED');
  const parsed = imports.filter(r => r.status !== 'UPLOADED');
  const startParse = async () => {
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await api(parsePath, parseBody ? parseBody() : {});
      setJobId(response.job_id);
      void refresh(); // 列表即时切到“解析中”
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  return <div>
    <ImportUploadPanel kind={kind} types={types} onUploaded={refresh} hint={hint} />
    <section className="panel">
      <div className="panel-heading"><h2>{listTitle}</h2>
        <button className="primary" disabled={busy || !!jobId || !waiting.length} onClick={startParse}>
          {busy ? '提交中…' : parseLabel}
        </button></div>
      <p className="muted">已导入但未解析的数据先进入列表等待；点击「{parseLabel}」开始全流程（含数据预处理→分析等步骤，进度实时显示）。</p>
      {importsError && <div className="error" role="alert">列表读取失败：{importsError}</div>}
      {error && <div className="error" role="alert">{error}</div>}
      <h3>待解析（{waiting.length}）</h3>
      <ImportListTable imports={waiting} onPreview={setPreviewId} emptyText="暂无待解析数据，请先在上方导入。" />
      {jobId && <JobProgress jobId={jobId} onDone={job => {
        setResult(job); setJobId(''); refresh();
        if (job.status === 'SUCCEEDED' || job.status === 'DEGRADED') {
          setTimeout(() => setResult(null), 15000);
        }
      }} />}
      {result && (result.status === 'FAILED'
        ? <div className="error" role="alert">{failPrefix}{result.error?.startsWith(failPrefix) ? result.error.slice(failPrefix.length) : `，${result.error ?? '未知原因'}`}</div>
        : <div className="notice" role="status"><strong>{result.result?.message ?? successPrefix}</strong>{result.result?.message_detail ? <> · {result.result.message_detail}</> : null}</div>)}
      {parsed.length > 0 && <><h3>已处理记录</h3><ImportListTable imports={parsed} onPreview={setPreviewId} emptyText="" /></>}
      {extra ? extra(parsed) : null}
    </section>
    {previewId && <FilePreview importId={previewId} onClose={() => setPreviewId('')} />}
  </div>;
}
