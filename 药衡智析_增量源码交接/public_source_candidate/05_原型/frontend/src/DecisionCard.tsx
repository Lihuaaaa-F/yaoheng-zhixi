import { useEffect, useState } from 'react';
import { api, Selection } from './api';

// Agent 自主决策卡（赛题加分项）：展示“生成报告/仅更新看板”的确定性决策、
// 小模型说明与信号依据；REPORT_NEEDED 时可一键按决策入队报告任务。
export default function DecisionCard({ selection, onApplied, onError }: {
    selection: Selection;
    onApplied: () => void;
    onError: (message: string) => void;
}) {
    const [data, setData] = useState<any>(null), [applying, setApplying] = useState(false), [applied, setApplied] = useState<string | null>(null);
    const key = `${selection.context_id}:${selection.factory}:${selection.product}:${selection.month}:${selection.analysis_type}:${selection.basis}`;
    useEffect(() => {
        const c = new AbortController();
        setData(null); setApplied(null);
        const params = new URLSearchParams({ ...selection, with_advisory: 'true' });
        api(`/agent/decision?${params}`, undefined, c.signal).then(x => { if (!c.signal.aborted) setData(x); }).catch(() => { if (!c.signal.aborted) setData(null); });
        return () => c.abort();
    }, [key]);
    if (!data) return null;
    const needed = data.decision === 'REPORT_NEEDED';
    const apply = async () => {
        setApplying(true);
        try {
            const r = await api(`/agent/decision/${data.decision_id}/apply`, {});
            setApplied(r.job_id); onApplied();
        } catch (e) { onError(e instanceof Error ? e.message : String(e)); }
        finally { setApplying(false); }
    };
    return <section className="panel decision-card" aria-label="Agent 分析决策">
        <div className="panel-heading"><h2>分析决策 · Agent 自主判断</h2><span className={needed ? 'outline-label increase' : 'outline-label'}>{needed ? '建议生成正式报告' : '看板更新即可'}</span></div>
        <p>{data.rationale || data.reason}</p>
        <ul className="decision-signals">
            {(data.signals ?? []).map((s: any) => <li key={s.id}><strong>{s.label}</strong>：{String(s.value)}<small>（{s.detail}）</small></li>)}
        </ul>
        <p className="muted">决策由确定性策略 {data.policy_version} 作出{data.advisory_status === 'PASS' ? `，说明文字由 ${data.advisory_model} 生成` : '，未使用模型说明（结论不受影响）'}。决策仅是系统建议；正式发送与人工审核流程不变。</p>
        {needed && !applied && <button className="primary" disabled={applying} onClick={() => void apply()}>{applying ? '正在入队…' : '按决策生成报告'}</button>}
        {applied && <p role="status">已按决策入队报告任务 <code>{applied.slice(0, 8)}</code>，进度见“报告与任务”页签。</p>}
    </section>;
}
