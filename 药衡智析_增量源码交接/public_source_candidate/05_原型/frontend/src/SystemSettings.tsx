import { Alert, Button, Segmented, Switch } from 'antd';
import { ReloadOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import { DEFAULT_UI_PREFERENCES, type UiPreferences } from './uiPreferences';

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
      <div className="setting-row"><div><h3>内容密度</h3><p>调整卡片、表格与导航的间距。</p></div><Segmented aria-label="内容密度" value={preferences.density} onChange={density => onChange({ density: density as UiPreferences['density'] })} options={[{ value: 'comfortable', label: '舒适' }, { value: 'compact', label: '紧凑' }]} /></div>
      <div className="setting-row"><div><h3>页面动效</h3><p>跟随系统偏好，或始终减少位移动画。</p></div><Segmented aria-label="页面动效" value={preferences.motion} onChange={motion => onChange({ motion: motion as UiPreferences['motion'] })} options={[{ value: 'system', label: '跟随系统' }, { value: 'reduce', label: '减少动态' }]} /></div>
      <div className="setting-row"><div><h3>默认分析口径</h3><p>立即应用，并在下次打开工作台时沿用。</p></div><Segmented aria-label="默认分析口径" value={preferences.defaultBasis} onChange={defaultBasis => onChange({ defaultBasis: defaultBasis as UiPreferences['defaultBasis'] })} options={[{ value: 'unit', label: '单位成本' }, { value: 'total', label: '总成本' }]} /></div>
      <div className="setting-row"><div><h3>任务完成提醒</h3><p>页面打开期间，每 5 秒检查报告任务；完成或失败后在页面内提醒。</p></div><Switch aria-label="任务完成提醒" checked={preferences.taskNotifications} onChange={taskNotifications => onChange({ taskNotifications })} /></div>
      <div className="settings-footer"><span>偏好保存在当前浏览器，不影响其他成员。</span><Button onClick={() => onChange({ ...DEFAULT_UI_PREFERENCES })}>恢复默认</Button></div>
    </section>
    <section className="panel settings-section">
      <div className="panel-heading"><h2>运行与连接</h2><Button icon={<ReloadOutlined />} onClick={onRefresh}>重新检测</Button></div>
      <dl className="runtime-diagnostics">
        <div><dt>部署方式</dt><dd>{status?.deployment?.label ?? '待检测'}</dd></div>
        <div><dt>应用服务</dt><dd>{health === 'online' ? '已连接' : health === 'offline' ? '连接失败' : '检测中'}</dd></div>
        <div><dt>网络探测</dt><dd>{status?.network?.status === 'reachable' ? '外网可达' : status?.network?.status === 'unreachable' ? '探测未通过' : '待检测'}<small>{status?.network?.detail ?? '尚未获得网络探测结果。'}</small></dd></div>
        <div><dt>数据更新时间</dt><dd>{status?.data?.updated_at ? new Date(status.data.updated_at).toLocaleString('zh-CN', { hour12: false }) : '尚无已发布数据'}<small>{status?.data?.basis ?? '完成数据解析后更新。'}</small></dd></div>
      </dl>
      <div className="setting-row"><div><h3>应用访问令牌</h3><p>用于连接受保护的应用服务；与模型 API 密钥分开。</p></div><Button icon={<SafetyCertificateOutlined />} onClick={onAccess}>配置令牌</Button></div>
    </section>
  </div>;
}
