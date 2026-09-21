import { useEffect, useRef, useState } from 'react';
import { api } from './api';

/** 解析流水线进度：轮询 /api/jobs/{id}，实时显示百分比与当前进度内容。
 * 终态（SUCCEEDED/DEGRADED/FAILED）后停止轮询并回调 onDone。 */
export default function JobProgress({ jobId, onDone, label = '处理进度' }: {
  jobId: string; onDone?: (job: any) => void; label?: string;
}) {
  const [job, setJob] = useState<any>(null);
  const [error, setError] = useState('');
  const doneRef = useRef(false);
  useEffect(() => {
    doneRef.current = false;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const value = await api(`/jobs/${encodeURIComponent(jobId)}`, undefined, controller.signal);
        if (controller.signal.aborted) return;
        setJob(value); setError('');
        if (['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(value.status)) {
          if (!doneRef.current) { doneRef.current = true; onDone?.(value); }
          return; // 终态停止轮询
        }
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      }
      if (!controller.signal.aborted) timer = setTimeout(poll, 1200);
    };
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);
  if (!job) return <p role="status" className="muted">{error ? `进度读取失败：${error}` : '正在读取任务进度…'}</p>;
  const percent = Math.max(0, Math.min(100, Number(job.progress ?? 0)));
  const terminal = ['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(job.status);
  return <div className="job-progress" role="status" aria-label={label}>
    <div className="progress-head"><span>{label}</span><strong>{percent}%</strong></div>
    <div className="progress-track"><div className="progress-fill" data-status={job.status} style={{ width: `${percent}%` }} /></div>
    <p className="muted progress-detail">{job.detail || (terminal ? '已完成' : '排队等待处理…')}</p>
    <details className="progress-history"><summary>步骤时间线</summary>
      <ul>{(job.history ?? []).map((h: any, i: number) => <li key={i}><span className="muted">{String(h.at ?? '').slice(11, 19)}</span> {h.stage}{h.detail ? ` · ${h.detail}` : ''}</li>)}</ul>
    </details>
  </div>;
}
