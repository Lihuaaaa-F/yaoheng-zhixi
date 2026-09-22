import { useState, useEffect, useCallback, useRef } from 'react';
import { api, Selection, IndustryContext, contextQuery } from './api';
import { Catalog, Snapshot, BenchmarkData } from './types';
import { useJobsActions } from './hooks';
import Analysis from './Analysis';
import ProductMonthHeatmap from './ProductMonthHeatmap';
import Benchmark from './Benchmark';
import { EvidenceDrawer } from './Evidence';
import DecisionCard from './DecisionCard';
import BusinessData from './BusinessData';
import KnowledgeData from './KnowledgeData';
import TemplateCenter from './TemplateCenter';
import ReportGeneration from './ReportGeneration';
import Rectification from './Rectification';
import { ExtractionModel, AnalysisModel, VectorModel } from './ModelPages';

// 三模块信息架构（2026-09-22 改版）：数据中心（3 子项）→ 工作台（4 子项）→
// 模型配置（3 子项）。专为本制药赛题定制：无行业包选择、无合成演示数据。
const NAV = [
  { module: '数据中心', items: ['业务数据', '知识库数据', '报告模板'] },
  { module: '工作台', items: ['数据分析', '跨厂对标', '报告生成', '问题整改'] },
  { module: '模型配置', items: ['数据提取模型', '数据分析模型', '向量模型'] },
];
const PAGES = NAV.flatMap(group => group.items.map(item => ({ module: group.module, item })));
const PAGE_INTROS: Record<string, string> = {
  '业务数据': '上传成本数据：多类型导入、列表等待、一键解析到归因分析全流程。',
  '知识库数据': '三类知识入库并构建向量知识索引；检索结果可核对来源与适用范围。',
  '报告模板': '解析月度/季度/专题报告模板：章节契约、占位符语义绑定与安装。',
  '数据分析': '从成本变化追踪数据，连接证据与可核查的行动建议。',
  '跨厂对标': '同产品、同规格、同期间，逐层查看工厂差异（找差异→拆结构→拆原因）。',
  '报告生成': '固定输入版本生成 Word/PDF 报告；下载与分项验收。',
  '问题整改': '报告建议转整改任务：确认发送、模拟通知与责任人确认全链路跟踪。',
  '数据提取模型': '小模型：数据提取与字段映射等轻量任务（多模型协作加分项）。',
  '数据分析模型': '大模型：报告分析、看板归因、对标拆原因与任务生成。',
  '向量模型': '本地向量模型信息与切换：脚本校验+分析模型适配+知识库重建。',
};
const initialSelection: Selection = { context_id: '', factory: '', product: '', month: '', analysis_type: 'monthly', basis: 'unit' };

export default function App() {
  const [page, setPage] = useState(3); // 默认进入“数据分析”
  const [contexts, setContexts] = useState<IndustryContext[]>([]);
  const [contextId, setContextId] = useState('');
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [selection, setSelection] = useState(initialSelection);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkData | null>(null);
  const [left, setLeft] = useState(''), [right, setRight] = useState('');
  const [error, setError] = useState('');
  const [analysisLoading, setAnalysisLoading] = useState(false), [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [drawer, setDrawer] = useState<any>(null), [reload, setReload] = useState(0), [benchElapsed, setBenchElapsed] = useState(0);
  const activeContext = contexts.find(c => c.context_id === contextId);
  const currentContext = useRef(contextId); currentContext.current = contextId;
  const pageInfo = PAGES[page];
  const inWorkspace = pageInfo?.module === '工作台';
  const { jobs, actions, refresh } = useJobsActions(inWorkspace && (pageInfo?.item === '报告生成' || pageInfo?.item === '问题整改') ? 2 : -1, contextId);
  // reload 计数：任一数据请求失败后“重试”按钮递增，触发对应 effect 重取
  useEffect(() => {
    const c = new AbortController();
    api('/industry/catalog', undefined, c.signal).then(x => {
      if (c.signal.aborted) return;
      setContexts(x.contexts);
      const requested = new URLSearchParams(window.location.search).get('context_id');
      if (!contexts.length) setContextId(x.contexts.some((v: IndustryContext) => v.context_id === requested) ? requested : x.default_context_id ?? x.contexts[0]?.context_id ?? '');
    }).catch(e => { if (!c.signal.aborted) setError(e.message); });
    return () => c.abort();
  }, [reload]);
  useEffect(() => {
    if (!contextId) { setCatalog(null); setSnapshot(null); setBenchmark(null); return; }
    const c = new AbortController();
    setCatalog(null); setSnapshot(null); setBenchmark(null); setDrawer(null); setError('');
    api(`/catalog?${contextQuery(contextId)}`, undefined, c.signal).then(x => {
      if (c.signal.aborted) return;
      setSelection(s => ({ ...initialSelection, context_id: contextId, factory: x.factories[0] ?? '', product: x.products[0] ?? '', month: x.months.at(-1) ?? '' }));
      setLeft(x.factories[0] ?? ''); setRight(x.factories[1] ?? ''); setCatalog(x);
    }).catch(e => { if (!c.signal.aborted) setError(e.message); });
    return () => c.abort();
  }, [contextId, reload]);
  const { factory, product, month, analysis_type, basis } = selection;
  const isAnalysisPage = pageInfo?.item === '数据分析';
  useEffect(() => {
    if (!isAnalysisPage || !catalog || selection.context_id !== contextId) return;
    const c = new AbortController();
    setAnalysisLoading(true); setError(''); setSnapshot(null);
    api('/analyses', selection, c.signal).then(x => { if (!c.signal.aborted) setSnapshot(x); })
      .catch(e => { if (!c.signal.aborted) setError(e.message); })
      .finally(() => { if (!c.signal.aborted) setAnalysisLoading(false); });
    return () => c.abort();
  }, [isAnalysisPage, catalog, contextId, selection, reload]);
  useEffect(() => {
    if (pageInfo?.item !== '跨厂对标' || !catalog || selection.context_id !== contextId || !left || !right || left === right) return;
    const c = new AbortController();
    setBenchmarkLoading(true); setError(''); setBenchmark(null); setBenchElapsed(0);
    const params = new URLSearchParams({ context_id: contextId, product, month, left, right, analysis_type, basis });
    api(`/benchmarks?${params}`, undefined, c.signal).then(x => { if (!c.signal.aborted) setBenchmark(x); })
      .catch(e => { if (!c.signal.aborted) setError(e.message); })
      .finally(() => { if (!c.signal.aborted) setBenchmarkLoading(false); });
    return () => c.abort();
  }, [page, catalog, contextId, product, month, left, right, analysis_type, basis, reload]);
  // 对标耗时反馈：每秒更新已等待时间，用户不再面对无进度长等待
  useEffect(() => { if (!benchmarkLoading) return; setBenchElapsed(0); const timer = setInterval(() => setBenchElapsed(n => n + 1), 1000); return () => clearInterval(timer); }, [benchmarkLoading]);
  const closeDrawer = useCallback(() => setDrawer(null), []);
  const changeRange = (kind: Selection['analysis_type']) => setSelection(s => {
    const ends = catalog?.months.filter((m: string) => ['03', '06', '09', '12'].includes(m.slice(-2))) ?? [];
    const quarterEnd = `${s.month.slice(0, 4)}-${String(Math.ceil(Number(s.month.slice(-2)) / 3) * 3).padStart(2, '0')}`;
    return { ...s, analysis_type: kind, month: kind === 'quarterly' ? (ends.includes(quarterEnd) ? quarterEnd : ends.at(-1) ?? s.month) : s.month };
  });
  const noData = inWorkspace && !contextId;
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">衡</span><div><strong>药衡智析</strong><small>制药成本智能分析报告系统</small></div></div>
      <nav aria-label="主导航">{NAV.map(group => <div className="nav-group" key={group.module}>
        <p className="nav-module">{group.module}</p>
        {group.items.map(item => {
          const index = PAGES.findIndex(p => p.item === item);
          return <button aria-current={page === index ? 'page' : undefined} className={page === index ? 'active' : ''} key={item} onClick={() => setPage(index)}>
            <span className="nav-number">{String(index + 1).padStart(2, '0')}</span>{item}</button>;
        })}
      </div>)}</nav>
      <div className="sidebar-footer"><strong>确定性计算 · 可追溯证据</strong><p>专业报告 · 模拟 RPA</p><span>企业赛题 · 创灵境</span></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><span>制药企业产品成本智能分析报告系统</span><span className="local-dot">本地服务</span></header>
      <main>
        <div className="page-heading">
          <div><h1>{pageInfo?.item ?? ''}</h1><p>{PAGE_INTROS[pageInfo?.item ?? ''] ?? ''}</p></div>
          {(inWorkspace || pageInfo?.item === '知识库数据') && <span className="outline-label">{activeContext?.data_label ?? (contexts.length ? '正在读取数据范围' : '尚无数据范围')}</span>}
        </div>
        {noData && <section className="panel"><h2>暂无可用数据范围</h2><p className="muted">请先到「数据中心 · 业务数据」导入并解析成本数据，或启用赛题数据包（见 README）。已解析的数据集会出现在此处“数据范围”选择器中。</p><button className="primary" onClick={() => setPage(0)}>前往数据中心</button></section>}
        {inWorkspace && contextId && <section className="filters context-filters" aria-label="数据范围">
          <label>数据范围<select aria-label="数据范围" value={contextId} onChange={e => setContextId(e.target.value)}>
            {contexts.map(c => <option key={c.context_id} value={c.context_id}>{c.company_name}{c.context_id === 'pharmaceutical:competition' ? '' : ''}</option>)}
          </select></label>
          <p className="muted">已建报告与任务保留创建时的数据集与政策版本。</p>
        </section>}
        {inWorkspace && contextId && catalog && <section className="filters" aria-label="分析筛选">
          <label>产品<select aria-label="产品" value={product} onChange={e => setSelection(s => ({ ...s, product: e.target.value }))}>{catalog.products.map(p => <option key={p}>{p}</option>)}</select></label>
          <label>工厂<select aria-label="工厂" value={factory} onChange={e => setSelection(s => ({ ...s, factory: e.target.value }))}>{catalog.factories.map(f => <option key={f}>{f}</option>)}</select></label>
          <label>{analysis_type === 'quarterly' ? '季度末月' : '月份'}<select aria-label="月份" value={month} onChange={e => setSelection(s => ({ ...s, month: e.target.value }))}>{catalog.months.filter((m: string) => analysis_type !== 'quarterly' || ['03', '06', '09', '12'].includes(m.slice(-2))).map((m: string) => <option key={m}>{m}</option>)}</select></label>
          <label>报告范围<select aria-label="报告范围" value={analysis_type} onChange={e => changeRange(e.target.value as Selection['analysis_type'])} title="月度分析：常规月度成本报告；季度分析：季度汇总口径；专题分析：围绕特定主题的专项报告"><option value="monthly">月度分析</option><option value="quarterly" disabled={!catalog.months.some((m: string) => ['03', '06', '09', '12'].includes(m.slice(-2)))}>季度分析</option><option value="special">专题分析（特定主题）</option></select></label>
          <div className="basis"><span>成本口径</span><div role="group" aria-label="成本口径">{(['unit', 'total'] as const).map(b => <button key={b} aria-pressed={basis === b} className={basis === b ? 'selected' : ''} onClick={() => setSelection(s => ({ ...s, basis: b }))}>{b === 'unit' ? '单位' : '总额'}</button>)}</div></div>
        </section>}
        {analysis_type === 'quarterly' && inWorkspace && <p className="notice">季度单位成本 = 季度总成本 ÷ 季度可比产量。缺月不补零；趋势图保留月度口径。</p>}
        {analysis_type === 'special' && inWorkspace && <p className="notice">专题分析：围绕选定的产品/工厂/月份出具一次专项主题报告（如某原料涨价影响）；报告结构由「数据中心 · 报告模板」中安装的专题模板决定，未安装时沿用月度模板。</p>}
        <Capabilities value={snapshot?.capabilities ?? catalog?.capabilities ?? activeContext?.capabilities} />
        {error && <ErrorBox message={error} onRetry={() => { setError(''); setReload(n => n + 1); }} />}
        {(pageInfo?.item === '跨厂对标' ? benchmarkLoading : analysisLoading) && <div className="loading" role="status">{pageInfo?.item === '跨厂对标' ? `正在对标分析：差异计算、证据检索与原因假设（约 10–60 秒），已等待 ${benchElapsed} 秒…` : '正在读取固定版本数据…'}</div>}

        {pageInfo?.item === '业务数据' && <BusinessData />}
        {pageInfo?.item === '知识库数据' && <KnowledgeData contextId={contextId} product={product} month={month} factory={factory} onOpen={setDrawer} />}
        {pageInfo?.item === '报告模板' && <TemplateCenter />}
        {isAnalysisPage && snapshot && <>
          <DecisionCard selection={selection} onApplied={refresh} onError={message => { if (currentContext.current === contextId) setError(message); }} />
          <Analysis key={`${contextId}:${snapshot.snapshot_id}`} snapshot={snapshot} basis={basis} onEvidence={setDrawer} />
        </>}
        {isAnalysisPage && catalog && selection.context_id === contextId && <ProductMonthHeatmap key={contextId} selection={selection} onSelect={(product, month) => setSelection(s => ({ ...s, product, month, analysis_type: 'monthly' }))} />}
        {pageInfo?.item === '跨厂对标' && <>
          <div className="comparison-filters">
            <label>分析工厂<select aria-label="分析工厂" value={left} onChange={e => { setLeft(e.target.value); setBenchmark(null); }}>{catalog?.factories.map((f: string) => <option key={f} disabled={f === right}>{f}</option>)}</select></label>
            <label>基准工厂<select aria-label="基准工厂" value={right} onChange={e => { setRight(e.target.value); setBenchmark(null); }}>{catalog?.factories.map((f: string) => <option key={f} disabled={f === left}>{f}</option>)}</select></label>
          </div>
          {!catalog || catalog.factories.length < 2 ? <p className="notice">当前数据范围仅有一个工厂，跨厂对标不可用。</p> : <Benchmark data={benchmark} analysisType={analysis_type} onSwap={() => { setLeft(right); setRight(left); setBenchmark(null); }} onEvidence={setDrawer} />}
        </>}
        {pageInfo?.item === '报告生成' && <ReportGeneration selection={selection} snapshot={snapshot} jobs={jobs} refresh={refresh} onError={message => { if (currentContext.current === contextId) setError(message); }} />}
        {pageInfo?.item === '问题整改' && <Rectification selection={selection} snapshot={snapshot} jobs={jobs} actions={actions} refresh={refresh} onError={message => { if (currentContext.current === contextId) setError(message); }} />}
        {pageInfo?.item === '数据提取模型' && <ExtractionModel />}
        {pageInfo?.item === '数据分析模型' && <AnalysisModel />}
        {pageInfo?.item === '向量模型' && <VectorModel />}
        <footer>成本共变仅支持原因假设；生产变更与整改完成均须人工确认。证据不足的结论明确标注，不由模型补全。</footer>
      </main>
    </div>
    {drawer && <EvidenceDrawer value={drawer} onClose={closeDrawer} />}
  </div>;
}
function ErrorBox({ message, onRetry }: { message: string; onRetry: () => void }) {
  return <div className="error" role="alert">请求失败：{message}<button className="retry" onClick={onRetry}>重试</button></div>;
}
const capabilityText = (value: string) => String(value).replaceAll('pdf_service', 'PDF 转换服务').replaceAll('model_service', '应用模型服务').replaceAll('rpa_service', '模拟任务服务');
function Capabilities({ value }: { value: any }) {
  if (value === null || value === undefined) return null;
  const rows = Array.isArray(value) ? value : Object.entries(value).map(([key, v]) => typeof v === 'object' && v !== null ? { key, ...v as any } : { key, status: v === true ? 'AVAILABLE' : 'UNAVAILABLE' });
  return <details className="capabilities"><summary>当前分析能力与数据缺口</summary>
    {rows.length
      ? <ul>{rows.map((v: any, i: number) => <li key={v.key ?? v.id ?? i}><strong>{v.label ?? v.name ?? v.key ?? v.id}</strong>：{({ AVAILABLE: '可用', PASS: '可用', DEGRADED: '降级', BLOCKED: '不可用', UNAVAILABLE: '不可用', MISSING_DATA: '缺少数据' } as Record<string, string>)[String(v.status).toUpperCase()] ?? v.status ?? '待核验'}{v.reason ? `；${capabilityText(v.reason)}` : ''}{(v.missing_fields ?? v.missing)?.length ? `；需补充 ${(v.missing_fields ?? v.missing).map(capabilityText).join('、')}` : ''}</li>)}</ul>
      : <p className="muted capabilities-empty">当前数据范围未报告能力缺口：成本分析、报告导出与知识检索均可正常使用。</p>}
  </details>;
}
