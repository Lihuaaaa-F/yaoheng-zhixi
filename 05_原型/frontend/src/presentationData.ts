/** Display transformations only; canonical Decimal values stay in API evidence. */
export const cleanText = (value: unknown) => String(value ?? '')
  .replace(/\\r\\n|\\n|\\r|\r\n|\r/g, '\n').replace(/\\t|\t/g, ' ').trim();

export function elementDelta(element: any, comparison: string, basis: string): number | null {
  const selected = element.comparisons?.[comparison]?.[basis];
  const raw = selected ? selected.delta : comparison === 'mom' ? element.delta : null;
  if (raw == null || raw === '') return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

export function waterfallBottoms(start: number, changes: (number | null)[]): (number | null)[] {
  let running: number | null = start;
  return changes.map(change => {
    // Once a delta is unknown, later cumulative levels cannot be inferred.
    if (running === null || change === null) { running = null; return null; }
    const bottom = Math.min(running, running + change);
    running += change;
    return bottom;
  });
}

export function jobNotification(job: { kind: string; status: string }) {
  if (!['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(job.status)) return null;
  const target = {
    report: { page: 'reports', label: '报告', success: '报告已生成', description: '打开分析报告查看结果与下载文件。' },
    kb: { page: 'knowledge', label: '知识库构建', success: '知识库构建完成', description: '打开知识库查看构建结果。' },
    data_parse: { page: 'business', label: '数据解析', success: '数据解析完成', description: '打开业务数据查看解析结果。' },
    template_parse: { page: 'templates', label: '模板解析', success: '模板解析完成', description: '打开报告模板查看解析结果。' },
    vector_switch: { page: 'models', label: '向量模型切换', success: '向量模型切换完成', description: '打开模型连接查看向量模型状态。' },
  }[job.kind];
  if (!target) return null;
  return { ...target, title: job.status === 'FAILED' ? `${target.label}任务未完成` : job.status === 'DEGRADED' ? `${target.success}，部分内容需复核` : target.success };
}
