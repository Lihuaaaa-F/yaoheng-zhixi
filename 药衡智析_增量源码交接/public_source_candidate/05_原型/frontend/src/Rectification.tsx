import { snapshotReport } from './NarrativePanel';
import { useState, useEffect } from 'react';
import { api, Selection } from './api';
import { cleanText, DeveloperDetails } from './presentation';

const taskLabel = (s: string) => ({ DRAFT: '待确认', PENDING_CONFIRMATION: '待确认', QUEUED: '等待发送', SENDING: '正在发送', SENT: '模拟通知已发送', ACCEPTED: '远端已接收，通知未确认', DELIVERY_UNKNOWN: '投递结果未知', FAILED: '发送未通过', CONFLICT: '内容冲突' }[s] ?? '待查询');
const normalizedPriority = (value: string) => ({ 高: 'high', 中: 'medium', 低: 'low', high: 'high', medium: 'medium', low: 'low' }[value] ?? 'medium');
const isActionable = (f: any) => [f.suggestion, f.verification_target, f.responsible_role, f.deadline_basis, ...(Array.isArray(f.expected_evidence) ? f.expected_evidence : [])].every(v => typeof v === 'string' && v.trim() && !/\[\[.+?\]\]|\{\{.+?\}\}/.test(v)) && Array.isArray(f.expected_evidence) && f.expected_evidence.length > 0;

/** 工作台 · 问题整改：企业任务看板 + 报告建议转整改任务草稿 + 发送与确认跟踪。 */
export default function Rectification({ selection, snapshot, jobs, actions, refresh, onError }: {
  selection: Selection; snapshot: any; jobs: any[]; actions: any[]; refresh: () => Promise<void>; onError: (s: string) => void;
}) {
  const [showHistory, setShowHistory] = useState(false);
  const [acknowledging, setAcknowledging] = useState<string | null>(null), [confirmationName, setConfirmationName] = useState(''), [confirmationComment, setConfirmationComment] = useState('');
  const [pending, setPending] = useState(false), [notice, setNotice] = useState(''), [name, setName] = useState('待分配'), [department, setDepartment] = useState('生产管理部'), [finding, setFinding] = useState(''), [suggestion, setSuggestion] = useState(''), [target, setTarget] = useState(''), [expected, setExpected] = useState(''), [role, setRole] = useState('待分配'), [priority, setPriority] = useState('medium'), [deadlineBasis, setDeadlineBasis] = useState(''), [deadline, setDeadline] = useState(''), [editing, setEditing] = useState<string | null>(null);
  // 2026-09-24（AUD-FE-01）：默认按当前选择过滤（快照可能未随筛选刷新）；
  // 历史任务用"查看全部任务"查看。
  const matchesSelection = (a: any) => a.payload?.source?.analysis_month === selection.month
    && a.payload?.source?.product === selection.product
    && a.metadata?.context_id === selection.context_id;
  const visibleActions = showHistory ? actions : actions.filter(matchesSelection);
  const currentReport = snapshotReport(jobs, snapshot?.snapshot_id);
  const availableFindings = (currentReport?.result?.narrative?.findings ?? []).filter(isActionable);
  useEffect(() => { setFinding(''); setSuggestion(''); setTarget(''); setExpected(''); setDeadlineBasis(''); setEditing(null); }, [snapshot?.snapshot_id]);
  const run = async (fn: () => Promise<void>) => {
    setPending(true); onError('');
    try { await fn(); await refresh(); }
    catch (e) { onError(e instanceof Error ? e.message : String(e)); }
    finally { setPending(false); }
  };
  const payload = () => ({ context_id: selection.context_id, snapshot_id: snapshot.snapshot_id, finding, assignee: { name, department }, suggestion, priority, verification_target: target, expected_evidence: expected.split(/[；\n]/).map(s => s.trim()).filter(Boolean), responsible_role: role, deadline_basis: deadlineBasis, ...(editing && deadline ? { deadline } : {}) });
  const uniqueActions = [...new Map(actions.map(a => [a.id, a])).values()];
  const delivered = uniqueActions.filter(a => a.delivery?.notification === 'SIMULATED_SENT').length;
  const ownerConfirmed = uniqueActions.filter(a => a.responsibility_confirmation?.status === 'CONFIRMED' && a.responsibility_confirmation?.confirmed_by && a.responsibility_confirmation?.confirmed_at).length;
  return <>
    <section className="panel"><h2>企业任务看板</h2>
      <div className="task-summary" aria-label="任务状态汇总"><div><span>已生成任务</span><strong>{uniqueActions.length}</strong></div><div><span>模拟通知送达</span><strong>{delivered}</strong></div><div><span>责任人确认</span><strong>{ownerConfirmed}</strong></div></div>
      <p className="muted">汇总当前数据范围全部任务，以任务 ID 去重；模拟送达按通知回执统计。责任人确认须有署名与时间记录，发送前确认不计入，送达不等于整改完成。</p></section>
    <section className="panel"><h2>建议转为模拟整改任务</h2>
      <p className="notice">仅将实际核查建议转为草稿。具体姓名未知时保留“待分配”；确认当前完整内容后才发送题包模拟通知。</p>
      <label className="finding-select">载入当前报告建议<select aria-label="载入当前报告建议" defaultValue="" key={snapshot?.snapshot_id} onChange={e => {
        const f = availableFindings[Number(e.target.value)]; if (!f) return;
        setFinding(cleanText(f.rendered_text ?? f.text_template)); setSuggestion(cleanText(f.suggestion)); setTarget(f.verification_target ?? '');
        setExpected(Array.isArray(f.expected_evidence) ? f.expected_evidence.join('；') : f.expected_evidence ?? '');
        setRole(f.responsible_role ?? '待分配'); setDepartment(f.department ?? '生产管理部'); setPriority(normalizedPriority(f.priority)); setDeadlineBasis(f.deadline_basis ?? '');
      }}><option value="">选择可执行建议，或手动填写</option>{availableFindings.map((f: any, i: number) => <option key={i} value={i}>{cleanText(f.suggestion).slice(0, 100)}</option>)}</select></label>
      {!availableFindings.length && <p className="muted">当前报告尚无可载入的行动建议。请先在「报告生成」页生成当前报告，或补充核查对象、所需证据和具体行动。</p>}
      <div className="form-grid">
        <label>责任人<input aria-label="责任人" value={name} onChange={e => setName(e.target.value)} /></label>
        <label>部门<input aria-label="部门" value={department} onChange={e => setDepartment(e.target.value)} /></label>
        <label>责任角色<input aria-label="责任角色" value={role} onChange={e => setRole(e.target.value)} /></label>
        <label>优先级<select aria-label="优先级" value={priority} onChange={e => setPriority(e.target.value)}><option value="high">高</option><option value="medium">中</option><option value="low">低</option></select></label>
        <label className="full">业务问题<textarea aria-label="业务问题" value={finding} onChange={e => setFinding(e.target.value)} /></label>
        <label className="full">核查对象<input aria-label="核查对象" value={target} onChange={e => setTarget(e.target.value)} /></label>
        <label className="full">预期证据<textarea aria-label="预期证据" value={expected} onChange={e => setExpected(e.target.value)} /></label>
        <label className="full">建议内容<textarea aria-label="建议内容" value={suggestion} onChange={e => setSuggestion(e.target.value)} /></label>
        <label className="full">期限依据<input aria-label="期限依据" placeholder="例如：在下次月度成本复盘前，具体日期由责任部门确认" value={deadlineBasis} onChange={e => setDeadlineBasis(e.target.value)} /></label>
        {editing && <label className="full">建议截止日期（确认前可调整）<input aria-label="建议截止日期" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} /></label>}
      </div>
      <button disabled={pending || !snapshot || ![name, department, role, finding, suggestion, target, expected, deadlineBasis].every(s => s.trim())} onClick={() => run(async () => {
        if (editing) { await api(`/actions/${editing}`, payload(), undefined, 'PUT'); setEditing(null); setNotice('草稿已更新，须重新核对确认。'); }
        else { await api('/actions', payload()); setNotice('草稿已生成，尚未发送。请核对下方完整内容。'); }
      })}>{editing ? '保存草稿修改' : '生成任务草稿'}</button></section>
    <section className="panel">
      <div className="panel-heading"><h2>任务与发送状态</h2>
        <div className="button-row"><label className="history-toggle"><input type="checkbox" checked={showHistory} onChange={e => setShowHistory(e.target.checked)} /> 查看全部任务</label>
          <button onClick={() => run(refresh)} disabled={pending}>刷新状态</button></div></div>
      <p className="muted">默认按当前分析筛选（{selection.factory} · {selection.product} · {selection.month}）；与上方企业汇总口径不同。</p>
      {!visibleActions.length ? <p className="empty">当前分析暂无任务。当前数据范围共 {uniqueActions.length} 条任务（见上方汇总），可勾选“查看全部任务”。</p> : visibleActions.map(a => {
        const p = a.payload ?? {}, m = a.metadata ?? {};
        return <article className="task" data-task-id={a.id} key={a.id}>
          <div className="panel-heading"><strong>{p.task_title ?? '核查任务'}</strong><span className="badge">{taskLabel(a.status)}</span></div>
          <dl className="task-details">
            <dt>责任人</dt><dd>{p.assignee?.name || '待分配'} · {p.assignee?.department}</dd>
            <dt>责任角色</dt><dd>{p.action_details?.responsible_role ?? p.responsible_role ?? m.responsible_role ?? '待分配'}</dd>
            <dt>业务问题</dt><dd>{p.source?.finding}</dd>
            <dt>核查对象</dt><dd>{p.action_details?.verification_target ?? p.verification_target ?? m.verification_target ?? '历史任务未记录'}</dd>
            <dt>预期证据</dt><dd>{(p.action_details?.expected_evidence ?? p.expected_evidence ?? m.expected_evidence ?? []).join?.('；') || '历史任务未记录'}</dd>
            <dt>建议</dt><dd>{p.suggestion}</dd>
            <dt>优先级</dt><dd>{{ high: '高', medium: '中', low: '低' }[p.priority as string] ?? '待确认'}</dd>
            <dt>期限依据</dt><dd>{p.action_details?.deadline_basis ?? p.deadline_basis ?? m.deadline_basis ?? '历史任务未记录，须复核'}</dd>
            <dt>截止日期</dt><dd>{p.deadline ?? '待责任部门确认'}{m.deadline_policy && <p className="muted">{m.deadline_policy}</p>}</dd>
            <dt>接口请求</dt><dd>{a.delivery?.http_accepted === true ? '远端已确认接收' : a.status === 'DELIVERY_UNKNOWN' ? '请求结果未知，等待查询' : '以实际发送记录为准'}</dd>
            <dt>模拟通知</dt><dd>{a.delivery?.notification === 'SIMULATED_SENT' ? '原 mock 已记录模拟发送' : '未确认发送'}</dd>
            <dt>整改进度</dt><dd>{a.delivery?.remediation === 'completed' ? '原 mock 记录完成；真实整改仍须人工验收' : a.delivery?.remediation === 'in_progress' ? '原 mock 记录处理中；真实进度待人工核查' : '待人工跟进，模拟发送不代表整改完成'}</dd>
          </dl>
          {['DRAFT', 'draft', 'PENDING_CONFIRMATION'].includes(a.status)
            ? <div className="button-row"><button disabled={pending} onClick={() => {
              setEditing(a.id); setDeadline(p.deadline ?? ''); setName(p.assignee?.name ?? '待分配'); setDepartment(p.assignee?.department ?? '');
              setFinding(p.source?.finding?.split('；分析期间：')[0] ?? ''); setSuggestion(p.suggestion ?? '');
              setTarget(p.action_details?.verification_target ?? p.verification_target ?? m.verification_target ?? '');
              setExpected((p.action_details?.expected_evidence ?? p.expected_evidence ?? m.expected_evidence ?? []).join('；'));
              setRole(p.action_details?.responsible_role ?? p.responsible_role ?? m.responsible_role ?? '待分配');
              setDeadlineBasis(p.action_details?.deadline_basis ?? p.deadline_basis ?? m.deadline_basis ?? ''); setPriority(normalizedPriority(p.priority)); setNotice('编辑后需要重新确认。');
            }}>编辑草稿</button>
              <button className="primary" disabled={pending || editing === a.id} onClick={() => run(async () => {
                await api(`/actions/${encodeURIComponent(a.id)}/confirm`, { payload_hash: a.payload_hash });
                setNotice('已确认，等待发送处理；请分别核对接口、模拟通知与整改状态。');
              })}>确认并发送模拟通知</button></div>
            : <button disabled={pending} onClick={() => run(async () => { await api(`/actions/${encodeURIComponent(a.id)}/refresh`, {}); })}>查询模拟通知状态</button>}
          {a.responsibility_confirmation?.status === 'CONFIRMED'
            ? <p className="notice">责任人确认：{a.responsibility_confirmation.confirmed_by} · {a.responsibility_confirmation.confirmed_at}。已确认跟进，不代表整改完成。</p>
            : ['SENT', 'ACCEPTED'].includes(a.status) && <div className="responsibility-confirmation">{acknowledging === a.id
              ? <><p className="notice">由实际责任人填写姓名，确认已收到并将跟进此任务。这不会登记整改完成或报告人工评分。</p>
                <label>责任确认人姓名<input aria-label="责任确认人姓名" placeholder="请责任人本人填写" value={confirmationName} onChange={e => setConfirmationName(e.target.value)} /></label>
                <label>确认备注<input aria-label="责任确认备注" value={confirmationComment} onChange={e => setConfirmationComment(e.target.value)} /></label>
                <div className="button-row"><button disabled={pending || !confirmationName.trim()} onClick={() => run(async () => {
                  await api(`/actions/${encodeURIComponent(a.id)}/acknowledge`, { confirmed_by: confirmationName.trim(), comment: confirmationComment.trim() });
                  setAcknowledging(null); setConfirmationName(''); setConfirmationComment(''); setNotice('已登记责任人确认；整改完成仍需后续核查。');
                })}>确认本人将跟进</button><button disabled={pending} onClick={() => setAcknowledging(null)}>取消</button></div></>
              : <button disabled={pending} onClick={() => { setAcknowledging(a.id); setConfirmationName(''); setConfirmationComment(''); }}>登记责任人确认</button>}</div>}
          {a.error && <p className="error">本次任务处理未通过。可点击“查询模拟通知状态”刷新；仍失败时请查看后端服务日志。</p>}
          <DeveloperDetails value={a} />
        </article>;
      })}
    </section>
  </>;
}
