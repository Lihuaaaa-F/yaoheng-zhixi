// 数据获取 hooks（2026-09-21 重构 #23；2026-09-22 三模块改版）：报告生成/
// 问题整改两个工作台子页需要任务与整改轮询；tab<0 表示当前页不轮询。
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
    if (!id) return;
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
