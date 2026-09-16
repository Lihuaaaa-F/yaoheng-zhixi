import { useState, useEffect, useCallback } from 'react';
import { api, Selection } from './api';
import Analysis from './Analysis';
import Benchmark from './Benchmark';
import Tasks from './Tasks';
import Evidence, { EvidenceDrawer } from './Evidence';
const sections = ['成本分析', '跨厂对标', '报告与任务', '数据与证据'];
export default function App() {
    const [tab, setTab] = useState(0), [catalog, setCatalog] = useState<any>(null), [selection, setSelection] = useState<Selection>({ factory: '一厂', product: '银黄口服液', month: '2026-05', analysis_type: 'monthly', basis: 'unit' }), [snapshot, setSnapshot] = useState<any>(null), [benchmark, setBenchmark] = useState<any>(null), [reverse, setReverse] = useState(false), [jobs, setJobs] = useState<any[]>([]), [actions, setActions] = useState<any[]>([]), [error, setError] = useState(''), [loading, setLoading] = useState(false), [drawer, setDrawer] = useState<any>(null);
    useEffect(() => { const c = new AbortController(); api('/catalog', undefined, c.signal).then(x => { setCatalog(x); setSelection(s => ({ ...s, factory: x.factories.includes(s.factory) ? s.factory : x.factories[0], product: x.products.includes(s.product) ? s.product : x.products[0], month: x.months.includes(s.month) ? s.month : x.months.at(-1) })); }).catch(e => { if (e.name !== 'AbortError')
        setError(e.message); }); return () => c.abort(); }, []);
    const { factory, product, month, analysis_type, basis } = selection;
    useEffect(() => { if (!catalog)
        return; const c = new AbortController(); setLoading(true); setError(''); setSnapshot(null); api('/analyses', { factory, product, month, analysis_type, basis }, c.signal).then(setSnapshot).catch(e => { if (e.name !== 'AbortError')
        setError(e.message); }).finally(() => { if (!c.signal.aborted)
        setLoading(false); }); return () => c.abort(); }, [catalog, factory, product, month, analysis_type, basis]);
    useEffect(() => { if (tab !== 1 || !catalog)
        return; const c = new AbortController(); setLoading(true); setError(''); setBenchmark(null); const a = catalog.factories[0], b = catalog.factories[1]; const params = new URLSearchParams({ product, month, left: reverse ? a : b, right: reverse ? b : a }); api(`/benchmarks?${params}`, undefined, c.signal).then(setBenchmark).catch(e => { if (e.name !== 'AbortError')
        setError(e.message); }).finally(() => { if (!c.signal.aborted)
        setLoading(false); }); return () => c.abort(); }, [tab, catalog, product, month, reverse]);
    const refresh = useCallback(async () => { const [j, a] = await Promise.all([api('/jobs'), api('/actions')]); setJobs(Array.isArray(j) ? j : j.jobs ?? []); setActions(Array.isArray(a) ? a : a.actions ?? []); }, []);
    useEffect(() => { if (tab !== 2)
        return; let cancelled = false, timer: ReturnType<typeof setTimeout>; const c = new AbortController(); const poll = async () => { try {
        const [j, a] = await Promise.all([api('/jobs', undefined, c.signal), api('/actions', undefined, c.signal)]);
        if (!cancelled) {
            setJobs(Array.isArray(j) ? j : j.jobs ?? []);
            setActions(Array.isArray(a) ? a : a.actions ?? []);
        }
    }
    catch (e) {
        if (!cancelled)
            setError(e instanceof Error ? e.message : String(e));
    }
    finally {
        if (!cancelled)
            timer = setTimeout(poll, 2000);
    } }; void poll(); return () => { cancelled = true; c.abort(); clearTimeout(timer); }; }, [tab]);
    const closeDrawer = useCallback(() => setDrawer(null), []);
    return <div className="app-shell"><aside className="sidebar"><div className="brand"><span className="brand-mark">衡</span><div><strong>药衡智析</strong><small>产品成本分析工作台</small></div></div><nav aria-label="主导航">{sections.map((s, i) => <button aria-current={tab === i ? 'page' : undefined} className={tab === i ? 'active' : ''} key={s} onClick={() => setTab(i)}><span className="nav-number">0{i + 1}</span>{s}</button>)}</nav><div className="sidebar-footer"><strong>本地演示环境</strong><p>确定性计算 · 可追溯证据<br />原模板报告 · 模拟 RPA</p><span>企业赛题 · 创灵境</span></div></aside>
 <div className="workspace"><header className="topbar"><span>制药企业产品成本智能分析报告系统</span><span className="local-dot">WSL 本地服务</span></header><main><div className="page-heading"><div><h1>{sections[tab]}</h1><p>{['从成本变化追踪数据，连接证据与可核查的行动建议。', '同产品、同规格、同月份，逐层查看工厂差异。', '固定输入版本，生成报告；确认后发送模拟通知。', '核查来源位置、适用范围和证据限制。'][tab]}</p></div><span className="outline-label">题包模拟数据</span></div>
 <section className="filters" aria-label="分析筛选"><label>产品<select aria-label="产品" value={product} onChange={e => setSelection(s => ({ ...s, product: e.target.value }))}>{catalog?.products?.map((p: string) => <option key={p}>{p}</option>)}</select></label><label>工厂<select aria-label="工厂" value={factory} onChange={e => setSelection(s => ({ ...s, factory: e.target.value }))}>{catalog?.factories?.map((f: string) => <option key={f}>{f}</option>)}</select></label><label>月份<select aria-label="月份" value={month} onChange={e => setSelection(s => ({ ...s, month: e.target.value }))}>{catalog?.months?.filter((m: string) => analysis_type !== 'quarterly' || ['03', '06', '09', '12'].includes(m.slice(-2))).map((m: string) => <option key={m}>{m}</option>)}</select></label><label>报告范围<select aria-label="报告范围" value={analysis_type} onChange={e => { const kind = e.target.value as Selection['analysis_type']; setSelection(s => { const quarterEnd = `${s.month.slice(0, 4)}-${String(Math.ceil(Number(s.month.slice(-2)) / 3) * 3).padStart(2, '0')}`; return { ...s, analysis_type: kind, month: kind === 'quarterly' && catalog.months.includes(quarterEnd) ? quarterEnd : s.month }; }); }}><option value="monthly">月度分析</option><option value="quarterly">季度分析</option><option value="special">专题分析</option></select></label><div className="basis"><span>成本口径</span><div role="group" aria-label="成本口径"><button aria-pressed={basis === 'unit'} className={basis === 'unit' ? 'selected' : ''} onClick={() => setSelection(s => ({ ...s, basis: 'unit' }))}>单位</button><button aria-pressed={basis === 'total'} className={basis === 'total' ? 'selected' : ''} onClick={() => setSelection(s => ({ ...s, basis: 'total' }))}>总额</button></div></div></section>
 {analysis_type === 'quarterly' && <p className="notice">季度分析按完整季度汇总，单位成本以产量加权。趋势图仅显示截至所选月的月度数据。</p>}{error && <div className="error" role="alert">请求失败：{error}</div>}{loading && <div className="loading" role="status">正在读取固定版本数据…</div>}
 {tab === 0 && snapshot && <Analysis snapshot={snapshot} basis={basis} onEvidence={setDrawer}/>}{tab === 1 && <Benchmark data={benchmark} onSwap={() => setReverse(r => !r)} onEvidence={setDrawer}/>}{tab === 2 && <Tasks selection={selection} snapshot={snapshot} jobs={jobs} actions={actions} refresh={refresh} onError={setError} demoAssignee={catalog?.demo_assignee}/>}{tab === 3 && <Evidence product={product} month={month} factory={factory} onOpen={setDrawer}/>}
 <footer>本演示用于题包成本分析。设备、市场与成本共变仅支持原因假设；建议中的生产和 GMP 变更须人工批准。</footer></main></div>{drawer && <EvidenceDrawer value={drawer} onClose={closeDrawer}/>}</div>;
}
