import { useEffect, useMemo, useState } from 'react';
import { api } from './api';

/** 模型配置共享表单：API/本地模型选项、厂商预填充（Base URL/模型型号）、
 * 密钥、推理强度滑块；选项联动——选本地则隐藏 API 密钥，选厂商则自动填充
 * 地址与协议、模型型号按档位过滤（提取=小模型、分析=大模型）。
 * 也可切换“手动填写”自由输入未收录模型。 */
export default function ModelConfigForm({ route }: { route: 'extraction' | 'analysis' }) {
  const [presets, setPresets] = useState<any>(null);
  const [status, setStatus] = useState<any>(null);
  const [mode, setMode] = useState<'api' | 'local'>('api');
  const [vendorId, setVendorId] = useState('');
  const [manual, setManual] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({
    model: '', base_url: '', protocol: 'openai', api_key: '', key_file: '', reasoning_effort: 'low',
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [modelList, setModelList] = useState<any>(null);

  const load = () => Promise.all([api('/settings/models'), api('/settings/models/presets')]).then(([s, p]: any[]) => {
    setStatus(s); setPresets(p);
    const c = s.connections?.[route] ?? {};
    const isLocal = /^https?:\/\/(localhost|127\.0\.0\.1|::1|host\.docker\.internal)/.test(c.base_url ?? '');
    setMode(c.base_url ? (isLocal ? 'local' : 'api') : 'api');
    setVendorId('');
    setManual(false);
    setForm({
      model: c.model ?? '', base_url: c.base_url ?? '', protocol: c.protocol ?? 'openai',
      api_key: '', key_file: '', reasoning_effort: c.reasoning_effort || 'low',
    });
  }).catch(e => setError(e instanceof Error ? e.message : String(e)));
  useEffect(() => { void load(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [route]);

  const rule = presets?.role_rules?.[route];
  const vendors = useMemo(() => {
    if (!presets) return [];
    return mode === 'local' ? presets.local_vendors ?? [] : presets.api_vendors ?? [];
  }, [presets, mode]);
  const vendor = vendors.find((v: any) => v.id === vendorId);
  const tierOptions = (vendor?.models ?? []).filter((m: any) => !rule || m.tier === rule.allowed_tier);
  const set = (key: string, value: string) => setForm(f => ({ ...f, [key]: value }));

  const pickVendor = (id: string) => {
    setVendorId(id);
    const target = vendors.find((v: any) => v.id === id);
    if (target) {
      setForm(f => ({ ...f, base_url: target.base_url, protocol: target.protocol ?? 'openai' }));
    }
  };
  const switchMode = (next: 'api' | 'local') => {
    setMode(next); setVendorId(''); setModelList(null);
    const list = next === 'local' ? presets?.local_vendors ?? [] : presets?.api_vendors ?? [];
    if (list[0]) pickVendorFrom(list, list[0].id);
  };
  const pickVendorFrom = (list: any[], id: string) => {
    setVendorId(id);
    const target = list.find((v: any) => v.id === id);
    if (target) setForm(f => ({ ...f, base_url: target.base_url, protocol: target.protocol ?? 'openai' }));
  };

  const tierWarning = useMemo(() => {
    if (!rule || !form.model) return '';
    const known = [...(presets?.api_vendors ?? []), ...(presets?.local_vendors ?? [])]
      .flatMap((v: any) => v.models ?? []).find((m: any) => m.id === form.model);
    if (!known) return '未收录型号（手动填写）：保存前建议先“测试连接”确认可用。';
    if (known.tier !== rule.allowed_tier) return `该型号为${known.tier === 'large' ? '旗舰/推理档' : '轻量档'}，不符合本角色要求（${route === 'extraction' ? '数据提取用小模型' : '数据分析用大模型'}），保存将被拒绝。`;
    return '';
  }, [form.model, presets, rule, route]);

  const save = async () => {
    setBusy(true); setError(''); setMessage('');
    try {
      const entry: Record<string, string> = {};
      for (const f of ['model', 'base_url', 'protocol', 'key_file', 'api_key', 'reasoning_effort', 'vendor'])
        if (form[f]?.trim() || (f === 'reasoning_effort')) entry[f] = form[f]?.trim() ?? 'low';
      if (!manual && vendorId) entry.vendor = mode === 'local' ? vendorId : vendorId;
      await api('/settings/models', { connections: { [route]: entry } }, undefined, 'PUT');
      setMessage('已保存。新任务将使用新配置；旧报告保留原模型来源。');
      void load();
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  const test = async () => {
    setBusy(true); setError('');
    try {
      const overrides: Record<string, string> = {};
      for (const f of ['model', 'base_url', 'protocol', 'reasoning_effort']) if (form[f]?.trim()) overrides[f] = form[f].trim();
      setTestResult(await api(`/settings/models/test?route=${route}`, overrides));
    } catch (e: any) { setTestResult({ status: 'FAILED', reason: e.message }); }
    finally { setBusy(false); }
  };
  const listModels = async () => {
    setBusy(true);
    try {
      const params = new URLSearchParams({ route });
      if (form.base_url?.trim()) params.set('base_url', form.base_url.trim());
      setModelList(await api(`/settings/models/list?${params}`));
    } catch (e: any) { setModelList({ status: 'UNAVAILABLE', reason: e.message }); }
    finally { setBusy(false); }
  };
  const effort = form.reasoning_effort || 'low';
  const effortIndex = { low: 0, medium: 1, high: 2 }[effort as 'low'] ?? 0;
  const current = status?.connections?.[route];

  return <section className="panel model-config">
    <h2>{rule?.label ?? route} {current?.configured && <span className="badge">已配置</span>} {current?.key_set && <span className="badge">密钥已就绪</span>}</h2>
    <p className="muted">{rule?.hint}</p>
    {error && <div className="error" role="alert">{error}</div>}
    {message && <div className="notice" role="status">{message}</div>}
    <div className="form-grid">
      <label>接入方式<div role="group" aria-label="接入方式" className="basis">
        <button aria-pressed={mode === 'api' && !manual} className={mode === 'api' && !manual ? 'selected' : ''} onClick={() => { setManual(false); switchMode('api'); }}>API 模型</button>
        <button aria-pressed={mode === 'local' && !manual} className={mode === 'local' && !manual ? 'selected' : ''} onClick={() => { setManual(false); switchMode('local'); }}>本地模型</button>
        <button aria-pressed={manual} className={manual ? 'selected' : ''} onClick={() => setManual(true)}>手动填写</button>
      </div></label>
      {!manual && <label>厂商 / 本地服务<select aria-label="厂商" value={vendorId} onChange={e => pickVendor(e.target.value)}>
        <option value="">（选择以自动填充地址）</option>
        {vendors.map((v: any) => <option key={v.id} value={v.id}>{v.label}</option>)}
      </select></label>}
      <label>模型名称<input aria-label="模型名称" list={`models-${route}`} value={form.model} onChange={e => set('model', e.target.value)} placeholder="可从下拉选择或手动输入" />
        <datalist id={`models-${route}`}>{tierOptions.map((m: any) => <option key={m.id} value={m.id}>{m.note}</option>)}</datalist></label>
      <label>API 根地址（Base URL）<input aria-label="Base URL" value={form.base_url} onChange={e => set('base_url', e.target.value)} placeholder={mode === 'local' ? 'http://127.0.0.1:11434/v1' : 'https://…/v4'} /></label>
      {mode === 'api' && !manual && <label>API 密钥<input aria-label="API 密钥" type="password" value={form.api_key} onChange={e => set('api_key', e.target.value)} placeholder={current?.key_set ? '已配置（留空保持不变）' : '仅写入本机受限文件，不回显'} /></label>}
      {mode === 'api' && !manual && <label>密钥文件路径（可选）<input aria-label="密钥文件路径" value={form.key_file} onChange={e => set('key_file', e.target.value)} placeholder="C:\keys\provider.key" /></label>}
      {mode === 'local' && !manual && <p className="muted form-hint">{presets?.local_key_hint ?? '本地服务通常无需密钥。'}</p>}
      <label>协议<select aria-label="协议" value={form.protocol} onChange={e => set('protocol', e.target.value)}><option value="openai">openai（兼容）</option><option value="anthropic">anthropic</option></select></label>
      <label className="effort-slider">推理强度
        <input type="range" min={0} max={2} step={1} value={effortIndex} aria-label="推理强度"
          onChange={e => set('reasoning_effort', ['low', 'medium', 'high'][Number(e.target.value)])} />
        <span className="effort-labels"><span>低</span><span>中</span><span>高</span></span>
        <span className="badge">{form.reasoning_effort === 'low' ? '低' : form.reasoning_effort === 'medium' ? '中' : '高'}</span>
      </label>
    </div>
    {tierWarning && <p className={tierWarning.includes('不符合') ? 'error' : 'muted'}>{tierWarning}</p>}
    {!manual && vendor && <div className="model-options">
      <p className="muted">推荐型号（已按{rule?.allowed_tier === 'small' ? '轻量' : '旗舰/推理'}档过滤）：</p>
      <div className="chips">{tierOptions.map((m: any) => <button key={m.id} className={`chip${form.model === m.id ? ' selected' : ''}`} onClick={() => set('model', m.id)}>{m.id}<small>{m.note}</small></button>)}</div>
      {vendor.key_url && <p className="muted">API Key 获取：<a href={vendor.key_url} target="_blank" rel="noreferrer">{vendor.key_url}</a></p>}
    </div>}
    <div className="button-row" style={{ marginTop: 10 }}>
      <button disabled={busy} onClick={listModels}>获取模型列表</button>
      <button disabled={busy} onClick={test}>测试连接（真实短生成）</button>
      <button className="primary" disabled={busy} onClick={save}>保存设置</button>
    </div>
    {modelList && (modelList.status === 'OK'
      ? <p className="muted" style={{ marginTop: 8 }}>端点模型：{(modelList.models ?? []).slice(0, 12).join('、')}{modelList.models?.length > 12 ? ' …' : ''}</p>
      : <p className="muted" style={{ marginTop: 8 }}>{modelList.hint ?? modelList.reason}</p>)}
    {testResult && <div className={testResult.status === 'PASS' ? 'notice' : 'error'} style={{ marginTop: 10 }}>
      <strong>{testResult.status === 'PASS' ? '连接可用' : testResult.status === 'NO_KEY' ? '未配置密钥' : '连接失败'}</strong>
      {testResult.model && <> · 请求模型 {testResult.model}</>}
      {testResult.returned_model && <> · 响应回显 {testResult.returned_model}（{testResult.identity_status ?? '未核验'}）</>}
      {testResult.elapsed_seconds !== undefined && <> · 耗时 {testResult.elapsed_seconds}s</>}
      {testResult.reason && <div style={{ marginTop: 4 }}>{testResult.reason}</div>}
    </div>}
  </section>;
}
