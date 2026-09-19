import { useState } from 'react';
import { api } from './api';

const ROUTES: { key: string; label: string; hint: string }[] = [
  { key: 'narrative', label: '报告生成模型', hint: '用于报告解释与归因（大模型）。更换后新任务立即生效，旧报告保留原模型来源。' },
  { key: 'decision', label: '决策说明模型', hint: '轻量任务（决策依据选择等）。留空与主模型同源。' },
  { key: 'vector', label: '向量模型', hint: '当前为本地内置模型；更换向量模型需重建知识索引并验证后切换。' },
];

export default function ModelSettings() {
  const [status, setStatus] = useState<any>(null);
  const [draft, setDraft] = useState<Record<string, Record<string, string>>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [modelLists, setModelLists] = useState<Record<string, any>>({});

  const load = () => api('/settings/models').then((s: any) => {
    setStatus(s);
    const next: Record<string, Record<string, string>> = {};
    for (const route of ROUTES) {
      const c = s.connections?.[route.key] ?? {};
      next[route.key] = { model: c.model ?? '', base_url: c.base_url ?? '', protocol: c.protocol ?? 'openai', key_file: '', api_key: '' };
    }
    setDraft(next);
  }).catch(e => setError(e.message));
  useState(() => { void load(); });

  const save = async () => {
    setBusy(true); setError(''); setMessage('');
    try {
      const connections: Record<string, any> = {};
      for (const route of ROUTES) {
        const d = draft[route.key] ?? {};
        const entry: Record<string, string> = {};
        for (const f of ['model', 'base_url', 'protocol', 'key_file', 'api_key']) if (d[f]?.trim()) entry[f] = d[f].trim();
        if (Object.keys(entry).length) connections[route.key] = entry;
      }
      await api('/settings/models', { connections }, undefined, 'PUT');
      setMessage('已保存。新任务将使用新配置；旧报告保留原模型来源。');
      void load();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };

  const test = async (route: string) => {
    setBusy(true); setError('');
    try {
      const d = draft[route] ?? {};
      const overrides: Record<string, string> = {};
      for (const f of ['model', 'base_url', 'protocol', 'key_file']) if (d[f]?.trim()) overrides[f] = d[f].trim();
      const result = await api(`/settings/models/test?route=${route}`, overrides && Object.keys(overrides).length ? overrides : {});
      setTestResults(r => ({ ...r, [route]: result }));
    } catch (e: any) { setTestResults(r => ({ ...r, [route]: { status: 'FAILED', reason: e.message } })); }
    finally { setBusy(false); }
  };

  const listModels = async (route: string) => {
    setBusy(true);
    try {
      const d = draft[route] ?? {};
      const params = new URLSearchParams({ route });
      if (d.base_url?.trim()) params.set('base_url', d.base_url.trim());
      if (d.key_file?.trim()) params.set('key_file', d.key_file.trim());
      const result = await api(`/settings/models/list?${params}`);
      setModelLists(r => ({ ...r, [route]: result }));
    } catch (e: any) { setModelLists(r => ({ ...r, [route]: { status: 'UNAVAILABLE', reason: e.message } })); }
    finally { setBusy(false); }
  };

  const field = (route: string, name: string, label: string, placeholder = '', type = 'text') => <label>{label}
    <input type={type} value={draft[route]?.[name] ?? ''} placeholder={placeholder}
      onChange={e => setDraft(d => ({ ...d, [route]: { ...(d[route] ?? {}), [name]: e.target.value } }))} /></label>;

  return <div>
    <section className="panel">
      <h2>模型连接</h2>
      <p className="muted">API 与后台任务读取同一份配置；环境变量优先于页面设置。连接测试从后端发起一次真实短生成（含身份回显与 JSON 结构检查），不只是探测地址。</p>
      {status?.notes?.map((n: string, i: number) => <p key={i} className="muted" style={{ fontSize: 12 }}>· {n}</p>)}
      {error && <div className="error" role="alert">{error}</div>}
      {message && <div className="loading">{message}</div>}
      {ROUTES.map(route => <div key={route.key} style={{ borderTop: '1px solid var(--border)', padding: '16px 0' }}>
        <h3>{route.label} {status?.connections?.[route.key]?.configured && <span className="badge">已配置</span>} {status?.connections?.[route.key]?.key_set && <span className="badge">密钥已就绪</span>}</h3>
        <p className="muted" style={{ whiteSpace: 'normal' }}>{route.hint}</p>
        <div className="form-grid">
          {field(route.key, 'model', '模型名称', '如 glm-5.3-flash（获取失败可手填）')}
          {field(route.key, 'base_url', '服务地址（OpenAI 兼容）', 'https://…/v4')}
          <label>协议<select value={draft[route.key]?.protocol ?? 'openai'}
            onChange={e => setDraft(d => ({ ...d, [route.key]: { ...(d[route.key] ?? {}), protocol: e.target.value } }))}>
            <option value="openai">openai</option><option value="anthropic">anthropic</option>
          </select></label>
          {field(route.key, 'key_file', '密钥文件路径（可选）', 'C:\\keys\\provider.key')}
          {field(route.key, 'api_key', '密钥（保存后不回显）', '仅写入本机受限文件，不回显、不入库', 'password')}
        </div>
        <div className="button-row" style={{ marginTop: 10 }}>
          <button disabled={busy} onClick={() => listModels(route.key)}>获取模型列表</button>
          <button disabled={busy} onClick={() => test(route.key)}>测试连接（真实短生成）</button>
        </div>
        {modelLists[route.key] && (modelLists[route.key].status === 'OK'
          ? <p className="muted" style={{ marginTop: 8 }}>可选模型：{modelLists[route.key].models.slice(0, 12).join('、')}{modelLists[route.key].models.length > 12 ? ' …' : ''}</p>
          : <p className="muted" style={{ marginTop: 8 }}>{modelLists[route.key].hint ?? modelLists[route.key].reason}</p>)}
        {testResults[route.key] && <TestResult value={testResults[route.key]} />}
      </div>)}
      <div className="button-row" style={{ marginTop: 8 }}>
        <button className="primary" disabled={busy} onClick={save}>保存设置</button>
      </div>
    </section>
  </div>;
}

function TestResult({ value }: { value: any }) {
  const ok = value.status === 'PASS';
  return <div className={ok ? 'notice' : 'error'} style={{ marginTop: 10 }}>
    <strong>{ok ? '连接可用' : value.status === 'NO_KEY' ? '未配置密钥' : '连接失败'}</strong>
    {value.model && <> · 请求模型 {value.model}</>}
    {value.returned_model && <> · 响应回显 {value.returned_model}（{value.identity_status ?? '未核验'}）</>}
    {value.elapsed_seconds !== undefined && <> · 耗时 {value.elapsed_seconds}s</>}
    {value.structured_output === false && <> · 未返回JSON结构</>}
    {value.reason && <div style={{ marginTop: 4 }}>{value.reason}</div>}
  </div>;
}
