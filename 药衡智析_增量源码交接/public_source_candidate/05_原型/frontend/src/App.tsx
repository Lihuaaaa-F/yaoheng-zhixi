import { lazy, Suspense, useState, useEffect, useCallback, useRef, type CSSProperties } from 'react';
import { Alert, Badge, Button, Drawer, Empty, Input, Menu, Modal, Select, Segmented, Spin, Tooltip, notification } from 'antd';
import { ApartmentOutlined, BarChartOutlined, BookOutlined, CheckSquareOutlined, ClockCircleOutlined, DatabaseOutlined, DesktopOutlined, FileTextOutlined, MenuFoldOutlined, MenuUnfoldOutlined, MessageOutlined, SettingOutlined, SwapOutlined, UploadOutlined, WifiOutlined } from '@ant-design/icons';
import { api, Selection, IndustryContext, contextQuery, setAccessToken } from './api';
import { Catalog, Snapshot, BenchmarkData } from './types';
import { useJobsActions } from './hooks';
import Analysis from './Analysis';
import { EvidenceDrawer } from './Evidence';
import AssistantDock from './AssistantDock';
import ModelConfigForm from './ModelConfigForm';
import { ExtractionModel, AnalysisModel, VectorModel } from './ModelPages';
import SystemSettings from './SystemSettings';
import { readUiPreferences, saveUiPreferences, type UiPreferences } from './uiPreferences';
const ProductMonthHeatmap = lazy(() => import('./ProductMonthHeatmap'));
const Benchmark = lazy(() => import('./Benchmark'));
const DecisionCard = lazy(() => import('./DecisionCard'));
const BusinessData = lazy(() => import('./BusinessData'));
const KnowledgeData = lazy(() => import('./KnowledgeData'));
const TemplateCenter = lazy(() => import('./TemplateCenter'));
const ReportGeneration = lazy(() => import('./ReportGeneration'));
const Rectification = lazy(() => import('./Rectification'));

const PAGES = [
  { key: 'analysis', title: '成本分析', group: '分析决策', icon: <BarChartOutlined />, intro: '从成本变化出发，核对数据、证据与可执行的建议。' },
  { key: 'benchmark', title: '跨厂对标', group: '分析决策', icon: <SwapOutlined />, intro: '同产品、同规格、同期间，依次找差异、拆结构、查原因。' },
  { key: 'reports', title: '分析报告', group: '分析决策', icon: <FileTextOutlined />, intro: '生成并核验正式报告，下载 Word 与 PDF。' },
  { key: 'actions', title: '问题整改', group: '分析决策', icon: <CheckSquareOutlined />, intro: '将建议转为整改草稿，确认下发并追踪送达和处理状态。' },
  { key: 'business', title: '业务数据', group: '数据中心', icon: <DatabaseOutlined />, intro: '导入成本汇总、明细与预算，完成校验后进入分析。' },
  { key: 'knowledge', title: '知识库', group: '数据中心', icon: <BookOutlined />, intro: '管理企业知识资料，检索并核对分析依据。' },
  { key: 'templates', title: '报告模板', group: '数据中心', icon: <FileTextOutlined />, intro: '维护月度、季度和专题报告模板。' },
  { key: 'models', title: '模型连接', group: '模型与设置', icon: <ApartmentOutlined />, intro: '分别配置分析、提取、向量检索和右侧助手所用模型。' },
  { key: 'settings', title: '系统设置', group: '模型与设置', icon: <SettingOutlined />, intro: '调整阅读偏好，检查应用与网络连接。' },
];
const ANALYSIS_SECTIONS = [
  ['g-overview', '概览'], ['g-trend', '趋势与预测'], ['g-focus', '重点分析'], ['g-bridge', '变动拆解'],
  ['g-drill', '原始明细'], ['g-explain', '解释与建议'], ['g-industry', '行业参考'],
];
const MODEL_TABS = [{ key: 'analysis', label: '分析与报告' }, { key: 'extraction', label: '数据提取' }, { key: 'assistant', label: '对话助手' }, { key: 'vector', label: '向量检索' }];
const initialSelection: Selection = { context_id: '', factory: '', product: '', month: '', analysis_type: 'monthly', basis: 'unit' };
function readLocation() {
  const q = new URLSearchParams(window.location.search);
  const page = PAGES.some(p => p.key === q.get('page')) ? q.get('page')! : 'analysis';
  const selection: Selection = { ...initialSelection, ...Object.fromEntries(['factory', 'product', 'month', 'topic'].flatMap(k => q.has(k) ? [[k, q.get(k)!]] : [])), analysis_type: ['monthly', 'quarterly', 'special'].includes(q.get('analysis_type') ?? '') ? q.get('analysis_type') as Selection['analysis_type'] : 'monthly', basis: q.has('basis') ? q.get('basis') === 'total' ? 'total' : 'unit' : readUiPreferences().defaultBasis };
  return { page, selection, left: q.get('left') ?? '', right: q.get('right') ?? '', modelTab:['analysis','extraction','assistant','vector'].includes(q.get('model_route')??'')?q.get('model_route')!:'analysis' };
}
function urlFor(page: string, selection: Selection, left: string, right: string) {
  const q = new URLSearchParams({ page });
  for (const [key, value] of Object.entries({ ...selection, left, right })) if (value && key !== 'context_id') q.set(key, String(value));
  return `${window.location.pathname}?${q.toString()}`;
}

export default function App() {
  const [location] = useState(readLocation), [page, setPage] = useState(location.page);
  const [activeContext, setActiveContext] = useState<IndustryContext | null>(null), [contextId, setContextId] = useState('');
  const [workspaceLoading, setWorkspaceLoading] = useState(true);
  const [workspaceRevision, setWorkspaceRevision] = useState(0);
  const workspaceLoaded = useRef(false);
  const [workspaceState, setWorkspaceState] = useState<{ status: string; issues: { message: string; filename?: string }[]; pending_files: number; dataVersion: string }>({ status: 'EMPTY', issues: [], pending_files: 0, dataVersion: '' });
  const [catalog, setCatalog] = useState<Catalog | null>(null), [selection, setSelection] = useState(location.selection);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null), [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [left, setLeft] = useState(location.left), [right, setRight] = useState(location.right);
  const [error, setError] = useState(''), [analysisLoading, setAnalysisLoading] = useState(false), [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [drawer, setDrawer] = useState<any>(null), [reload, setReload] = useState(0), [health, setHealth] = useState<'loading' | 'online' | 'offline'>('loading');
  const [assistantOpen, setAssistantOpen] = useState(false), [assistantWidth, setAssistantWidth] = useState(360), [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(window.innerWidth < 1100), [navOpen, setNavOpen] = useState(false);
  const [systemStatus,setSystemStatus]=useState<any>(null);
  const [accessOpen, setAccessOpen] = useState(false), [token, setToken] = useState(''), [modelTab, setModelTab] = useState(location.modelTab);
  const [preferences, setPreferences] = useState(readUiPreferences), [storageWarning, setStorageWarning] = useState(false);
  const [activeSection, setActiveSection] = useState('g-overview');
  const contentRef = useRef<HTMLDivElement>(null), scrollRef = useRef<HTMLDivElement>(null);
  const previousJobs = useRef(new Map<string, string>());
  const [notifications, notificationHolder] = notification.useNotification();
  const pageInfo = PAGES.find(p => p.key === page)!;
  const inWorkspace = pageInfo.group === '分析决策', currentContext = useRef(contextId); currentContext.current = contextId;
  const { jobs, actions, refresh, jobsError } = useJobsActions(page === 'reports' || page === 'actions' || preferences.taskNotifications ? 2 : -1, contextId, page === 'reports' || page === 'actions' ? 2000 : 5000);
  const selectionRef = useRef(selection); selectionRef.current = selection;
  const navigate = (next: string) => { if (next !== page) { window.history.pushState(null, '', urlFor(next, selection, left, right)); setPage(next); } setNavOpen(false); };
  const changeSelection = (next: Partial<Selection>) => { const value = { ...selection, ...next }; window.history.pushState(null, '', urlFor(page, value, left, right)); setSelection(value); if (value.context_id !== contextId) setContextId(value.context_id); };
  useEffect(() => {const url=new URL(urlFor(page,selection,left,right),window.location.origin);if(page==='models')url.searchParams.set('model_route',modelTab);window.history.replaceState(null,'',url.pathname+url.search);},[page,selection,left,right,modelTab]);
  useEffect(() => { const pop = () => { const value = readLocation(); setPage(value.page); setSelection({ ...value.selection, context_id: currentContext.current }); setLeft(value.left); setRight(value.right); setModelTab(value.modelTab); }; window.addEventListener('popstate', pop); return () => window.removeEventListener('popstate', pop); }, []);
  useEffect(() => { setStorageWarning(!saveUiPreferences(preferences)); }, [preferences]);
  useEffect(() => {
    document.documentElement.dataset.density = preferences.density;
  }, [preferences.density]);
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: 'instant' });
    setActiveSection('g-overview');
    const content = contentRef.current;
    if (!content) return;
    const animation = content.animate([{ opacity: 0.3, transform: 'translateY(5px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: 190, easing: 'cubic-bezier(.22,.75,.2,1)' });
    return () => animation.cancel();
  }, [page, modelTab]);
  useEffect(() => { previousJobs.current = new Map(); }, [contextId, preferences.taskNotifications]);
  useEffect(() => {
    for (const job of jobs) {
      const previous = previousJobs.current.get(job.id);
      if (preferences.taskNotifications && previous && previous !== job.status && ['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(job.status)) {
        notifications.open({ key: job.id, title: job.status === 'FAILED' ? '报告任务未完成' : job.status === 'DEGRADED' ? '报告已生成，部分内容需复核' : '报告已生成', description: '打开分析报告查看结果与下载文件。', duration: 7, onClick: () => navigate('reports') });
      }
      previousJobs.current.set(job.id, job.status);
    }
  }, [jobs, preferences.taskNotifications, notifications]);
  useEffect(() => { const resize = () => setMobile(window.innerWidth < 1100); window.addEventListener('resize', resize); return () => window.removeEventListener('resize', resize); }, []);
  useEffect(() => {
    const changed = () => setWorkspaceRevision(value => value + 1);
    window.addEventListener('pharma:data-changed', changed);
    window.addEventListener('focus', changed);
    return () => { window.removeEventListener('pharma:data-changed', changed); window.removeEventListener('focus', changed); };
  }, []);
  useEffect(() => { const required = () => setAccessOpen(true); window.addEventListener('pharma:access-required', required); return () => window.removeEventListener('pharma:access-required', required); }, []);
  useEffect(() => {
    const controller = new AbortController();
    const check = () => fetch('/health', { signal: controller.signal }).then(response => { if (!controller.signal.aborted) setHealth(response.ok ? 'online' : 'offline'); }).catch(() => { if (!controller.signal.aborted) setHealth('offline'); });
    void check(); const timer = setInterval(check, 30000); return () => { controller.abort(); clearInterval(timer); };
  }, [reload]);
  useEffect(()=>{const c=new AbortController();const poll=()=>api(`/system/status?${contextQuery(contextId)}`,undefined,c.signal).then(setSystemStatus).catch(()=>{if(!c.signal.aborted)setSystemStatus(null)});void poll();const timer=setInterval(poll,60000);return()=>{c.abort();clearInterval(timer)}},[contextId,reload]);
  useEffect(() => {
    const c = new AbortController(); if (!workspaceLoaded.current) setWorkspaceLoading(true);
    api('/workspace', undefined, c.signal).then(x => {
      if (c.signal.aborted) return;
      setActiveContext(x.context ?? null); setContextId(x.context_id ?? '');
      setWorkspaceState({ status: x.status ?? 'EMPTY', issues: x.issues ?? [], pending_files: x.pending_files ?? 0, dataVersion: typeof x.data_snapshot === 'string' ? x.data_snapshot : JSON.stringify(x.data_snapshot ?? null) });
    }).catch(e => { if (!c.signal.aborted) { setError(e.message); setContextId(''); setActiveContext(null); } }).finally(() => { if (!c.signal.aborted) { workspaceLoaded.current = true; setWorkspaceLoading(false); } });
    return () => c.abort();
  }, [reload, workspaceRevision]);
  useEffect(() => {
    if (!contextId) { setCatalog(null); setSnapshot(null); setBenchmark(null); return; }
    const c = new AbortController(); setCatalog(null); setSnapshot(null); setBenchmark(null); setDrawer(null); setError('');
    api(`/catalog?${contextQuery(contextId)}`, undefined, c.signal).then(x => {
      if (c.signal.aborted) return;
      const previous = selectionRef.current, same = !previous.context_id || previous.context_id === contextId;
      let selectedMonth=same&&x.months.includes(previous.month)?previous.month:x.months.at(-1)??'';
      if(same&&previous.analysis_type==='quarterly'&&!['03','06','09','12'].includes(selectedMonth.slice(-2)))selectedMonth=x.months.filter((value:string)=>['03','06','09','12'].includes(value.slice(-2))).at(-1)??selectedMonth;
      setSelection({ ...initialSelection, basis: preferences.defaultBasis, ...(same ? previous : {}), context_id: contextId, factory: same && x.factories.includes(previous.factory) ? previous.factory : x.factories[0] ?? '', product: same && x.products.includes(previous.product) ? previous.product : x.products[0] ?? '', month:selectedMonth });
      setLeft(value => x.factories.includes(value) ? value : x.factories[0] ?? ''); setRight(value => x.factories.includes(value) ? value : x.factories[1] ?? ''); setCatalog(x);
    }).catch(e => { if (!c.signal.aborted) setError(e.message); }); return () => c.abort();
  }, [contextId, reload, workspaceState.dataVersion]);
  const { factory, product, month, analysis_type, basis } = selection;
  const snapshotPage = ['analysis', 'reports', 'actions'].includes(page);
  useEffect(() => {
    if (workspaceState.status !== 'READY') { setSnapshot(null); setAnalysisLoading(false); return; }
    if (workspaceLoading || workspaceState.status !== 'READY' || !snapshotPage || !catalog || selection.context_id !== contextId || !selection.factory || !selection.product || !selection.month) return;
    const c = new AbortController(); setAnalysisLoading(true); setError(''); setSnapshot(null);
    api('/analyses', selection, c.signal).then(x => { if (!c.signal.aborted) setSnapshot(x); }).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setAnalysisLoading(false); }); return () => c.abort();
  }, [snapshotPage, catalog, contextId, selection, reload, workspaceLoading, workspaceState.status]);
  useEffect(() => {
    if (workspaceState.status !== 'READY') { setBenchmark(null); setBenchmarkLoading(false); return; }
    if (workspaceLoading || workspaceState.status !== 'READY' || page !== 'benchmark' || !catalog || selection.context_id !== contextId || !left || !right || left === right) return;
    const c = new AbortController(); setBenchmarkLoading(true); setError(''); setBenchmark(null);
    const params = new URLSearchParams({ context_id: contextId, product, month, left, right, analysis_type, basis, explain: 'async' });
    api(`/benchmarks?${params}`, undefined, c.signal).then(x => { if (!c.signal.aborted) setBenchmark(x); }).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setBenchmarkLoading(false); }); return () => c.abort();
  }, [page, catalog, contextId, product, month, left, right, analysis_type, basis, reload, workspaceLoading, workspaceState.status]);
  const closeDrawer = useCallback(() => setDrawer(null), []);
  const changeRange = (kind: Selection['analysis_type']) => {
    const ends = catalog?.months.filter(m => ['03', '06', '09', '12'].includes(m.slice(-2))) ?? [];
    const quarterEnd = `${month.slice(0, 4)}-${String(Math.ceil(Number(month.slice(-2)) / 3) * 3).padStart(2, '0')}`;
    changeSelection({ analysis_type: kind, month: kind === 'quarterly' ? ends.includes(quarterEnd) ? quarterEnd : ends.at(-1) ?? month : month });
  };
  const onPublished = () => { setWorkspaceLoading(true); setSnapshot(null); setBenchmark(null); navigate('analysis'); setReload(n => n + 1); };
  const onError = (message: string) => { if (currentContext.current === contextId) setError(message); };
  const nav = <Menu mode="inline" selectedKeys={[page]} inlineCollapsed={!mobile && collapsed} onClick={({ key }) => navigate(key)} items={['分析决策', '数据中心', '模型与设置'].map(group => ({ type: 'group', key: group, label: collapsed && !mobile ? undefined : group, children: PAGES.filter(p => p.group === group).map(p => ({ key: p.key, icon: p.icon, label: p.title, title: p.title })) }))} />;
  const assistant = <AssistantDock selection={page==='benchmark'?{...selection,factory:left,...(right?{benchmark_right:right}:{})}:selection} onConfigure={()=>{setModelTab('assistant');navigate('models');setAssistantOpen(false)}} onClose={() => setAssistantOpen(false)} onEvidence={setDrawer} onApplied={value => { void refresh().catch(e=>onError(e.message)); if (value.job_id) navigate('reports'); else if (value.action_id) navigate('actions'); }} />;
  const resizeAssistant = (event: React.PointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId); const start = event.clientX, width = assistantWidth;
    const move = (e: PointerEvent) => setAssistantWidth(Math.min(500, Math.max(320, width + start - e.clientX)));
    const stop = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', stop); window.removeEventListener('pointercancel', stop); };
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', stop, { once: true }); window.addEventListener('pointercancel', stop, { once: true });
  };
  const changePreferences = (update: Partial<UiPreferences>) => {
    setPreferences(previous => ({ ...previous, ...update }));
    if (update.defaultBasis) changeSelection({ basis: update.defaultBasis });
  };
  const jumpToSection = (id: string) => {
    const section = document.getElementById(id), scroll = scrollRef.current;
    if (!section || !scroll) return;
    if (section instanceof HTMLDetailsElement) section.open = true;
    setActiveSection(id);
    const top = section.getBoundingClientRect().top - scroll.getBoundingClientRect().top + scroll.scrollTop - 4;
    scroll.scrollTo({ top, behavior: 'smooth' });
  };
  const trackSection = () => {
    if (page !== 'analysis') return;
    const scroll = scrollRef.current;
    if (!scroll) return;
    const threshold = scroll.getBoundingClientRect().top + 70;
    let current = ANALYSIS_SECTIONS[0][0];
    for (const [id] of ANALYSIS_SECTIONS) {
      const section = document.getElementById(id);
      if (section && section.getBoundingClientRect().top <= threshold) current = id;
    }
    setActiveSection(previous => previous === current ? previous : current);
  };
  const statusContent = <div className="sidebar-runtime" aria-label="运行状态">
    <Tooltip title={systemStatus?.deployment?.label ?? '运行环境检测中'}><div><DesktopOutlined /><span>{systemStatus?.deployment?.label ?? '环境检测中'}</span></div></Tooltip>
    <Tooltip title={systemStatus?.network?.detail ?? '网络状态待检测'}><div><WifiOutlined /><span>{systemStatus?.network?.status === 'reachable' ? '外网可达' : systemStatus?.network?.status === 'unreachable' ? '外网探测失败' : '网络待检测'}</span><Badge status={systemStatus?.network?.status === 'reachable' ? 'success' : systemStatus?.network?.status === 'unreachable' ? 'warning' : 'default'} /></div></Tooltip>
    <Tooltip title={systemStatus?.data?.basis ?? '完成数据解析后更新'}><div><ClockCircleOutlined /><span>{systemStatus?.data?.updated_at ? `更新 ${new Date(systemStatus.data.updated_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false })}` : '尚无数据更新'}</span></div></Tooltip>
    {health === 'offline' && <p className="sidebar-service-warning" role="status">应用服务未连接</p>}
  </div>;
  return <div className={`workbench-shell three-panel-shell ${collapsed ? 'nav-collapsed' : ''}`} style={{ '--assistant-width': `${assistantWidth}px` } as CSSProperties}>
    {notificationHolder}
    <div className="workbench-body">
      <aside className="workbench-nav floating-surface" aria-label="主导航">
        <div className="sidebar-brand"><strong>{collapsed ? '药衡' : '药衡智析'}</strong></div>
        <div className="sidebar-navigation">{nav}</div>
        <div className="nav-bottom">{statusContent}<Tooltip title={collapsed ? '展开导航' : '收起导航'}><Button type="text" aria-label={collapsed ? '展开导航' : '收起导航'} icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => setCollapsed(value => !value)}>{!collapsed && '收起导航'}</Button></Tooltip></div>
      </aside>
      <main className="workbench-content floating-surface" aria-label={`${pageInfo.title}工作区`}>
        <div className="workspace-toolbar" aria-label="工作区选项">
          {mobile && <div className="mobile-workspace-controls"><Button type="text" aria-label="打开导航" icon={<MenuUnfoldOutlined />} onClick={() => setNavOpen(true)} /><strong>药衡智析</strong><Button type="text" aria-label="打开对话" icon={<MessageOutlined />} onClick={() => setAssistantOpen(true)} /></div>}
          {page !== 'analysis' && <div className="workspace-page-title"><h1>{pageInfo.title}</h1><p>{pageInfo.intro}</p></div>}
          {inWorkspace && contextId && catalog && <section className="workspace-filters" aria-label="分析筛选">
            <label className="product-field"><span>产品</span><Select aria-label="产品" value={product} options={catalog.products.map(value => ({ value }))} onChange={value => changeSelection({ product: value })} /></label>
            {page !== 'benchmark' && <label className="factory-field"><span>工厂</span><Select aria-label="工厂" value={factory} options={catalog.factories.map(value => ({ value }))} onChange={value => changeSelection({ factory: value })} /></label>}
            <label className="period-field"><span>{analysis_type === 'quarterly' ? '季度截止月' : '月份'}</span><Select aria-label="月份" value={month} options={catalog.months.filter(m => analysis_type !== 'quarterly' || ['03', '06', '09', '12'].includes(m.slice(-2))).map(value => ({ value }))} onChange={value => changeSelection({ month: value })} /></label>
            <label className="range-field"><span>类型</span><Select aria-label="报告范围" value={analysis_type} options={[{ value: 'monthly', label: '月度' }, { value: 'quarterly', label: '季度', disabled: !catalog.months.some(m => ['03', '06', '09', '12'].includes(m.slice(-2))) }, { value: 'special', label: '专题' }]} onChange={changeRange} /></label>
            <label className="cost-basis"><span>口径</span><Segmented aria-label="成本口径" value={basis} options={[{ value: 'unit', label: '单位' }, { value: 'total', label: '总额' }]} onChange={value => changeSelection({ basis: value as Selection['basis'] })} /></label>
            {page === 'analysis' && <Tooltip title="生成报告"><Button className="generate-report-button" type="primary" aria-label="生成报告" icon={<FileTextOutlined />} onClick={() => navigate('reports')}><span>生成报告</span></Button></Tooltip>}
            {analysis_type === 'special' && <label className="topic-field"><span>专题主题</span><Input key={`${contextId}:${selection.topic ?? ''}`} aria-label="专题主题" defaultValue={selection.topic ?? ''} maxLength={120} placeholder="例如：原材料成本变动与核查建议" onBlur={event => { if (event.target.value !== (selection.topic ?? '')) changeSelection({ topic: event.target.value }); }} onPressEnter={event => event.currentTarget.blur()} /></label>}
          </section>}
          {page === 'analysis' && <nav className="workspace-section-tabs" aria-label="分析分区导航">{ANALYSIS_SECTIONS.map(([id, label]) => <button key={id} type="button" aria-current={activeSection === id ? 'location' : undefined} onClick={() => jumpToSection(id)}>{label}</button>)}</nav>}
          {page === 'models' && <div className="workspace-section-tabs" role="tablist" aria-label="模型用途">{MODEL_TABS.map((item, index) => <button type="button" key={item.key} id={`model-tab-${item.key}`} role="tab" aria-selected={modelTab === item.key} aria-controls="model-settings-panel" tabIndex={modelTab === item.key ? 0 : -1} onClick={() => setModelTab(item.key)} onKeyDown={event => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            const next = event.key === 'Home' ? 0 : event.key === 'End' ? MODEL_TABS.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + MODEL_TABS.length) % MODEL_TABS.length;
            setModelTab(MODEL_TABS[next].key); document.getElementById(`model-tab-${MODEL_TABS[next].key}`)?.focus();
          }}>{item.label}</button>)}</div>}
        </div>
        <div className="workspace-scroll" ref={scrollRef} onScroll={trackSection}>
          <div className="business-main" ref={contentRef}>
            {workspaceLoading && inWorkspace && <div className="business-loading" role="status"><Spin /><span>正在汇集已发布的数据…</span></div>}
            {!workspaceLoading && workspaceState.status === 'EMPTY' && !contextId && inWorkspace && !error && <section className="panel onboarding"><Empty description="尚无可分析的数据" /><p>导入业务文件并完成解析后，这里会自动汇集数据。</p><Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('business')}>导入业务数据</Button></section>}
            {!workspaceLoading && ['BLOCKED', 'PENDING'].includes(workspaceState.status) && inWorkspace && <Alert className="workspace-data-warning" type="warning" showIcon title={workspaceState.status === 'PENDING' ? '还有文件待解析，分析将在全部通过后更新' : '部分文件未通过校验，暂不能生成新分析'} description={workspaceState.issues.slice(0, 3).map((item, index) => <p key={index}>{item.filename ? `${item.filename}：` : ''}{item.message}</p>)} action={<Button size="small" onClick={() => navigate('business')}>检查数据</Button>} />}
            {analysis_type === 'quarterly' && inWorkspace && <p className="scope-note">季度单位成本按总成本 ÷ 可比产量计算；趋势图保留月度明细，缺月不补零。</p>}
            {error && <Alert type="error" showIcon title={error} action={<Button size="small" onClick={() => { setError(''); setReload(value => value + 1); }}>重试</Button>} />}
            {jobsError && ['reports', 'actions'].includes(page) && <Alert type="error" title={`任务列表读取失败：${jobsError}`} action={<Button size="small" onClick={() => refresh()}>重试</Button>} />}
            {!workspaceLoading && (page === 'benchmark' ? benchmarkLoading : snapshotPage && analysisLoading) && <div className="business-loading" role="status"><Spin /><span>{page === 'benchmark' ? '正在计算跨厂差异与检索证据…' : '正在读取当前版本的数据…'}</span></div>}
            <Suspense key={reload} fallback={<div className="business-loading"><Spin />正在加载功能…</div>}>
              {page === 'business' && <BusinessData onPublished={onPublished} />}
              {page === 'knowledge' && <KnowledgeData contextId={contextId} product={product} month={month} factory={factory} onOpen={setDrawer} />}
              {page === 'templates' && <TemplateCenter />}
              {page === 'analysis' && snapshot && !workspaceLoading && workspaceState.status === 'READY' && <><Analysis key={`${contextId}:${snapshot.snapshot_id}`} snapshot={snapshot} basis={basis} onEvidence={setDrawer} /><details className="panel"><summary>报告与看板任务建议</summary><DecisionCard selection={selection} onApplied={() => void refresh().catch(event => onError(event.message))} onError={onError} /></details></>}
              {page === 'analysis' && catalog && selection.context_id === contextId && !workspaceLoading && workspaceState.status === 'READY' && <ProductMonthHeatmap key={contextId} selection={selection} onSelect={(product, month) => changeSelection({ product, month, analysis_type: 'monthly' })} />}
              {page === 'benchmark' && <><div className="comparison-filters"><label>分析工厂<Select aria-label="分析工厂" value={left} options={catalog?.factories.map(value => ({ value, disabled: value === right }))} onChange={value => { window.history.pushState(null, '', urlFor(page, selection, value, right)); setLeft(value); setBenchmark(null); }} /></label><SwapOutlined /><label>基准工厂<Select aria-label="基准工厂" value={right || undefined} placeholder="请选择基准工厂" options={catalog?.factories.map(value => ({ value, disabled: value === left }))} onChange={value => { window.history.pushState(null, '', urlFor(page, selection, left, value)); setRight(value); setBenchmark(null); }} /></label></div>{!catalog || catalog.factories.length < 2 ? <Alert type="info" title="需要至少两个工厂的可比数据才能进行对标。" description="当前工作区接入的工厂不足两家。可在「数据中心」导入第二家工厂的同口径数据；未接入业务数据时，工作区会展示示范双厂数据，可直接体验三步对标。" /> : <div className="benchmark-workbench"><Benchmark data={benchmark} analysisType={analysis_type} onSwap={() => { setLeft(right); setRight(left); setBenchmark(null); }} onEvidence={setDrawer} /></div>}</>}
              {page === 'reports' && <ReportGeneration selection={selection} snapshot={snapshot} jobs={jobs} refresh={refresh} onError={onError} />}
              {page === 'actions' && <Rectification selection={selection} snapshot={snapshot} jobs={jobs} actions={actions} refresh={refresh} onError={onError} />}
            </Suspense>
            {page === 'models' && <div role="tabpanel" id="model-settings-panel" aria-labelledby={`model-tab-${modelTab}`} key={modelTab}>{modelTab === 'analysis' ? <AnalysisModel /> : modelTab === 'extraction' ? <ExtractionModel /> : modelTab === 'assistant' ? <ModelConfigForm route="assistant" /> : <VectorModel />}</div>}
            {page === 'settings' && <SystemSettings preferences={preferences} onChange={changePreferences} storageWarning={storageWarning} status={systemStatus} health={health} onRefresh={() => setReload(value => value + 1)} onAccess={() => setAccessOpen(true)} />}
            {inWorkspace && <Capabilities value={snapshot?.capabilities ?? catalog?.capabilities ?? activeContext?.capabilities} />}
          </div>
        </div>
      </main>
      {!mobile && <aside className="assistant-dock floating-surface" aria-label="对话工作区"><div className="assistant-resizer" role="separator" aria-label="调整助手宽度" aria-orientation="vertical" aria-valuemin={320} aria-valuemax={500} aria-valuenow={assistantWidth} tabIndex={0} onPointerDown={resizeAssistant} onKeyDown={event => { if (['ArrowLeft', 'ArrowRight'].includes(event.key)) event.preventDefault(); if (event.key === 'ArrowLeft') setAssistantWidth(value => Math.min(500, value + 20)); if (event.key === 'ArrowRight') setAssistantWidth(value => Math.max(320, value - 20)); }} />{assistant}</aside>}
    </div>
    {mobile && <Drawer title="对话" open={assistantOpen && !drawer} onClose={() => setAssistantOpen(false)} size={Math.min(window.innerWidth, 440)} styles={{ body: { padding: 0 } }} forceRender>{assistant}</Drawer>}
    <Drawer className="mobile-navigation-drawer" title="药衡智析" placement="left" open={navOpen} onClose={() => setNavOpen(false)} size={250}><div className="mobile-sidebar-content">{nav}{statusContent}</div></Drawer>
    {drawer && <EvidenceDrawer value={{ context_id: contextId, ...drawer }} onClose={closeDrawer} />}
    <Modal title="应用访问令牌" open={accessOpen} onCancel={() => { setAccessOpen(false); setToken(''); }} onOk={() => { setAccessToken(token); setToken(''); setAccessOpen(false); setReload(value => value + 1); }} okText="连接" cancelText="取消" destroyOnHidden><p>仅在服务启用了访问令牌时填写。令牌只保存在当前页面内存中，与模型 API 密钥分开。</p><Input.Password aria-label="应用访问令牌" value={token} autoComplete="off" onChange={event => setToken(event.target.value)} /></Modal>
  </div>;
}

function Capabilities({ value }: { value: any }) {
  if (value == null) return null;
  const rows = Array.isArray(value) ? value : Object.entries(value).map(([key, v]) => typeof v === 'object' && v !== null ? { key, ...v as any } : { key, status: v === true ? 'AVAILABLE' : 'UNAVAILABLE' });
  if (!rows.length) return null;
  const names: Record<string, string> = { pdf_service: 'PDF 转换', model_service: '模型服务', rpa_service: '任务服务' };
  const status: Record<string, string> = { AVAILABLE: '可用', PASS: '可用', DEGRADED: '降级', BLOCKED: '不可用', UNAVAILABLE: '不可用', MISSING_DATA: '缺少数据' };
  return <details className="capabilities"><summary>查看当前能力与数据缺口</summary><ul>{rows.map((v: any, i: number) => <li key={v.key ?? i}><strong>{v.label ?? v.name ?? names[v.key] ?? v.key ?? '分析能力'}</strong>：{status[String(v.status).toUpperCase()] ?? '待核验'}{v.reason ? `；${v.reason}` : ''}</li>)}</ul></details>;
}
