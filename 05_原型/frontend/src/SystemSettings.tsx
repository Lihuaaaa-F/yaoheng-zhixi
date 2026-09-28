import { useEffect, useState } from 'react';
import { Alert, Button, Segmented, Switch } from 'antd';
import { ReloadOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { api } from './api';
import { DEFAULT_UI_PREFERENCES, type UiPreferences } from './uiPreferences';

/** 内网隔离开关（2026-09-24）：开启后后端模型网关仅接受本机/局域网端点，
 * 敏感数据不会发往外部模型 API；关闭后可接入外网模型（如 OpenAI）处理非敏感内容。 */
function NetworkIsolationSetting() {
  const [isolation, setIsolation] = useState<boolean | null>(null);
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    api('/settings/network', undefined, controller.signal)
      .then(value => { if (!controller.signal.aborted) setIsolation(Boolean(value.isolation)); })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
    return () => controller.abort();
  }, []);
  const toggle = async (next: boolean) => {
    setBusy(true); setError(''); setInfo('');
    try {
      const result = await api('/settings/network', { isolation: next }, undefined, 'PUT');
      setIsolation(Boolean(result.isolation));
      const blocked: string[] = result.blocked_routes ?? [];
      const routeLabels: Record<string, string> = { extraction: '资料抽取', analysis: '成本分析', assistant: '智能助手' };
      setInfo(next
        ? (blocked.length
          ? `已开启。以下路由当前配置的是外网端点，模型调用会被拦截：${blocked.map(route => routeLabels[route] ?? route).join('、')}；请改配内网端点或关闭隔离。`
          : '已开启。当前已配置的模型端点均为内网地址。')
        : '已关闭，允许调用外网模型。');
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  return <div className="setting-row"><div><h3>内网隔离</h3>
    <p>开启后仅允许本机或局域网模型。</p>
    {info && <p className="muted">{info}</p>}
    {error && <p className="error" role="alert">{error}</p>}
  </div><Switch aria-label="内网隔离" checked={Boolean(isolation)} disabled={busy || isolation === null} onChange={next => void toggle(next)} /></div>;
}

export default function SystemSettings({ preferences, onChange, storageWarning, status, health, onRefresh, onAccess }: {
  preferences: UiPreferences;
  onChange: (value: Partial<UiPreferences>) => void;
  storageWarning: boolean;
  status: any;
  health: 'loading' | 'online' | 'offline';
  onRefresh: () => void;
  onAccess: () => void;
}) {
  return <div className="system-settings">
    {storageWarning && <Alert type="warning" showIcon title="当前浏览器无法保存偏好；本次页面内仍会生效。" />}
    <section className="panel settings-section">
      <h2>阅读与交互</h2>
      <div className="setting-row"><div><h3>内容密度</h3></div><Segmented aria-label="内容密度" value={preferences.density} onChange={density => onChange({ density: density as UiPreferences['density'] })} options={[{ value: 'comfortable', label: '舒适' }, { value: 'compact', label: '紧凑' }]} /></div>
      <div className="setting-row"><div><h3>默认分析口径</h3></div><Segmented aria-label="默认分析口径" value={preferences.defaultBasis} onChange={defaultBasis => onChange({ defaultBasis: defaultBasis as UiPreferences['defaultBasis'] })} options={[{ value: 'unit', label: '单位成本' }, { value: 'total', label: '总成本' }]} /></div>
      <div className="setting-row"><div><h3>任务完成提醒</h3><p>任务完成或失败时在页面内提醒。</p></div><Switch aria-label="任务完成提醒" checked={preferences.taskNotifications} onChange={taskNotifications => onChange({ taskNotifications })} /></div>
      <div className="settings-footer"><span>仅在当前浏览器生效</span><Button onClick={() => onChange({ ...DEFAULT_UI_PREFERENCES })}>恢复默认</Button></div>
    </section>
    <section className="panel settings-section">
      <div className="panel-heading"><h2>运行与连接</h2><Button icon={<ReloadOutlined />} onClick={onRefresh}>重新检测</Button></div>
      <dl className="runtime-diagnostics">
        <div><dt>部署方式</dt><dd>{status?.deployment?.label ?? '待检测'}</dd></div>
        <div><dt>应用服务</dt><dd>{health === 'online' ? '已连接' : health === 'offline' ? '连接失败' : '检测中'}</dd></div>
        <div><dt>网络探测</dt><dd>{status?.network?.status === 'reachable' ? '外网可达' : status?.network?.status === 'unreachable' ? '探测未通过' : '待检测'}{status?.network?.status === 'unreachable' && status.network.detail && <small>{status.network.detail}</small>}</dd></div>
        <div><dt>数据更新时间</dt><dd>{status?.data?.updated_at ? new Date(status.data.updated_at).toLocaleString('zh-CN', { hour12: false }) : '尚无已发布数据'}</dd></div>
      </dl>
      <NetworkIsolationSetting />
      <div className="setting-row"><div><h3>应用访问令牌</h3><p>连接受保护服务，与模型密钥独立。</p></div><Button icon={<SafetyCertificateOutlined />} onClick={onAccess}>配置令牌</Button></div>
    </section>
  </div>;
}
