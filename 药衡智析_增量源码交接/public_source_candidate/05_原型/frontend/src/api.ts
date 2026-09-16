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
    factory: string;
    product: string;
    month: string;
    analysis_type: 'monthly' | 'quarterly' | 'special';
    basis: 'unit' | 'total';
};
export const fmt = (value: unknown, digits = 2): string => value === null || value === undefined || value === '' ? 'N/A' : Number.isFinite(Number(value)) ? Number(value).toLocaleString('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits }) : String(value);
export const pct = (value: unknown) => value === null || value === undefined ? 'N/A' : `${Number(value) > 0 ? '+' : ''}${fmt(value)}%`;
