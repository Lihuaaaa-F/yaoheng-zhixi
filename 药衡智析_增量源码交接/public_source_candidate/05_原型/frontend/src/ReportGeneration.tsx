import { snapshotReport } from './NarrativePanel';
import { useState } from 'react';
import { api, Selection } from './api';
import { Acceptance, AnalysisStatus, DeveloperDetails } from './presentation';

const jobLabel = (s: string) => ({ SUCCEEDED: '生成流程结束', DEGRADED: '生成流程结束，存在待评或降级项', FAILED: '生成失败', QUEUED: '等待生成', RUNNING: '正在生成' }[s] ?? '处理中');

/** 工作台 · 报告生成：按当前分析选择生成报告任务、跟踪进度、验收与下载。 */
export default function ReportGeneration({ selection, snapshot, jobs, refresh, onError }: {
  selection: Selection; snapshot: any; jobs: any[]; refresh: () => Promise<void>; onError: (s: string) => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState('');
  // 2026-09-24 修复（AUD-FE-01）：按当前选择参数过滤而非 snapshot_id——
  // 此前进本页改筛选后快照未刷新，新任务默认列表不显示（须勾"查看历史"）。
  const matchesSelection = (j: any) => j.kind === 'report'
    && j.input?.context_id === selection.context_id
    && j.input?.factory === selection.factory
    && j.input?.product === selection.product
    && j.input?.month === selection.month
    && j.input?.analysis_type === selection.analysis_type;
  const visibleJobs = showHistory ? jobs.filter(j => j.kind !== 'data_parse' && j.kind !== 'kb' && j.kind !== 'template_parse' && j.kind !== 'vector_switch')
    : jobs.filter(matchesSelection).slice(0, 3);
  const snapshotJob = jobs.find(matchesSelection);
  const needsRetry = !!snapshotJob && ['DEGRADED', 'FAILED'].includes(snapshotJob.status);
  const currentReport = snapshotReport(jobs, snapshot?.snapshot_id);
  const run = async (fn: () => Promise<void>) => {
    setPending(true); onError('');
    try { await fn(); await refresh(); }
    catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setPending(false); }
  };
  return <section className="panel">
    <div className="panel-heading">
      <div><h2>报告生成与下载</h2>
        <p className="muted">{selection.factory} · {selection.product} · {selection.month} · {{ monthly: '月度', quarterly: '季度', special: '专题' }[selection.analysis_type]}报告</p></div>
      <button className="primary" disabled={pending || !snapshot} onClick={() => run(async () => {
        await api('/reports', { ...selection, ...(needsRetry ? { retry: true } : {}) });
        setNotice(needsRetry ? '已忽略缓存重新生成，约需一至两分钟；完成后此处更新验收状态。' : '报告已提交，进度见下方任务卡；完成后核验分项验收。');
      })}>{needsRetry ? '重新生成（忽略缓存）' : '生成报告'}</button>
    </div>
    <p role="status">{notice}</p>
    <label className="history-toggle"><input type="checkbox" checked={showHistory} onChange={e => setShowHistory(e.target.checked)} /> 查看历史报告及失败记录</label>
    {!visibleJobs.length
      ? <p className="empty">{snapshot ? '尚无报告。生成后分别核验文件、业务内容与人工评审。' : '请先在左侧选择有效的分析对象（数据范围/产品/工厂/月份）。'}</p>
      : <div className="job-list">{visibleJobs.map(j => <article className="job" key={j.id}>
        <strong>{j.result?.snapshot?.product ?? '报告'} · {j.result?.snapshot?.factory ?? ''} · {j.result?.snapshot?.period?.start ?? j.input?.month ?? ''}{j.result?.snapshot?.period?.end !== j.result?.snapshot?.period?.start ? ` 至 ${j.result?.snapshot?.period?.end ?? ''}` : ''}{j.created ? <span className="muted" style={{ fontWeight: 400 }}>（生成于 {(j.created ?? '').slice(5, 16).replace('T', ' ')}）</span> : null}</strong>
        <p>执行状态：{jobLabel(j.status)}{j.detail && j.detail !== '排队等待处理' ? ` · ${j.detail}` : ''}{typeof j.progress === 'number' && !['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(j.status) ? `（${j.progress}%）` : ''}</p>
        {j.result?.narrative && <AnalysisStatus narrative={j.result.narrative} review={j.result.acceptance} />}
        <Acceptance result={j.result} />
        {['SUCCEEDED', 'DEGRADED'].includes(j.status) && <AcceptanceUpload jobId={j.id} onDone={refresh} onError={onError} />}
        {j.error && <p className="error">本次生成未通过：{j.error}</p>}
        <div className="downloads">{['docx', 'pdf'].map(kind => {
          const a = j.result?.[kind];
          return a?.artifact_id && ['SUCCEEDED', 'DEGRADED'].includes(j.status)
            ? <a key={kind} href={`/api/artifacts/${encodeURIComponent(a.artifact_id)}`} download>{kind === 'docx' ? 'Word' : 'PDF'} 下载（待审核）</a>
            : <span key={kind}>{kind.toUpperCase()} · {j.status === 'FAILED' ? '生成未通过' : a?.status === 'PASS' ? '文件已生成' : '等待文件'}</span>;
        })}{j.result?.audit?.artifact_id && ['SUCCEEDED', 'DEGRADED'].includes(j.status) && <a href={`/api/artifacts/${encodeURIComponent(j.result.audit.artifact_id)}`} download>机器审计附件</a>}</div>
        <DeveloperDetails value={j} />
      </article>)}</div>}
    {currentReport && <p className="muted">当前分析已有报告 {currentReport.id.slice(0, 8)}（{jobLabel(currentReport.status)}）；重复生成按输入版本指纹幂等复用。</p>}
  </section>;
}

const HUMAN_DIMS = ['section_completeness', 'readability', 'visual_quality'] as const;
/** 人工验收：上传已签署的验收文档，登记审核记录并重算验收状态（2026-09-23 反馈）。 */
function AcceptanceUpload({ jobId, onDone, onError }: { jobId: string; onDone: () => void; onError: (s: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [reviewer, setReviewer] = useState('');
  const [score, setScore] = useState(5);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState('');
  const submit = async () => {
    if (!reviewer.trim()) { onError('人工验收：请填写验收人姓名。'); return; }
    if (!file) { onError('人工验收：请选择验收文档（Word/PDF/截图）。'); return; }
    setBusy(true); onError('');
    try {
      const fd = new FormData();
      fd.append('file', file); fd.append('reviewer', reviewer.trim()); fd.append('attribution_score', String(score));
      for (const k of HUMAN_DIMS) fd.append(k, 'PASS');
      const r = await fetch(`/api/reports/${encodeURIComponent(jobId)}/acceptance-doc`, { method: 'POST', body: fd });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error?.message ?? data.detail ?? `HTTP ${r.status}`);
      setDone(`已登记人工验收（验收人 ${reviewer.trim()}；验收文档已存档，编号 …${String(data.acceptance_doc?.artifact_id ?? '').slice(-8)}），下方验收状态已更新。`);
      onDone();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  return <details className="acceptance-upload">
    <summary>人工验收 · 上传验收文档</summary>
    {done ? <p className="notice" role="status">{done}</p> : <>
      <p className="muted">上传已签署的验收文档（Word / PDF / 截图），系统将其存档为验收凭证并登记人工验收记录；人工三项（章节实质完整、内容可读、视觉合格）按“通过”登记，验收状态立即重算。</p>
      <div className="acceptance-form">
        <label>验收人<input value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="如：张三（质量部）" /></label>
        <label>人工归因评分（0–5）<select value={score} onChange={e => setScore(Number(e.target.value))}>{[5, 4, 3, 2, 1, 0].map(n => <option key={n} value={n}>{n}</option>)}</select></label>
        <label className="grow">验收文档<input type="file" accept=".docx,.pdf,.png,.jpg,.jpeg" onChange={e => setFile(e.target.files?.[0] ?? null)} /></label>
        <button className="primary" disabled={busy} onClick={() => void submit()}>{busy ? '正在提交…' : '提交人工验收'}</button>
      </div>
    </>}
  </details>;
}
