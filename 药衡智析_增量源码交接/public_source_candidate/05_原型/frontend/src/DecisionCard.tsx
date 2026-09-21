import { useEffect, useState, useRef } from 'react';
import { api, Selection } from './api';

// Agent 自主决策卡（赛题加分项）：展示“生成报告/仅更新看板”的确定性决策、
// 模型选择说明依据与信号依据；REPORT_NEEDED 时可一键按决策入队报告任务。
export default function DecisionCard({ selection, onApplied, onError }: {
    selection: Selection;
    onApplied: () => void;
    onError: (message: string) => void;
}) {
    const [explaining,setExplaining]=useState(false);
    const [data, setData] = useState<any>(null), [applying, setApplying] = useState(false), [applied, setApplied] = useState<string | null>(null), [error, setError] = useState(''), [reload, setReload] = useState(0);
    const key = `${selection.context_id}:${selection.factory}:${selection.product}:${selection.month}:${selection.analysis_type}:${selection.basis}`;
    const currentKey=useRef(key);currentKey.current=key;
    useEffect(() => {
        const c = new AbortController();
        setData(null); setApplied(null);setExplaining(false);setError('');
        const params = new URLSearchParams({ ...selection, with_advisory: 'false' });
        api(`/agent/decision?${params}`, undefined, c.signal).then(x => { if (!c.signal.aborted) setData(x); }).catch(e => { if (!c.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
        return () => c.abort();
    }, [key, reload]);
    if (error && !data) return <section className="panel decision-card" aria-label="Agent 分析决策"><div className="panel-heading"><h2>分析决策 · 确定性规则</h2></div><p className="error" role="alert">决策信息加载失败：{error}</p><button onClick={() => setReload(n => n + 1)}>重试加载</button></section>;
    if (!data) return null;
    const needed = data.decision === 'REPORT_NEEDED';
    const explain = async () => {
        setExplaining(true);
        try { const params=new URLSearchParams({...selection,with_advisory:'true'});const result=await api(`/agent/decision?${params}`);if(currentKey.current===key)setData(result); }
        catch(e){onError(e instanceof Error?e.message:String(e));}
        finally{if(currentKey.current===key)setExplaining(false)}
    };
    const apply = async () => {
        setApplying(true);
        try {
            const r = await api(`/agent/decision/${data.decision_id}/apply`, {});
            setApplied(r.job_id); onApplied();
        } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
        finally { setApplying(false); }
    };
    return <section className="panel decision-card" aria-label="Agent 分析决策">
        <div className="panel-heading"><h2>分析决策 · 确定性规则</h2><span className={needed ? 'outline-label increase' : 'outline-label'}>{needed ? '建议生成正式报告' : '看板更新即可'}</span></div>
        <p>{data.rationale || data.reason}</p>
        <ul className="decision-signals">
            {(data.signals ?? []).map((s: any) => <li key={s.id}><strong>{s.label}</strong>：{String(s.value)}</li>)}
        </ul>
        <p className="muted">决策由确定性规则作出{data.advisory_status === 'PASS' ? `，说明依据由 ${data.advisory_model} 选择，文字由规则生成` : '，未使用模型说明（结论不受影响）'}。决策仅是系统建议；正式发送与人工审核流程不变。</p>
        <details><summary>查看决策技术依据</summary><pre style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{JSON.stringify({policy_version:data.policy_version,advisory_status:data.advisory_status,advisory_model:data.advisory_model,signals:data.signals,applied_job_id:applied},null,2)}</pre></details>
        {data.advisory_status !== 'PASS' && <button disabled={explaining} onClick={()=>void explain()}>{explaining?'正在核验说明依据…':'生成决策说明'}</button>}
        {needed && !applied && <button className="primary" disabled={applying} onClick={() => void apply()}>{applying ? '正在入队…' : '按决策生成报告'}</button>}
        {applied && <p role="status">已按决策入队报告任务，进度见“报告与整改”页签。</p>}
    </section>;
}
