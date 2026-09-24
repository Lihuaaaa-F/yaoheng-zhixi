import { snapshotReport } from './NarrativePanel';
import { useEffect, useState } from 'react';
import { Button, Input, Select } from 'antd';
import FilePicker from './FilePicker';
import { api, apiHeaders, openApiFile, Selection } from './api';
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
    && j.input?.analysis_type === selection.analysis_type
    && (j.input?.basis??'unit') === selection.basis
    && (j.input?.topic??'') === (selection.topic??'');
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
        {['SUCCEEDED', 'DEGRADED'].includes(j.status) && <ReportAcceptance job={j} onError={onError} />}
        {j.error && <p className="error">本次生成未通过：{j.error}</p>}
        <div className="downloads">{['docx', 'pdf'].map(kind => {
          const a = j.result?.[kind];
          return a?.artifact_id && ['SUCCEEDED', 'DEGRADED'].includes(j.status)
            ? <a key={kind} href={`/api/artifacts/${encodeURIComponent(a.artifact_id)}`} onClick={event=>{event.preventDefault();void openApiFile(`/api/artifacts/${encodeURIComponent(a.artifact_id)}`,`${j.input?.product??'成本分析'}_${j.input?.month??'报告'}.${kind}`).catch(e=>onError(e.message))}} download>{kind === 'docx' ? 'Word' : 'PDF'} 下载（待审核）</a>
            : <span key={kind}>{kind.toUpperCase()} · {j.status === 'FAILED' ? '生成未通过' : a?.status === 'PASS' ? '文件已生成' : '等待文件'}</span>;
        })}{j.result?.audit?.artifact_id && ['SUCCEEDED', 'DEGRADED'].includes(j.status) && <a href={`/api/artifacts/${encodeURIComponent(j.result.audit.artifact_id)}`} onClick={event=>{event.preventDefault();void openApiFile(`/api/artifacts/${encodeURIComponent(j.result.audit.artifact_id)}`,'报告验证记录.json').catch(e=>onError(e.message))}} download>机器审计附件</a>}</div>
        <DeveloperDetails value={j} />
      </article>)}</div>}
    {currentReport && <p className="muted">当前分析已有报告（{jobLabel(currentReport.status)}）。相同输入可复用已有结果，避免重复生成。</p>}
  </section>;
}

const HUMAN_DIMS = ['section_completeness', 'readability', 'visual_quality'] as const;
const HUMAN_DIM_SHORT: Record<string, string> = { section_completeness: '章节', readability: '可读', visual_quality: '版式' };
/** 人工验收区（2026-09-24）：评定标准说明 + 负责人评审登记 + 可追踪的评审历史。 */
function ReportAcceptance({ job, onError }: { job: any; onError: (s: string) => void }) {
  const [version, setVersion] = useState(0);
  return <>
    <AcceptanceUpload jobId={job.id} onDone={() => setVersion(value => value + 1)} onError={onError} />
    <ReviewHistory jobId={job.id} version={version} />
  </>;
}
/** 人工验收：上传已签署的验收文档，登记审核记录并重算验收状态（2026-09-23 反馈）。 */
function AcceptanceUpload({ jobId, onDone, onError }: { jobId: string; onDone: () => void; onError: (s: string) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [reviewer, setReviewer] = useState('');
  const [score, setScore] = useState('');
  const [dimensions,setDimensions]=useState<Record<string,string>>({});
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState('');
  const submit = async () => {
    if (!reviewer.trim()) { onError('人工验收：请填写验收负责人姓名（评定必须可追踪到人）。'); return; }
    if (!file) { onError('人工验收：请选择验收文档（Word/PDF/截图）。'); return; }
    if(score===''||HUMAN_DIMS.some(key=>!['PASS','FAIL'].includes(dimensions[key]))){onError('人工验收：请人工填写归因评分，并逐项选择通过或未通过。');return;}
    setBusy(true); onError('');
    try {
      const fd = new FormData();
      fd.append('file', file); fd.append('reviewer', reviewer.trim()); fd.append('attribution_score', String(score));
      for (const k of HUMAN_DIMS) fd.append(k, dimensions[k]);
      const r = await fetch(`/api/reports/${encodeURIComponent(jobId)}/acceptance-doc`, { method: 'POST', body: fd, headers: apiHeaders() });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error?.message ?? data.detail ?? `HTTP ${r.status}`);
      setDone(`已登记人工验收（验收负责人 ${reviewer.trim()}；按各项实际评审结果记录，绑定当前报告版本），验收文档已存档。`);
      onDone();
    } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  return <details className="acceptance-upload">
    <summary>报告评定（人工验收）· 由负责人逐项评定</summary>
    {done ? <p className="notice" role="status">{done}</p> : <>
      <p className="muted">评定标准：报告合格需 8 个分项全部「通过」。「文件可打开 / 计算一致 / 证据适用 / 任务可执行 / 模型参与」五项由系统自动核验；「章节实质完整 / 内容可读 / 视觉与版式」三项必须由验收负责人在此逐项评定——填写负责人姓名、人工归因评分（0–5），并上传已签署的验收文档。评定记录会保存负责人、时间与所评报告版本；报告重新生成后原评定自动失效，需重新评定。</p>
      <div className="acceptance-form">
        <label>验收负责人（必填）<Input aria-label="验收负责人" value={reviewer} onChange={e => setReviewer(e.target.value)} placeholder="如：张三（质量部）" /></label>
        <label>人工归因评分（0–5）<Select aria-label="人工归因评分" value={score||undefined} placeholder="请人工评分" onChange={setScore} options={[0,1,2,3,4,5].map(n=>({value:String(n),label:String(n)}))}/></label>
        {([['section_completeness','章节实质完整'],['readability','内容可读'],['visual_quality','视觉与版式']] as const).map(([key,label])=><label key={key}>{label}<Select aria-label={label} value={dimensions[key]||undefined} placeholder="请人工评审" onChange={choice=>setDimensions(value=>({...value,[key]:choice}))} options={[{value:'PASS',label:'通过'},{value:'FAIL',label:'未通过'}]}/></label>)}
        <div className="upload-field grow"><span>验收文档</span><FilePicker file={file} onChange={setFile} accept=".docx,.pdf,.png,.jpg,.jpeg" disabled={busy}/></div>
        <Button type="primary" loading={busy} onClick={() => void submit()}>提交评定</Button>
      </div>
    </>}
  </details>;
}
/** 评审历史：展示历次评定的负责人、时间、分项结果与版本有效性，确保可追踪。 */
function ReviewHistory({ jobId, version }: { jobId: string; version: number }) {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    const controller = new AbortController();
    api(`/reports/${encodeURIComponent(jobId)}/reviews`, undefined, controller.signal)
      .then(value => { if (!controller.signal.aborted) setData(value); })
      .catch(() => { if (!controller.signal.aborted) setData({ reviews: [] }); });
    return () => controller.abort();
  }, [jobId, version]);
  const reviews = data?.reviews ?? [];
  if (!reviews.length) return null;
  return <details className="review-history">
    <summary>评审历史（{reviews.length} 条）</summary>
    <div className="table-scroll"><table>
      <thead><tr><th>验收负责人</th><th>评审时间</th><th>人工分项结果</th><th>归因评分</th><th>绑定报告版本</th><th>备注</th></tr></thead>
      <tbody>{reviews.map((review: any, index: number) => <tr key={review.id ?? index}>
        <td>{review.reviewer}</td>
        <td className="muted">{String(review.reviewed_at ?? '').slice(0, 19).replace('T', ' ')}</td>
        <td>{HUMAN_DIMS.map(key => {
          const item = review.dimensions?.[key];
          const status = typeof item === 'object' && item ? item.status : item;
          return `${HUMAN_DIM_SHORT[key]}${status === 'PASS' ? '通过' : status === 'FAIL' ? '未通过' : '待评'}`;
        }).join(' / ')}</td>
        <td>{review.attribution_score ?? '—'}/5</td>
        <td>{review.valid_for_current_artifacts ? <span className="badge" data-status="PASS">当前版本有效</span> : <span className="badge" data-status="FAIL">已失效（报告已更新）</span>}</td>
        <td>{review.comment || '—'}</td>
      </tr>)}</tbody>
    </table></div>
    <p className="muted">每条评审绑定当次报告文件版本（文件哈希）；报告重新生成后旧评审自动标记失效，须由负责人重新评定。</p>
  </details>;
}
