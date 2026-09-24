import { useCallback, useEffect, useState } from 'react';
import { Button, Modal, Select } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import FilePicker from './FilePicker';
import { api, apiHeaders } from './api';
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
  const response = await fetch('/api/imports/uploads', { method: 'POST', body: form, headers: apiHeaders() });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message ?? data?.detail ?? `上传失败（HTTP ${response.status}）`);
  if (kind === 'business') window.dispatchEvent(new Event('pharma:data-changed'));
  return data;
}

export function ImportUploadPanel({ kind, types, onUploaded, hint, processingNotes }: {
  kind: string; types: { id: string; label: string; accept: string; note?: string }[];
  onUploaded: () => void; hint: string; processingNotes?: string;
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
    const chosen = file;
    try {
      const saved = await uploadTypedFile(kind, dataType, chosen);
      // 同内容重复上传是幂等的：返回已有记录（可能早已解析完，直接躺在
      // "已处理记录"里）。必须说明白，否则用户会以为被悄悄解析了。
      setMessage(saved.dedup
        ? `「${chosen.name}」的内容此前已上传过（当前状态：${IMPORT_STATUS_LABELS[saved.status] ?? saved.status}），本次未重复导入。${saved.status === 'UPLOADED' || saved.status === 'PARSE_FAILED' ? '它就在下方待解析列表中。' : '如需更换数据，请上传内容不同的修正文件。'}`
        : `已上传：${chosen.name}（${active?.label}），进入下方列表等待解析。`);
      setFile(null);
      onUploaded();
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  return <section className="panel">
    <h2>导入数据</h2>
    <p className="muted">{hint}</p>
    <div className="filters import-filters">
      <label>数据类型<Select aria-label="数据类型" value={dataType} options={types.map(t => ({ value: t.id, label: t.label }))} onChange={setDataType} disabled={busy} /></label>
      <div className="upload-field"><span>文件</span><FilePicker file={file} onChange={setFile} accept={active?.accept ?? '*'} disabled={busy} /></div>
      <Button type="primary" icon={<UploadOutlined />} disabled={!file} loading={busy} onClick={doUpload}>上传</Button>
    </div>
    {active?.note && <p className="muted" style={{ whiteSpace: 'normal' }}>{active.note}</p>}
    {processingNotes && <details className="processing-notes"><summary>处理说明</summary><p className="muted">{processingNotes}</p></details>}
    {error && <div className="error" role="alert">{error}</div>}
    {message && <div className="notice" role="status">{message}</div>}
  </section>;
}

export const KIND_LABELS: Record<string, string> = { business: '业务数据', knowledge: '知识资料', template: '报告模板' };
export const DATA_TYPE_LABELS: Record<string, string> = {
  cost_summary: '成本汇总数据', material_detail: '原材料消耗明细', manufacturing_detail: '制造费用明细',
  labor_detail: '人工工时明细', budget: '预算数据', industry_reference: '行业参考数据',
  product: '产品知识', industry: '行业知识', enterprise: '企业内部知识',
  monthly: '月度成本分析', quarterly: '季度成本分析', special: '专题分析',
};

const DELETABLE_IMPORT_STATUSES = ['UPLOADED', 'PARSE_FAILED'];

export function ImportListTable({ imports, onPreview, onDelete, emptyText }: {
  imports: any[]; onPreview: (id: string) => void; onDelete?: (record: any) => void; emptyText: string;
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
      <td><button onClick={() => onPreview(r.id)}>预览</button>
        {onDelete && DELETABLE_IMPORT_STATUSES.includes(r.status) && <button className="danger" onClick={() => onDelete(r)}>删除</button>}</td>
    </tr>)}</tbody>
  </table></div>;
}

/** 单页导入工作流：上传面板 + 待解析列表 + 解析按钮 + 进度 + 终态提示。 */
export default function ImportWorkflow({ kind, types, parsePath, parseLabel, successPrefix, failPrefix,
  parseBody, hint, processingNotes, listTitle, extra, emptyText, onPublished }: {
  kind: string; types: { id: string; label: string; accept: string; note?: string }[];
  parsePath: string; parseLabel: string; successPrefix: string; failPrefix: string;
  parseBody?: () => any; hint: string; processingNotes?: string; listTitle: string; extra?: (record: any) => any;
  emptyText?: string; onPublished?: (value: any) => void;
}) {
  const { imports, importsError, refresh } = useImports(kind);
  const [previewId, setPreviewId] = useState('');
  const [jobId, setJobId] = useState(() => sessionStorage.getItem(`pharma-import-${kind}`) ?? '');
  const [result, setResult] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [replacements, setReplacements] = useState<Record<string, string>>({});
  const [acceptedIds, setAcceptedIds] = useState<string[]>([]);
  const [modal, modalHolder] = Modal.useModal();
  useEffect(() => {
    if (kind !== 'business') return;
    const controller = new AbortController();
    api('/workspace', undefined, controller.signal).then(value => {
      if (!controller.signal.aborted) setAcceptedIds((value.imported_files ?? []).map((item: any) => item.import_id));
    }).catch(() => { if (!controller.signal.aborted) setAcceptedIds([]); });
    return () => controller.abort();
  }, [kind, imports]);
  useEffect(()=>{if(jobId)return;const active=imports.find(record=>record.status==='PARSING'&&record.meta?.parse_job);if(active){setJobId(active.meta.parse_job);sessionStorage.setItem(`pharma-import-${kind}`,active.meta.parse_job)}},[imports,jobId,kind]);
  const waiting = imports.filter(r => r.status === 'UPLOADED' || r.status === 'PARSE_FAILED');
  const parsed = imports.filter(r => !['UPLOADED','PARSE_FAILED'].includes(r.status));
  const startParse = async () => {
    const changes = Object.fromEntries(Object.entries(replacements).filter(([id, previous]) => waiting.some(item => item.id === id) && acceptedIds.includes(previous)));
    if (Object.keys(changes).length && !await modal.confirm({ title: '更新已接入的数据版本？',
      content: <><p>以下新文件将替代对应文件参与分析。旧原件及历史结果仍保留，全部文件校验成功后才会更新工作区。</p><ul>{Object.entries(changes).map(([id, previous]) => <li key={id}>{imports.find(item => item.id === previous)?.filename} → {imports.find(item => item.id === id)?.filename}</li>)}</ul></>,
      okText: '确认更新并解析', cancelText: '返回检查' })) return;
    setBusy(true); setError(''); setResult(null);
    try {
      const response = await api(parsePath, { ...(parseBody ? parseBody() : {}), ...(kind === 'business' ? { replacements: changes } : {}) });
      setJobId(response.job_id); sessionStorage.setItem(`pharma-import-${kind}`, response.job_id);
      if (kind === 'business') window.dispatchEvent(new Event('pharma:data-changed'));
      void refresh(); // 列表即时切到“解析中”
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  const removeImport = async (record: any) => {
    if (!await modal.confirm({ title: `删除待解析文件“${record.filename}”？`, content: '删除后如需重新导入，请再次上传。已接入数据不受影响。', okText: '删除文件', okButtonProps: { danger: true }, cancelText: '保留' })) return;
    setError('');
    try {
      await api(`/imports/${encodeURIComponent(record.id)}`, undefined, undefined, 'DELETE');
      if (kind === 'business') window.dispatchEvent(new Event('pharma:data-changed'));
      if (previewId === record.id) setPreviewId('');
      void refresh();
    } catch (e: any) { setError(e.message ?? String(e)); }
  };
  return <div>
    {modalHolder}
    <ImportUploadPanel kind={kind} types={types} onUploaded={refresh} hint={hint} processingNotes={processingNotes} />
    <section className="panel">
      <div className="panel-heading"><h2>{listTitle}</h2>
        <Button type="primary" disabled={!!jobId || !waiting.length} loading={busy} onClick={startParse}>
          {parseLabel}
        </Button></div>
      <p className="muted">检查下方文件后，点击「{parseLabel}」。处理进度和结果将在本页显示。</p>
      {importsError && <div className="error" role="alert">列表读取失败：{importsError}</div>}
      {error && <div className="error" role="alert">{error}</div>}
      <h3>待解析（{waiting.length}）</h3>
      <ImportListTable imports={waiting} onPreview={setPreviewId} onDelete={removeImport} emptyText={emptyText ?? '暂无待解析数据，请先在上方导入。'} />
      {kind === 'business' && waiting.length > 0 && acceptedIds.length > 0 && <details className="import-version-options"><summary>更新已接入文件（可选）</summary><p className="muted">补充新期间或新产品时保留“新增文件”。修正旧表时，选择由新文件替代的旧版本；原件会保留。</p>{waiting.map(record => <label className="import-version-row" key={record.id}><span>{record.filename}</span><Select aria-label={`为 ${record.filename} 选择替代文件`} value={replacements[record.id] || ''} disabled={busy || !!jobId} options={[{ value: '', label: '新增文件' }, ...imports.filter(item => acceptedIds.includes(item.id) && item.meta?.data_type === record.meta?.data_type).map(item => ({ value: item.id, label: item.filename }))]} onChange={value => setReplacements(current => ({ ...current, [record.id]: value }))} /></label>)}</details>}
      {jobId && <JobProgress jobId={jobId} onDone={job => {
        setResult(job); setJobId(''); sessionStorage.removeItem(`pharma-import-${kind}`); refresh();
        if (kind === 'business') window.dispatchEvent(new Event('pharma:data-changed'));
        if (job.status === 'SUCCEEDED' || job.status === 'DEGRADED') {
          onPublished?.(job.result);
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
