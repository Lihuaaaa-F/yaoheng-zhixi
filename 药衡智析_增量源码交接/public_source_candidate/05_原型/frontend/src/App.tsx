import { lazy, Suspense, useState, useEffect, useCallback, useRef, type CSSProperties } from 'react';
import { Alert, Badge, Button, Drawer, Empty, Input, Menu, Modal, Select, Segmented, Space, Spin, Tabs, Tooltip } from 'antd';
import { ApartmentOutlined, BarChartOutlined, BookOutlined, CheckSquareOutlined, DatabaseOutlined, FileTextOutlined, MenuFoldOutlined, MenuUnfoldOutlined, RobotOutlined, SafetyCertificateOutlined, SettingOutlined, SwapOutlined, UploadOutlined } from '@ant-design/icons';
import { api, Selection, IndustryContext, contextQuery, setAccessToken } from './api';
import { Catalog, Snapshot, BenchmarkData } from './types';
import { useJobsActions } from './hooks';
import Analysis from './Analysis';
import { EvidenceDrawer } from './Evidence';
import AssistantDock from './AssistantDock';
import ModelConfigForm from './ModelConfigForm';
import { ExtractionModel, AnalysisModel, VectorModel } from './ModelPages';
const ProductMonthHeatmap = lazy(() => import('./ProductMonthHeatmap'));
const Benchmark = lazy(() => import('./Benchmark'));
const DecisionCard = lazy(() => import('./DecisionCard'));
const BusinessData = lazy(() => import('./BusinessData'));
const KnowledgeData = lazy(() => import('./KnowledgeData'));
const TemplateCenter = lazy(() => import('./TemplateCenter'));
const ReportGeneration = lazy(() => import('./ReportGeneration'));
const Rectification = lazy(() => import('./Rectification'));

const PAGES = [
  { key: 'analysis', title: '成本分析', group: '工作台', icon: <BarChartOutlined />, intro: '从成本变化出发，核对数据、证据与可执行的建议。' },
  { key: 'benchmark', title: '跨厂对标', group: '工作台', icon: <SwapOutlined />, intro: '同产品、同规格、同期间，依次找差异、拆结构、查原因。' },
  { key: 'reports', title: '分析报告', group: '工作台', icon: <FileTextOutlined />, intro: '生成并核验正式报告，下载 Word 与 PDF。' },
  { key: 'actions', title: '问题整改', group: '工作台', icon: <CheckSquareOutlined />, intro: '将建议转为整改草稿，确认下发并追踪送达和处理状态。' },
  { key: 'business', title: '业务数据', group: '数据中心', icon: <DatabaseOutlined />, intro: '导入成本汇总、明细与预算，完成校验后进入分析。' },
  { key: 'knowledge', title: '知识库', group: '数据中心', icon: <BookOutlined />, intro: '按当前数据范围管理资料，检索和核对来源。' },
  { key: 'templates', title: '报告模板', group: '数据中心', icon: <FileTextOutlined />, intro: '维护月度、季度和专题报告模板。' },
  { key: 'models', title: '模型连接', group: '模型与设置', icon: <ApartmentOutlined />, intro: '分别配置分析、提取、向量检索和右侧助手所用模型。' },
];
const initialSelection: Selection = { context_id: '', factory: '', product: '', month: '', analysis_type: 'monthly', basis: 'unit' };
function readLocation() {
  const q = new URLSearchParams(window.location.search);
  const page = PAGES.some(p => p.key === q.get('page')) ? q.get('page')! : 'analysis';
  const selection: Selection = { ...initialSelection, ...Object.fromEntries(['context_id', 'factory', 'product', 'month', 'topic'].flatMap(k => q.has(k) ? [[k, q.get(k)!]] : [])), analysis_type: ['monthly', 'quarterly', 'special'].includes(q.get('analysis_type') ?? '') ? q.get('analysis_type') as Selection['analysis_type'] : 'monthly', basis: q.get('basis') === 'total' ? 'total' : 'unit' };
  return { page, selection, left: q.get('left') ?? '', right: q.get('right') ?? '', modelTab:['analysis','extraction','assistant','vector'].includes(q.get('model_route')??'')?q.get('model_route')!:'analysis' };
}
function urlFor(page: string, selection: Selection, left: string, right: string) {
  const q = new URLSearchParams({ page });
  for (const [key, value] of Object.entries({ ...selection, left, right })) if (value) q.set(key, String(value));
  return `${window.location.pathname}?${q.toString()}`;
}

export default function App() {
  const [location] = useState(readLocation), [page, setPage] = useState(location.page);
  const [contexts, setContexts] = useState<IndustryContext[]>([]), [contextId, setContextId] = useState(location.selection.context_id);
  const [catalog, setCatalog] = useState<Catalog | null>(null), [selection, setSelection] = useState(location.selection);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null), [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [left, setLeft] = useState(location.left), [right, setRight] = useState(location.right);
  const [error, setError] = useState(''), [analysisLoading, setAnalysisLoading] = useState(false), [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [drawer, setDrawer] = useState<any>(null), [reload, setReload] = useState(0), [health, setHealth] = useState<'loading' | 'online' | 'offline'>('loading');
  const [assistantOpen, setAssistantOpen] = useState(window.innerWidth >= 1100), [assistantWidth, setAssistantWidth] = useState(380), [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(window.innerWidth < 1100), [navOpen, setNavOpen] = useState(false);
  const [systemStatus,setSystemStatus]=useState<any>(null);
  const [accessOpen, setAccessOpen] = useState(false), [token, setToken] = useState(''), [modelTab, setModelTab] = useState(location.modelTab);
  const activeContext = contexts.find(c => c.context_id === contextId), pageInfo = PAGES.find(p => p.key === page)!;
  const inWorkspace = pageInfo.group === '工作台', currentContext = useRef(contextId); currentContext.current = contextId;
  const { jobs, actions, refresh, jobsError } = useJobsActions(page === 'reports' || page === 'actions' ? 2 : -1, contextId);
  const selectionRef = useRef(selection); selectionRef.current = selection;
  const navigate = (next: string) => { window.history.pushState(null, '', urlFor(next, selection, left, right)); setPage(next); setNavOpen(false); };
  const changeSelection = (next: Partial<Selection>) => { const value = { ...selection, ...next }; window.history.pushState(null, '', urlFor(page, value, left, right)); setSelection(value); if (value.context_id !== contextId) setContextId(value.context_id); };
  useEffect(() => {const url=new URL(urlFor(page,selection,left,right),window.location.origin);if(page==='models')url.searchParams.set('model_route',modelTab);window.history.replaceState(null,'',url.pathname+url.search);},[page,selection,left,right,modelTab]);
  useEffect(() => { const pop = () => { const value = readLocation(); setPage(value.page); setSelection(value.selection); setContextId(value.selection.context_id); setLeft(value.left); setRight(value.right); setModelTab(value.modelTab); }; window.addEventListener('popstate', pop); return () => window.removeEventListener('popstate', pop); }, []);
  useEffect(() => { const resize = () => setMobile(window.innerWidth < 1100); window.addEventListener('resize', resize); return () => window.removeEventListener('resize', resize); }, []);
  useEffect(() => { const required = () => setAccessOpen(true); window.addEventListener('pharma:access-required', required); return () => window.removeEventListener('pharma:access-required', required); }, []);
  useEffect(() => {
    const controller = new AbortController();
    const check = () => fetch('/health', { signal: controller.signal }).then(response => { if (!controller.signal.aborted) setHealth(response.ok ? 'online' : 'offline'); }).catch(() => { if (!controller.signal.aborted) setHealth('offline'); });
    void check(); const timer = setInterval(check, 30000); return () => { controller.abort(); clearInterval(timer); };
  }, [reload]);
  useEffect(()=>{const c=new AbortController();const poll=()=>api(`/system/status?${contextQuery(contextId)}`,undefined,c.signal).then(setSystemStatus).catch(()=>{if(!c.signal.aborted)setSystemStatus(null)});void poll();const timer=setInterval(poll,60000);return()=>{c.abort();clearInterval(timer)}},[contextId,reload]);
  useEffect(() => {
    const c = new AbortController(); api('/industry/catalog', undefined, c.signal).then(x => {
      if (c.signal.aborted) return; setContexts(x.contexts ?? []);
      const current = currentContext.current;
      if (!x.contexts.some((v: IndustryContext) => v.context_id === current)) setContextId(x.default_context_id ?? x.contexts[0]?.context_id ?? '');
    }).catch(e => { if (!c.signal.aborted) setError(e.message); }); return () => c.abort();
  }, [reload]);
  useEffect(() => {
    if (!contextId) { setCatalog(null); setSnapshot(null); setBenchmark(null); return; }
    const c = new AbortController(); setCatalog(null); setSnapshot(null); setBenchmark(null); setDrawer(null); setError('');
    api(`/catalog?${contextQuery(contextId)}`, undefined, c.signal).then(x => {
      if (c.signal.aborted) return;
      const previous = selectionRef.current, same = previous.context_id === contextId;
      let selectedMonth=same&&x.months.includes(previous.month)?previous.month:x.months.at(-1)??'';
      if(same&&previous.analysis_type==='quarterly'&&!['03','06','09','12'].includes(selectedMonth.slice(-2)))selectedMonth=x.months.filter((value:string)=>['03','06','09','12'].includes(value.slice(-2))).at(-1)??selectedMonth;
      setSelection({ ...initialSelection, ...(same ? previous : {}), context_id: contextId, factory: same && x.factories.includes(previous.factory) ? previous.factory : x.factories[0] ?? '', product: same && x.products.includes(previous.product) ? previous.product : x.products[0] ?? '', month:selectedMonth });
      setLeft(value => x.factories.includes(value) ? value : x.factories[0] ?? ''); setRight(value => x.factories.includes(value) ? value : x.factories[1] ?? ''); setCatalog(x);
    }).catch(e => { if (!c.signal.aborted) setError(e.message); }); return () => c.abort();
  }, [contextId, reload]);
  const { factory, product, month, analysis_type, basis } = selection;
  const snapshotPage = ['analysis', 'reports', 'actions'].includes(page);
  useEffect(() => {
    if (!snapshotPage || !catalog || selection.context_id !== contextId) return;
    const c = new AbortController(); setAnalysisLoading(true); setError(''); setSnapshot(null);
    api('/analyses', selection, c.signal).then(x => { if (!c.signal.aborted) setSnapshot(x); }).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setAnalysisLoading(false); }); return () => c.abort();
  }, [snapshotPage, catalog, contextId, selection, reload]);
  useEffect(() => {
    if (page !== 'benchmark' || !catalog || selection.context_id !== contextId || !left || !right || left === right) return;
    const c = new AbortController(); setBenchmarkLoading(true); setError(''); setBenchmark(null);
    const params = new URLSearchParams({ context_id: contextId, product, month, left, right, analysis_type, basis, explain: 'async' });
    api(`/benchmarks?${params}`, undefined, c.signal).then(x => { if (!c.signal.aborted) setBenchmark(x); }).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setBenchmarkLoading(false); }); return () => c.abort();
  }, [page, catalog, contextId, product, month, left, right, analysis_type, basis, reload]);
  const closeDrawer = useCallback(() => setDrawer(null), []);
  const changeRange = (kind: Selection['analysis_type']) => {
    const ends = catalog?.months.filter(m => ['03', '06', '09', '12'].includes(m.slice(-2))) ?? [];
    const quarterEnd = `${month.slice(0, 4)}-${String(Math.ceil(Number(month.slice(-2)) / 3) * 3).padStart(2, '0')}`;
    changeSelection({ analysis_type: kind, month: kind === 'quarterly' ? ends.includes(quarterEnd) ? quarterEnd : ends.at(-1) ?? month : month });
  };
  const onPublished = (value: any) => { const id = value?.context_id ?? value?.published?.context_id ?? value?.dataset?.context_id ?? value?.contexts?.[0]?.context_id; if (id) { setContextId(id); setSelection({ ...initialSelection, context_id: id }); setPage('analysis'); } setReload(n => n + 1); };
  const onError = (message: string) => { if (currentContext.current === contextId) setError(message); };
  const nav = <Menu mode="inline" selectedKeys={[page]} inlineCollapsed={!mobile && collapsed} onClick={({ key }) => navigate(key)} items={['工作台', '数据中心', '模型与设置'].map(group => ({ type: 'group', key: group, label: collapsed && !mobile ? undefined : group, children: PAGES.filter(p => p.group === group).map(p => ({ key: p.key, icon: p.icon, label: p.title, title: p.title })) }))} />;
  const assistant = <AssistantDock key={reload} selection={page==='benchmark'?{...selection,factory:left,benchmark_right:right}:selection} onConfigure={()=>{setModelTab('assistant');navigate('models')}} onClose={() => setAssistantOpen(false)} onEvidence={setDrawer} onApplied={value => { void refresh().catch(e=>onError(e.message)); if (value.job_id) navigate('reports'); else if (value.action_id) navigate('actions'); }} />;
  const resizeAssistant = (event: React.PointerEvent<HTMLDivElement>) => {
    event.currentTarget.setPointerCapture(event.pointerId); const start = event.clientX, width = assistantWidth;
    const move = (e: PointerEvent) => setAssistantWidth(Math.min(520, Math.max(340, width + start - e.clientX)));
    const stop = () => { window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', stop); };
    window.addEventListener('pointermove', move); window.addEventListener('pointerup', stop, { once: true });
  };
  return <div className={`workbench-shell ${collapsed ? 'nav-collapsed' : ''}`} style={{ '--assistant-width': `${assistantWidth}px` } as CSSProperties}>
    <header className="workbench-header"><div className="header-brand"><Button type="text" aria-label={mobile ? '打开导航' : collapsed ? '展开导航' : '收起导航'} icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />} onClick={() => mobile ? setNavOpen(true) : setCollapsed(v => !v)} /><strong>药衡智析</strong></div>
      <div className="header-runtime"><span>{systemStatus?.deployment?.label??'运行环境检测中'}</span><Tooltip title={systemStatus?.network?.detail??'网络状态待检测'}><Badge status={systemStatus?.network?.status==='reachable'?'success':systemStatus?.network?.status==='unreachable'?'warning':'default'} text={systemStatus?.network?.status==='reachable'?'外网可达':systemStatus?.network?.status==='unreachable'?'外网探测失败':'网络状态待检测'}/></Tooltip><Tooltip title={systemStatus?.data?.basis??'当前数据版本'}><span>数据更新 {systemStatus?.data?.updated_at ? new Date(systemStatus.data.updated_at).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false}) : '—'}</span></Tooltip><span className="service-health">{health==='online'?'服务已连接':health==='offline'?'服务未连接':'服务检测中'}</span></div>
      <Space><Tooltip title="应用访问令牌"><Button type="text" aria-label="应用访问令牌" icon={<SafetyCertificateOutlined />} onClick={() => setAccessOpen(true)} /></Tooltip><Button icon={<SettingOutlined />} onClick={() => navigate('models')}>系统设置</Button><Button type={assistantOpen ? 'default' : 'primary'} icon={<RobotOutlined />} onClick={() => setAssistantOpen(v => !v)}>AI 助手</Button></Space>
    </header>
    <div className="workbench-body"><aside className="workbench-nav">{nav}<div className="nav-bottom">{!collapsed && <span>数据可核对 · 行动可追踪</span>}</div></aside>
      <div className="workbench-content"><main className="business-main"><div className="page-heading"><div><h1>{pageInfo.title}</h1>{page!=='analysis'&&<p>{pageInfo.intro}</p>}</div>{page === 'analysis' && contextId && <Button type="primary" icon={<FileTextOutlined />} onClick={() => navigate('reports')}>生成报告</Button>}</div>
        {!contextId && inWorkspace && <section className="panel onboarding"><Empty description="尚无可分析的数据" /><p>先导入企业成本数据，完成校验后即可分析与生成报告。</p><Button type="primary" icon={<UploadOutlined />} onClick={() => navigate('business')}>导入业务数据</Button></section>}
        {(inWorkspace||page==='knowledge') && contexts.length>0 && <div className="data-scope-row"><DatabaseOutlined/><label>数据范围</label><Select size="small" aria-label="数据范围" value={contextId||undefined} options={contexts.map(c=>({value:c.context_id,label:c.company_name}))} onChange={value=>changeSelection({...initialSelection,context_id:value})}/></div>}
        {inWorkspace && contextId && catalog && <section className="workspace-filters" aria-label="分析筛选">
          <label className="product-field">产品<Select aria-label="产品" value={product} options={catalog.products.map(value => ({ value }))} onChange={value => changeSelection({ product: value })} /></label>
          {page !== 'benchmark' && <label className="factory-field">工厂<Select aria-label="工厂" value={factory} options={catalog.factories.map(value => ({ value }))} onChange={value => changeSelection({ factory: value })} /></label>}
          <label className="period-field">{analysis_type === 'quarterly' ? '季度截止月' : '月份'}<Select aria-label="月份" value={month} options={catalog.months.filter(m => analysis_type !== 'quarterly' || ['03', '06', '09', '12'].includes(m.slice(-2))).map(value => ({ value }))} onChange={value => changeSelection({ month: value })} /></label>
          <label className="range-field">范围<Select aria-label="报告范围" value={analysis_type} options={[{ value: 'monthly', label: '月度' }, { value: 'quarterly', label: '季度', disabled: !catalog.months.some(m => ['03', '06', '09', '12'].includes(m.slice(-2))) }, { value: 'special', label: '专题' }]} onChange={changeRange} /></label>
          <label className="cost-basis">口径<Segmented value={basis} options={[{ value: 'unit', label: '单位' }, { value: 'total', label: '总额' }]} onChange={value => changeSelection({ basis: value as Selection['basis'] })} /></label>
          {analysis_type === 'special' && <label className="topic-field">专题主题<Input key={`${contextId}:${selection.topic??''}`} aria-label="专题主题" defaultValue={selection.topic ?? ''} maxLength={120} placeholder="例如：原材料成本变动与核查建议" onBlur={e => {if(e.target.value!==(selection.topic??''))changeSelection({ topic: e.target.value })}} onPressEnter={e=>e.currentTarget.blur()} /></label>}
        </section>}
        {analysis_type === 'quarterly' && inWorkspace && <p className="scope-note">季度单位成本按总成本 ÷ 可比产量计算；趋势图保留月度明细，缺月不补零。</p>}
        {error && <Alert type="error" showIcon title={error} action={<Button size="small" onClick={() => { setError(''); setReload(n => n + 1); }}>重试</Button>} />}
        {jobsError && ['reports', 'actions'].includes(page) && <Alert type="error" title={`任务列表读取失败：${jobsError}`} action={<Button size="small" onClick={() => refresh()}>重试</Button>} />}
        {(page === 'benchmark' ? benchmarkLoading : snapshotPage && analysisLoading) && <div className="business-loading" role="status"><Spin /> <span>{page === 'benchmark' ? '正在计算跨厂差异与检索证据…' : '正在读取当前版本的数据…'}</span></div>}
        <Suspense key={reload} fallback={<div className="business-loading"><Spin />正在加载功能…</div>}>
          {page === 'business' && <BusinessData onPublished={onPublished} />}
          {page === 'knowledge' && <KnowledgeData contextId={contextId} product={product} month={month} factory={factory} onOpen={setDrawer} />}
          {page === 'templates' && <TemplateCenter />}
          {page === 'analysis' && snapshot && <><Analysis key={`${contextId}:${snapshot.snapshot_id}`} snapshot={snapshot} basis={basis} onEvidence={setDrawer} /><details className="panel"><summary>报告与看板任务建议</summary><DecisionCard selection={selection} onApplied={()=>void refresh().catch(e=>onError(e.message))} onError={onError} /></details></>}
          {page === 'analysis' && catalog && selection.context_id === contextId && <ProductMonthHeatmap key={contextId} selection={selection} onSelect={(product, month) => changeSelection({ product, month, analysis_type: 'monthly' })} />}
          {page === 'benchmark' && <><div className="comparison-filters"><label>分析工厂<Select aria-label="分析工厂" value={left} options={catalog?.factories.map(value => ({ value, disabled: value === right }))} onChange={value => { window.history.pushState(null, '', urlFor(page, selection, value, right)); setLeft(value); setBenchmark(null); }} /></label><SwapOutlined /><label>基准工厂<Select aria-label="基准工厂" value={right} options={catalog?.factories.map(value => ({ value, disabled: value === left }))} onChange={value => { window.history.pushState(null, '', urlFor(page, selection, left, value)); setRight(value); setBenchmark(null); }} /></label></div>{!catalog || catalog.factories.length < 2 ? <Alert type="info" title="当前数据范围需要两个工厂才能进行对标。" /> : <div className="benchmark-workbench"><Benchmark data={benchmark} analysisType={analysis_type} onSwap={() => { setLeft(right); setRight(left); setBenchmark(null); }} onEvidence={setDrawer} /></div>}</>}
          {page === 'reports' && <ReportGeneration selection={selection} snapshot={snapshot} jobs={jobs} refresh={refresh} onError={onError} />}
          {page === 'actions' && <Rectification selection={selection} snapshot={snapshot} jobs={jobs} actions={actions} refresh={refresh} onError={onError} />}
        </Suspense>
        {page === 'models' && <Tabs key={reload} activeKey={modelTab} onChange={value=>{const url=new URL(window.location.href);url.searchParams.set('model_route',value);window.history.pushState(null,'',url.pathname+url.search);setModelTab(value)}} destroyOnHidden items={[{ key: 'analysis', label: '分析与报告', children: <AnalysisModel /> }, { key: 'extraction', label: '数据提取', children: <ExtractionModel /> }, { key: 'assistant', label: 'AI 助手（独立）', children: <ModelConfigForm route="assistant" /> }, { key: 'vector', label: '向量检索', children: <VectorModel /> }]} />}
        {inWorkspace && <Capabilities value={snapshot?.capabilities ?? catalog?.capabilities ?? activeContext?.capabilities} />}
      </main></div>
      {!mobile && <aside className="assistant-dock" style={{ display: assistantOpen && !drawer ? 'flex' : 'none' }}><div className="assistant-resizer" role="separator" aria-label="调整助手宽度" aria-orientation="vertical" aria-valuemin={340} aria-valuemax={520} aria-valuenow={assistantWidth} tabIndex={0} onPointerDown={resizeAssistant} onKeyDown={e => { if (['ArrowLeft','ArrowRight'].includes(e.key))e.preventDefault(); if (e.key === 'ArrowLeft') setAssistantWidth(v => Math.min(520, v + 20)); if (e.key === 'ArrowRight') setAssistantWidth(v => Math.max(340, v - 20)); }} />{assistant}</aside>}
    </div>
    {mobile && <Drawer title={null} open={assistantOpen && !drawer} onClose={() => setAssistantOpen(false)} size={Math.min(window.innerWidth, 440)} closable={false} styles={{ body: { padding: 0 } }} forceRender>{assistant}</Drawer>}
    <Drawer title="药衡智析" placement="left" open={navOpen} onClose={() => setNavOpen(false)} size={240}>{nav}</Drawer>
    {drawer && <EvidenceDrawer value={{ context_id: contextId, ...drawer }} onClose={closeDrawer} />}
    <Modal title="应用访问令牌" open={accessOpen} onCancel={() => { setAccessOpen(false); setToken(''); }} onOk={() => { setAccessToken(token); setToken(''); setAccessOpen(false); setReload(n => n + 1); }} okText="连接" cancelText="取消" destroyOnHidden><p>仅在服务启用了访问令牌时填写。令牌只保存在当前页面内存中，与模型 API 密钥分开。</p><Input.Password aria-label="应用访问令牌" value={token} autoComplete="off" onChange={e => setToken(e.target.value)} /></Modal>
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
