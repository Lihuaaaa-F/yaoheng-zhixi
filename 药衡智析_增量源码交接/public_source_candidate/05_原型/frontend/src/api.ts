let accessToken = '';
export function setAccessToken(value: string) { accessToken = value.trim(); }
export function apiHeaders(json = false): Record<string, string> {
  return { ...(json ? { 'Content-Type': 'application/json' } : {}), ...(accessToken ? { 'X-API-Token': accessToken } : {}) };
}
export async function api<T = any>(path: string, body?: unknown, signal?: AbortSignal, method?: string): Promise<T> {
  const response = await fetch(`/api${path}`, { method: method ?? (body === undefined ? 'GET' : 'POST'), headers: apiHeaders(body !== undefined), body: body === undefined ? undefined : JSON.stringify(body), signal });
  if (response.status === 401 || response.status === 403) window.dispatchEvent(new Event('pharma:access-required'));
  const text = await response.text();
  let data: any;
  try { data = text ? JSON.parse(text) : null; }
  catch { throw new Error(`服务响应无法读取（HTTP ${response.status}），请稍后重试。`); }
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : data?.error?.message ?? `请求未完成（HTTP ${response.status}）`);
  return data;
}
export type Selection = {
  context_id: string; factory: string; product: string; month: string;
  analysis_type: 'monthly' | 'quarterly' | 'special'; basis: 'unit' | 'total'; topic?: string; benchmark_right?: string;
};
export const fmt = (value: unknown, digits = 2): string => {
  if (value === null || value === undefined || value === '') return '—';
  const n = Number(value); if (!Number.isFinite(n)) return String(value);
  const normalized = Object.is(n, -0) || (n !== 0 && Math.abs(n) < Math.pow(10, -digits) / 2 && n.toFixed(digits) === `-${(0).toFixed(digits)}`) ? 0 : n;
  return normalized.toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits });
};
export const pct = (value: unknown) => value === null || value === undefined ? '—' : `${Number(value) > 0 ? '+' : ''}${fmt(value)}%`;
export const contextQuery = (contextId: string) => `context_id=${encodeURIComponent(contextId)}`;
export type IndustryContext = { context_id: string; industry_id: string; industry_name: string; company_id: string; company_name: string; data_label?: string; capabilities?: unknown };

/** Fetch protected same-origin files without putting access tokens in URLs. */
export async function openApiFile(path: string, filename?: string, page?: number) {
  if (!path.startsWith('/api/')) throw new Error('文件地址不属于当前应用。');
  const response = await fetch(path, { headers: apiHeaders() });
  if (!response.ok) { if (response.status === 401 || response.status === 403) window.dispatchEvent(new Event('pharma:access-required')); throw new Error(`文件读取失败（HTTP ${response.status}）`); }
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement('a'); anchor.href = `${url}${page ? `#page=${page}` : ''}`;
  if (filename) anchor.download = filename; else { anchor.target = '_blank'; anchor.rel = 'noopener'; }
  anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 120000);
}
