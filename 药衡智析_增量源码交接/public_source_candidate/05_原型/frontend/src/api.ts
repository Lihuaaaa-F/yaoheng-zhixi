export async function api<T = any>(path: string, body?: unknown, signal?: AbortSignal, method?: string): Promise<T> {
    const response = await fetch(`/api${path}`, { method: method ?? (body === undefined ? 'GET' : 'POST'), headers: body === undefined ? undefined : { 'Content-Type': 'application/json' }, body: body === undefined ? undefined : JSON.stringify(body), signal });
    const text = await response.text();
    let data: any;
    try { data = JSON.parse(text); }
    catch { throw new Error(response.ok ? '服务响应不完整，请重试并保留本次记录。' : `服务请求未完成（HTTP ${response.status}），请稍后重试并保留本次记录。`); }
    if (!response.ok)
        throw new Error(typeof data.detail === 'string' ? data.detail : data.error?.message ?? JSON.stringify(data.detail ?? data));
    return data;
}
export type Selection = {
    context_id: string;
    factory: string;
    product: string;
    month: string;
    analysis_type: 'monthly' | 'quarterly' | 'special';
    basis: 'unit' | 'total';
};
export const fmt = (value: unknown, digits = 2): string => {
    if (value === null || value === undefined || value === '') return 'N/A';
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    // 消除 -0/-0.00 类负零显示（四舍五入到 0 的极小负值按 0 呈现）
    const normalized = Object.is(n, -0) || (n !== 0 && Math.abs(n) < Math.pow(10, -digits) / 2 && n.toFixed(digits) === `-${(0).toFixed(digits)}`) ? 0 : n;
    return normalized.toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits });
};
export const pct = (value: unknown) => value === null || value === undefined ? 'N/A' : `${Number(value) > 0 ? '+' : ''}${fmt(value)}%`;

export const contextQuery = (contextId: string) => `context_id=${encodeURIComponent(contextId)}`;
export type IndustryContext = { context_id: string; industry_id: string; industry_name: string; company_id: string; company_name: string; data_label?: string; capabilities?: unknown };
