import { useEffect, useMemo, useState } from 'react';
import { Alert, Button, Form, Input, InputNumber, Select, Space, Tag, Collapse, Switch } from 'antd';
import { ApiOutlined, CheckCircleOutlined, SaveOutlined } from '@ant-design/icons';
import { api } from './api';

type Route = 'extraction' | 'analysis' | 'assistant';
const LABELS: Record<Route, string> = { extraction: '数据提取模型', analysis: '分析与报告模型', assistant: 'AI 助手独立模型' };
// 推理强度三挡（2026-09-24 收窄）：历史 8 挡实际使用中易选错，收敛为 低/中/高 + 模型默认；
// 旧档位（none/minimal/xhigh/max）由后端读取时自动归一化。
const EFFORTS = [ ['', '由模型默认决定'], ['low', '低'], ['medium', '中'], ['high', '高'] ];
const initial = { model: '', base_url: '', protocol: 'openai', api_key: '', key_file: '', reasoning_effort: '', temperature: undefined as number | undefined, top_p: undefined as number | undefined, max_tokens: undefined as number | undefined, timeout_seconds: undefined as number | undefined, auth_mode: 'auto', clear_api_key: false };

/** Keys are ephemeral input state. Saving/testing sends only the chosen route; no browser persistence. */
export default function ModelConfigForm({ route, onSaved }: { route: Route; onSaved?: () => void }) {
  const [form, setForm] = useState(initial);
  const [contextWindow,setContextWindow]=useState<number|undefined>(undefined);
  const [presets, setPresets] = useState<any>(null), [current, setCurrent] = useState<any>(null);
  const [vendor, setVendor] = useState(''), [busy, setBusy] = useState(''), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [result, setResult] = useState<any>(null), [models, setModels] = useState<string[]>([]);
  const load = async (signal?: AbortSignal) => {
    const [status, options] = await Promise.all([api('/settings/models', undefined, signal), api('/settings/models/presets', undefined, signal)]);
    const c = status.connections?.[route] ?? {};
    setCurrent(c); setPresets(options); setVendor(c.vendor ?? ''); setContextWindow(c.model_context_windows?.[c.model]??undefined);
    setForm({ ...initial, ...Object.fromEntries(Object.keys(initial).filter(k => !['api_key', 'key_file', 'clear_api_key'].includes(k)).map(k => [k, c[k] ?? (initial as any)[k]])) });
  };
  useEffect(() => { const controller = new AbortController(); setError(''); setResult(null); setNotice(''); void load(controller.signal).catch(e => { if (!controller.signal.aborted) setError(e.message); }); return () => { controller.abort(); }; }, [route]);
  const vendors = useMemo(() => [...(presets?.api_vendors ?? []), ...(presets?.local_vendors ?? [])], [presets]);
  const modelOptions = useMemo(() => [...new Set([...models, ...(vendors.find(v => v.id === vendor)?.models ?? []).map((m: any) => m.id)])], [models, vendors, vendor]);
  const set = (key: keyof typeof initial, value: any) => { if(key==='model')setContextWindow(current?.model_context_windows?.[value]??undefined);setForm(previous => ({ ...previous, [key]: value })); };
  const payload = () => {
    const entry: Record<string, unknown> = { model: form.model.trim(), base_url: form.base_url.trim(), protocol: form.protocol, reasoning_effort: form.reasoning_effort, auth_mode: form.auth_mode };
    for (const key of ['temperature', 'top_p', 'max_tokens', 'timeout_seconds'] as const) entry[key] = form[key] ?? null;
    if (form.api_key.trim()) entry.api_key = form.api_key.trim();
    if (form.key_file.trim()) entry.key_file = form.key_file.trim();
    if (form.clear_api_key) entry.clear_api_key = true;
    if (vendor) entry.vendor = vendor;
    if(form.model.trim())entry.model_context_windows={[form.model.trim()]:contextWindow??null};
    return entry;
  };
  const run = async (action: 'save' | 'test' | 'list') => {
    setBusy(action); setError(''); setNotice('');
    try {
      if (action === 'save') {
        await api('/settings/models', { connections: { [route]: payload() } }, undefined, 'PUT');
        await load(); setNotice('设置已保存，将用于后续新任务。其他模型连接保持不变。'); window.dispatchEvent(new Event('pharma:model-saved')); onSaved?.();
      } else if (action === 'test') setResult(await api(`/settings/models/test?route=${route}`, payload()));
      else {
        const response = await api(`/settings/models/list?route=${route}`, payload());
        if (response.status === 'OK' || response.models?.length) { setModels(response.models.map((m: any) => typeof m === 'string' ? m : m.id)); setNotice(`读取到 ${response.models.length} 个模型，可复制名称或继续手动输入。`); }
        else setError(response.hint ?? response.reason ?? '此端点未提供模型列表，请手动填写模型名称。');
      }
    } catch (e: any) { setError(e.message); } finally { setBusy(''); }
  };
  return <section className="panel model-config">
    <div className="panel-heading"><h2>{LABELS[route]}</h2><Space>{current?.configured && <Tag color="cyan">已配置</Tag>}{current?.key_set && <Tag icon={<CheckCircleOutlined />}>密钥已保存</Tag>}</Space></div>
    <p className="muted">{route === 'assistant' ? '助手有独立的连接、密钥和推理参数。未配置时使用本地确定性查询，不继承报告模型密钥。' : '可选择任意兼容模型。厂商与型号仅提供填写建议，不限制模型档位。'}</p>
    {error && <Alert type="error" showIcon title={error} closable onClose={() => setError('')} />}
    {notice && <Alert type="success" showIcon title={notice} />}
    {current?.parameter_warnings?.map((warning: any, i: number) => <Alert key={i} type="warning" showIcon title={typeof warning === 'string' ? warning : warning.message} />)}
    {current?.configured && current?.effective?.model && <p className="muted">当前生效型号：{current.effective.model}。修改表单后，保存才会用于新任务。</p>}
    <Form layout="vertical" className="model-form" onFinish={() => run('save')}>
      <Form.Item label="快速填写厂商或本地服务"><Select value={vendor || undefined} allowClear placeholder="也可以直接填写下方连接" options={vendors.map(v => ({ value: v.id, label: v.label }))} onChange={id => { setVendor(id ?? ''); const v = vendors.find(v => v.id === id); if (v) setForm(f => ({ ...f, base_url: v.base_url, protocol: v.protocol ?? 'openai' })); }} /></Form.Item>
      <div className="form-grid">
        <Form.Item label="模型名称" required><Input aria-label="模型名称" list={`models-${route}`} value={form.model} onChange={e => set('model', e.target.value)} placeholder="如 glm-5.3；支持自由输入" autoComplete="off" /><datalist id={`models-${route}`}>{modelOptions.map(model => <option key={model} value={model} />)}</datalist></Form.Item>
        <Form.Item label="接口协议"><Select aria-label="协议" value={form.protocol} onChange={v => set('protocol', v)} options={[{ value: 'openai', label: 'OpenAI 兼容' }, { value: 'anthropic', label: 'Anthropic' }]} /></Form.Item>
      </div>
      <Form.Item label="API 根地址（Base URL）" required extra="本地 Ollama、vLLM、LM Studio 使用其兼容 API 地址。Docker 内的本机服务请使用 host.docker.internal。"><Input aria-label="Base URL" value={form.base_url} onChange={e => set('base_url', e.target.value)} placeholder="https://…/v1 或 http://localhost:11434/v1" autoComplete="off" /></Form.Item>
      <Form.Item label={route === 'assistant' ? '助手 API 密钥' : 'API 密钥'} extra="仅发送到当前应用后端并保存至受控文件；不回显、不进入对话或浏览器持久存储。留空保留已保存密钥。"><Input.Password aria-label="API 密钥" value={form.api_key} onChange={e => set('api_key', e.target.value)} placeholder={current?.key_set ? '已保存，留空保持' : '无需鉴权的本地服务可留空'} autoComplete="new-password" /></Form.Item>
      <div className="form-grid">
        <Form.Item label="鉴权方式"><Select value={form.auth_mode} onChange={v => set('auth_mode', v)} options={[{ value: 'auto', label: '自动识别' }, { value: 'required', label: '必须提供密钥' }, { value: 'none', label: '无需密钥（本地服务）' }]} /></Form.Item>
        <Form.Item label="推理强度"><Select aria-label="推理强度" value={form.reasoning_effort} options={EFFORTS.map(([value, label]) => ({ value, label }))} onChange={v => set('reasoning_effort', v)} /></Form.Item>
      </div>
      <p className="muted">推理强度由厂商适配器映射；不支持的参数会明确提示。默认值不额外发送推理强度。</p>
      <Collapse items={[{ key: 'parameters', label: '生成参数与密钥文件', children: <>
        <div className="form-grid">
          <Form.Item label="温度 temperature"><InputNumber min={0} max={2} step={0.1} value={form.temperature} onChange={v => set('temperature', v ?? undefined)} placeholder="模型默认" /></Form.Item>
          <Form.Item label="采样范围 top_p"><InputNumber min={0} max={1} step={0.05} value={form.top_p} onChange={v => set('top_p', v ?? undefined)} placeholder="模型默认" /></Form.Item>
          <Form.Item label="最大输出 token"><InputNumber min={1} max={32768} value={form.max_tokens} onChange={v => set('max_tokens', v ?? undefined)} placeholder="服务默认" /></Form.Item>
          <Form.Item label="请求超时（秒）"><InputNumber min={5} max={180} value={form.timeout_seconds} onChange={v => set('timeout_seconds', v ?? undefined)} placeholder="服务默认" /></Form.Item>
        </div>
        <Form.Item label="当前型号上下文窗口（tokens，可选）" extra="按服务商文档填写；留空显示未知。此值仅适用于当前模型名称，不会自动套用到其他型号。"><InputNumber aria-label="当前型号上下文窗口" min={1024} max={2000000} value={contextWindow} onChange={value=>setContextWindow(value??undefined)} placeholder="未知"/></Form.Item>
        <Form.Item label="受控密钥文件名（可选）" extra="仅填写后端受控目录中的文件名，例如 assistant.key。留空保留现有密钥；不接受完整路径。"><Input value={form.key_file} onChange={e => set('key_file', e.target.value)} placeholder="assistant.key" /></Form.Item>
        <Space><Switch checked={form.clear_api_key} onChange={v => set('clear_api_key', v)} /><span>保存时解除此连接的已存密钥引用</span></Space>
      </> }]} />
      <div className="button-row model-actions"><Button icon={<ApiOutlined />} loading={busy === 'list'} disabled={!!busy} onClick={() => run('list')}>读取模型列表</Button><Button loading={busy === 'test'} disabled={!!busy} onClick={() => run('test')}>测试连接</Button><Button type="primary" icon={<SaveOutlined />} htmlType="submit" loading={busy === 'save'} disabled={!!busy}>保存设置</Button></div>
      <p className="muted">测试连接会使用当前填写的连接发起一次短请求，可能计入厂商用量；保存不会发起模型生成。</p>
    </Form>
    {result && <Alert showIcon type={result.status === 'PASS' ? 'success' : 'error'} title={result.status === 'PASS' ? '连接测试通过' : '连接测试未通过'} description={<><p>{result.reason ?? `${result.returned_model ?? result.model ?? form.model}${result.elapsed_seconds !== undefined ? ` · ${result.elapsed_seconds} 秒` : ''}`}</p>{result.parameter_warnings?.map((w: any, i: number) => <p key={i}>{typeof w === 'string' ? w : w.message}</p>)}</>} />}
  </section>;
}
