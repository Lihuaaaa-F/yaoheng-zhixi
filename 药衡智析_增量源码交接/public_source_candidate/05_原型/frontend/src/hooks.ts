// 数据获取 hooks（2026-09-21 重构 #23）：从 App.tsx 抽出的任务/整改轮询逻辑，
// 状态归属与轮询节奏集中一处；App 只消费 {jobs, actions, refresh}。
import { useCallback, useEffect, useRef, useState } from 'react';
import { api, contextQuery } from './api';
import { Job, RpaAction } from './types';

export function useJobsActions(tab: number, contextId: string) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [actions, setActions] = useState<RpaAction[]>([]);
  const [error, setError] = useState('');
  const currentContext = useRef(contextId);
  currentContext.current = contextId;
  const refresh = useCallback(async () => {
    const id = contextId;
    const [j, a] = await Promise.all([api(`/jobs?${contextQuery(id)}`), api(`/actions?${contextQuery(id)}`)]);
    if (currentContext.current !== id) return;
    setJobs(Array.isArray(j) ? j : []);
    setActions(Array.isArray(a) ? a : []);
  }, [contextId]);
  useEffect(() => {
    if (tab !== 2 || !contextId) return;
    const c = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const [j, a] = await Promise.all([api(`/jobs?${contextQuery(contextId)}`, undefined, c.signal), api(`/actions?${contextQuery(contextId)}`, undefined, c.signal)]);
        if (!c.signal.aborted) { setJobs(Array.isArray(j) ? j : []); setActions(Array.isArray(a) ? a : []); }
      } catch (e) {
        if (!c.signal.aborted) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!c.signal.aborted) timer = setTimeout(poll, 2000);
      }
    };
    void poll();
    return () => { c.abort(); clearTimeout(timer); };
  }, [tab, contextId]);
  return { jobs, setJobs, actions, setActions, jobsError: error, refresh };
}
