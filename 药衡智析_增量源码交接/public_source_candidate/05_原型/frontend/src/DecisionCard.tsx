import { useEffect, useState, useRef } from 'react';
import { api, Selection } from './api';

// Agent 自主决策卡（赛题加分项）：展示“生成报告/仅更新看板”的确定性决策、
// 模型选择说明依据与信号依据；REPORT_NEEDED 时可一键按决策入队报告任务。
const signalExplain: Record<string, string> = {
    active_alerts: '页面存在超阈值成本告警（严格超过 ±10%），规则要求出正式报告供人工核查',
    report_for_period: '判断当前期间是否已有正式报告',
    snapshot_binding: '判断已有报告绑定的数据版本与当前选择是否一致',
    artifact_health: '判断已有报告的文件产物是否可用',
};
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
        <div className="panel-heading"><h2>分析决策建议</h2><span className={needed ? 'outline-label increase' : 'outline-label'}>{needed ? '建议生成正式报告' : '看板更新即可'}</span></div>
        <p>{data.rationale || data.reason}</p>
        <ul className="decision-signals">
            {(data.signals ?? []).map((s: any) => <li key={s.id}><strong>{s.label}</strong>：{String(s.value)}</li>)}
        </ul>
        <p className="muted">决策由确定性规则作出{data.advisory_status === 'PASS' ? `，说明依据由 ${data.advisory_model} 选择，文字由规则生成` : '，未使用模型说明（结论不受影响）'}。决策仅是系统建议；正式发送与人工审核流程不变。</p>
        <details><summary>查看决策依据</summary><div className="decision-basis">
            <dl>
                <dt>决策结论</dt><dd>{needed ? '系统判断当前数据版本需要出具一份正式报告' : '系统判断本次仅更新看板即可，无需出具新报告'}。</dd>
                <dt>触发信号</dt><dd><ul>{(data.signals ?? []).map((s: any) => <li key={s.id}><strong>{s.label}</strong>：{String(s.value)}——{signalExplain[s.id] ?? '按决策规则参与判断'}。</li>)}</ul></dd>
                <dt>说明依据</dt><dd>{data.advisory_status === 'PASS' ? `由模型 ${data.advisory_model} 提供说明依据；决策结论仍由规则决定，模型不改变结论。` : '本次决策未使用模型说明；结论完全由确定性规则得出。'}</dd>
                <dt>规则版本</dt><dd>决策规则 {data.policy_version}。</dd>
                {applied && <><dt>已执行</dt><dd>已按此决策入队报告，进度见「分析报告」页。</dd></>}
            </dl>
            <p className="muted">完整机器可读数据见报告任务的机器审计附件。</p>
        </div></details>
        {data.advisory_status !== 'PASS' && <button disabled={explaining} onClick={()=>void explain()}>{explaining?'正在核验说明依据…':'生成决策说明'}</button>}
        {needed && !applied && <button className="primary" disabled={applying} onClick={() => void apply()}>{applying ? '正在入队…' : '按决策生成报告'}</button>}
        {applied && <p role="status">已按决策入队报告任务，进度见“分析报告”页。</p>}
    </section>;
}
