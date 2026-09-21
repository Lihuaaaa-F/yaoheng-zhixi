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
  const visibleJobs = showHistory ? jobs.filter(j => j.kind !== 'data_parse' && j.kind !== 'kb' && j.kind !== 'template_parse' && j.kind !== 'vector_switch')
    : jobs.filter(j => (j.result?.snapshot?.snapshot_id === snapshot?.snapshot_id || j.input?.snapshot_id === snapshot?.snapshot_id)
      && j.kind === 'report').slice(0, 3);
  const snapshotJob = jobs.find(j => (j.result?.snapshot?.snapshot_id === snapshot?.snapshot_id || j.input?.snapshot_id === snapshot?.snapshot_id) && j.kind === 'report');
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
        <strong>{j.result?.snapshot?.product ?? '报告'} · {j.result?.snapshot?.factory ?? ''} · {j.result?.snapshot?.period?.start ?? j.input?.month ?? ''}{j.result?.snapshot?.period?.end !== j.result?.snapshot?.period?.start ? ` 至 ${j.result?.snapshot?.period?.end ?? ''}` : ''}</strong>
        <p>执行状态：{jobLabel(j.status)}{j.detail ? ` · ${j.detail}` : ''}{typeof j.progress === 'number' && !['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(j.status) ? `（${j.progress}%）` : ''}</p>
        {j.result?.narrative && <AnalysisStatus narrative={j.result.narrative} review={j.result.acceptance} />}
        <Acceptance result={j.result} />
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
