import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Button, Dropdown, Input, Popconfirm, Space, Tag, Tooltip } from 'antd';
import { BarChartOutlined, CheckOutlined, DoubleRightOutlined, DownOutlined, FileTextOutlined, HistoryOutlined, FileSearchOutlined, PlusOutlined, RobotOutlined, SendOutlined, StopOutlined } from '@ant-design/icons';
import { api, Selection } from './api';

type Message = { id: string; context?: Partial<Selection>; mode?:string;model?:string;model_status?:string;related_reports?:any[];related_tasks?:any[]; role: string; content: string; created_at?: string; facts?: any[]; sources?: any[]; proposals?: any[]; status?: string };
type Conversation = { id: string; title?: string; context?: any; selection?: Selection; messages: Message[] };
const stages: Record<string, string> = { queued: '等待处理', running: '分析中', completed: '已完成', failed: '未完成', cancelled: '已取消', context: '读取当前数据', analysis: '核对成本指标', retrieval: '检索适用证据', planning: '组织查询步骤', model: '生成解释', answering: '整理结果', tools: '查询系统数据' };
const labelStage = (stage: string) => stages[stage?.toLowerCase()] ?? '正在处理请求';
const effortLabels: Record<string,string> = {'':'默认',none:'关闭',minimal:'最少',low:'低',medium:'中',high:'高',xhigh:'最高',max:'最大'};
function remainingColor(ratio:number|null){
 if(ratio===null)return '#a5afb5';
 const stops:[number,string][]=[[.05,'#dc3545'],[.2,'#d99b00'],[.4,'#2f6feb'],[.6,'#2f9e44']];
 if(ratio<=stops[0][0])return stops[0][1];if(ratio>=stops[stops.length-1][0])return stops[stops.length-1][1];
 const high=stops.findIndex(([value])=>value>=ratio),[from,a]=stops[high-1],[to,b]=stops[high],t=(ratio-from)/(to-from);
 return `rgb(${[1,3,5].map(index=>Math.round(parseInt(a.slice(index,index+2),16)*(1-t)+parseInt(b.slice(index,index+2),16)*t)).join(',')})`;
}

const scope = (value?: Partial<Selection>) => value ? [value.product, value.benchmark_right ? `分析工厂 ${value.factory} / 基准 ${value.benchmark_right}` : value.factory, value.month, value.analysis_type === 'quarterly' ? '季度' : value.analysis_type === 'special' ? '专题' : '月度', value.basis === 'total' ? '总额' : '单位成本'].filter(Boolean).join(' · ') : '';

export default function AssistantDock({ selection, onClose, onEvidence, onApplied, onConfigure }: { selection: Selection; onClose: () => void; onEvidence: (value: any) => void; onApplied: (value: any) => void; onConfigure: () => void }) {
  const [conversation, setConversation] = useState<Conversation | null>(null), [history, setHistory] = useState<any[]>([]);
  const [draft, setDraft] = useState(''), [busy, setBusy] = useState(()=>Boolean(sessionStorage.getItem('pharma-assistant-turn'))), [turn, setTurn] = useState<any>(()=>{const id=sessionStorage.getItem('pharma-assistant-turn');return id?{id,status:'queued'}:null}), [error, setError] = useState('');
  const [model, setModel] = useState<any>(null), [retryText, setRetryText] = useState('');
  const [selectedModel, setSelectedModel] = useState(''), [effort, setEffort] = useState(''), [modelOptions, setModelOptions] = useState<string[]>([]), [usage, setUsage] = useState<any>(null);
  const [confirming, setConfirming] = useState('');
  const [modelsRead,setModelsRead]=useState(false);
  const scroll = useRef<HTMLDivElement>(null), activeConversation = useRef(sessionStorage.getItem('pharma-assistant-conversation')??'');
  const loadModel = useCallback(() => Promise.all([api('/settings/models'),api('/settings/models/presets')]).then(([value,presets]) => {const connection=value.connections?.assistant??{};setModel(connection);setSelectedModel(current=>current||connection.effective?.model||connection.model||'');setEffort(current=>current||connection.effective?.reasoning_effort||connection.reasoning_effort||'');setModelOptions([...new Set<string>([connection.effective?.model,connection.model,...[...(presets.api_vendors??[]),...(presets.local_vendors??[])].filter((vendor:any)=>vendor.id===connection.vendor||vendor.base_url===connection.base_url).flatMap((vendor:any)=>(vendor.models??[]).map((item:any)=>item.id))].filter(Boolean))]);}).catch(() => setModel(null)), []);
  const loadHistory = useCallback(() => api('/assistant/conversations').then(value => setHistory(Array.isArray(value) ? value : value.conversations ?? [])).catch(e => setError(e.message)), []);
  useEffect(() => { void loadModel(); void loadHistory(); if(activeConversation.current)void loadConversation(activeConversation.current).catch(()=>{sessionStorage.removeItem('pharma-assistant-conversation');activeConversation.current='';setBusy(false);setTurn(null);sessionStorage.removeItem('pharma-assistant-turn')}); const reload=()=>{setSelectedModel('');setEffort('');setModelsRead(false);void loadModel();};window.addEventListener('pharma:model-saved',reload);return()=>window.removeEventListener('pharma:model-saved',reload); }, [loadModel, loadHistory]);
  useEffect(()=>{setUsage(null);if(!selection.context_id||!selection.factory||!selection.product||!selection.month){setUsage(null);return;}const controller=new AbortController();const timer=setTimeout(()=>{api('/assistant/context',{conversation_id:conversation?.id,selection,text:draft,overrides:{...(selectedModel.trim()?{model:selectedModel.trim()}:{}),reasoning_effort:effort}},controller.signal).then(value=>{if(!controller.signal.aborted)setUsage(value)}).catch(()=>{if(!controller.signal.aborted)setUsage(null)})},450);return()=>{clearTimeout(timer);controller.abort()}},[conversation?.id,conversation?.messages?.length,selection,draft,selectedModel,effort,model]);
  useEffect(()=>setUsage(null),[selectedModel]);
  const readModels=async(open:boolean)=>{if(!open||!model?.configured||modelsRead)return;setModelsRead(true);try{const value=await api('/settings/models/list?route=assistant',{model:selectedModel});if(value.models?.length)setModelOptions([...new Set<string>([selectedModel,...value.models.map((item:any)=>typeof item==='string'?item:item.id)].filter(Boolean))]);}catch{/* Manual names and provider presets remain available in model connections. */}};
  const loadConversation = async (id: string) => {
    const result = await api(`/assistant/conversations/${encodeURIComponent(id)}`);
    if (activeConversation.current === id) setConversation(result);
    return result;
  };
  useEffect(() => {
    if (!turn?.id || !['queued', 'running'].includes(String(turn.status).toLowerCase())) return;
    const controller = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const result = await api(`/assistant/turns/${encodeURIComponent(turn.id)}`, undefined, controller.signal);
        if (controller.signal.aborted) return;
        const terminal = ['completed', 'failed', 'cancelled'].includes(String(result.status).toLowerCase());
        setTurn(result);
        if (terminal) {
          setBusy(false); sessionStorage.removeItem('pharma-assistant-turn');
          if (result.status === 'failed') setError(result.error ?? '本次请求未完成，请重试。');
          await loadConversation(activeConversation.current); void loadHistory();
        } else timer = setTimeout(poll, 1200);
      } catch (e: any) { if (!controller.signal.aborted) { setError(`进度读取失败：${e.message}`); timer = setTimeout(poll, 3000); } }
    };
    void poll(); return () => { controller.abort(); clearTimeout(timer); };
  }, [turn?.id, turn?.status, loadHistory]);
  useEffect(() => { scroll.current?.scrollTo({ top: scroll.current.scrollHeight, behavior: 'auto' }); }, [conversation?.messages?.length, turn?.stage]);
  const validSelection = Boolean(selection.context_id && selection.product && selection.factory && selection.month);
  const send = async (text = draft) => {
    if (!text.trim() || busy || !validSelection) return;
    setBusy(true); setError(''); setRetryText(text); setDraft('');
    try {
      let id = conversation?.id;
      if (!id) { const created = await api('/assistant/conversations', { selection }); id = created.id; activeConversation.current = id!; sessionStorage.setItem('pharma-assistant-conversation',id!); setConversation({ ...created, messages: created.messages ?? [] }); }
      const result = await api(`/assistant/conversations/${encodeURIComponent(id!)}/messages`, { text: text.trim(), selection, client_request_id: crypto.randomUUID(), overrides: { ...(selectedModel.trim()?{model:selectedModel.trim()}:{}), reasoning_effort: effort } });
      sessionStorage.setItem('pharma-assistant-turn',result.turn_id??result.id); setTurn({ ...result, id: result.turn_id ?? result.id }); await loadConversation(id!); void loadHistory();
    } catch (e: any) { setBusy(false); setError(e.message); }
  };
  const cancel = async () => {
    if (!turn?.id) return;
    try { const value = await api(`/assistant/turns/${encodeURIComponent(turn.id)}/cancel`, {}); setTurn(value); setBusy(false); sessionStorage.removeItem('pharma-assistant-turn'); await loadConversation(activeConversation.current); }
    catch (e: any) { setError(e.message); }
  };
  const pick = async (id: string) => {
    if (busy) return;
    activeConversation.current = id; sessionStorage.setItem('pharma-assistant-conversation',id); setError(''); setTurn(null);
    try { await loadConversation(id); } catch (e: any) { setError(e.message); }
  };
  const confirm = async (proposal: any) => {
    setConfirming(proposal.id); setError('');
    try { const result = await api(`/assistant/proposals/${encodeURIComponent(proposal.id)}/confirm`, {}); await loadConversation(activeConversation.current); onApplied(result); }
    catch (e: any) { setError(e.message); } finally { setConfirming(''); }
  };
  const previousSelection = conversation?.selection ?? conversation?.context?.selection ?? conversation?.context;
  const scopeChanged = previousSelection?.context_id && ['context_id', 'factory', 'product', 'month', 'analysis_type', 'basis', 'benchmark_right'].some(key => previousSelection[key] !== (selection as any)[key]);
  return <section className="assistant-panel" aria-label="AI 助手">
    <header className="assistant-header"><h2><RobotOutlined /> AI 助手</h2><Space size={2}>
      <Tooltip title="新建对话"><Button className="assistant-new-conversation" type="text" icon={<PlusOutlined />} aria-label="新建对话" disabled={busy} onClick={() => { activeConversation.current = ''; sessionStorage.removeItem('pharma-assistant-conversation'); sessionStorage.removeItem('pharma-assistant-turn'); setConversation(null); setTurn(null); setError(''); setDraft(''); }}>新建对话</Button></Tooltip>
      <Dropdown trigger={['click']} menu={{ items: history.map(item => ({ key: item.id, label: item.title || '成本分析对话' })), onClick: ({ key }) => pick(key) }} disabled={busy || !history.length}><Button type="text" icon={<HistoryOutlined />} aria-label="对话历史" /></Dropdown>
      <Button type="text" icon={<DoubleRightOutlined />} aria-label="收起 AI 助手" onClick={onClose} />
    </Space></header>
    <div className="assistant-scroll" ref={scroll}>
      {scopeChanged && <Alert type="info" showIcon title="数据范围已切换" description="历史消息保留原范围；新请求会核对当前选择。建议新建对话以区分不同分析。" />}
      {!conversation?.messages?.length && <div className="assistant-empty"><RobotOutlined /><h3>想了解哪一项成本变化？</h3><p>查看当前数据、核对证据，或准备下一步行动。</p><div className="assistant-starters">{[{label:'解释变化',text:'解释当前成本变化',icon:<BarChartOutlined/>},{label:'核查数据',text:'检查数据和证据缺口',icon:<FileSearchOutlined/>},{label:'准备报告',text:'准备当前范围的分析报告',icon:<FileTextOutlined/>}].map(item => <Button key={item.text} icon={item.icon} disabled={!validSelection || busy} onClick={() => send(item.text)}>{item.label}</Button>)}</div></div>}
      {conversation?.messages?.map(message => <article key={message.id} className={`assistant-message ${message.role === 'user' ? 'from-user' : 'from-assistant'}`}>
        <div className="assistant-message-label">{message.role === 'user' ? '你' : 'AI 助手'}{message.mode&&<span>{message.mode==='model'?`模型解释${message.model?` · ${message.model}`:''}`:'规则分析'}</span>}{message.status && <Tag>{labelStage(message.status)}</Tag>}</div>
        <div className="assistant-message-text">{message.content}</div>
        {!!message.facts?.length && <><dl className="assistant-facts">{message.facts.slice(0,4).map((fact, i) => <div key={fact.ref ?? i}><dt>{fact.label}</dt><dd>{String(fact.value ?? '—')} {fact.unit ?? ''}</dd></div>)}</dl>{message.facts.length>4&&<details className="assistant-more"><summary>其余 {message.facts.length-4} 项指标</summary><dl className="assistant-facts">{message.facts.slice(4).map((fact,i)=><div key={fact.ref??i}><dt>{fact.label}</dt><dd>{String(fact.value??'—')} {fact.unit??''}</dd></div>)}</dl></details>}</>}
        {!!message.related_reports?.length&&<div className="assistant-related"><strong>相关报告</strong>{message.related_reports.map((item,index)=><p key={index}>{item.product} · {item.month} · {({SUCCEEDED:'生成完成',DEGRADED:'已生成，存在降级项',FAILED:'生成失败',QUEUED:'等待处理',RUNNING:'处理中'} as Record<string,string>)[item.status]??'状态待核验'}</p>)}</div>}
        {!!message.related_tasks?.length&&<div className="assistant-related"><strong>相关整改任务</strong>{message.related_tasks.map((item,index)=><p key={index}>{item.title} · {({DRAFT:'草稿',CONFIRMED:'已确认',SENT:'接口已接收',FAILED:'处理失败',PENDING:'待处理',COMPLETED:'已记录完成'} as Record<string,string>)[item.status]??'请在整改页核对状态'}</p>)}</div>}
        {!!message.sources?.length && <div className="assistant-sources"><strong>依据</strong>{message.sources.slice(0,3).map((source, i) => <button key={source.source_id ?? i} onClick={() => onEvidence({ ...source, source: source.title, context_id: message.context?.context_id ?? source.context_id ?? conversation?.context?.context_id })}><FileTextOutlined /><span>{source.title ?? '相关资料'}{source.page ? ` · 第 ${source.page} 页` : ''}</span></button>)}{message.sources.length>3&&<details className="assistant-more"><summary>其余 {message.sources.length-3} 份引用</summary>{message.sources.slice(3).map((source,i)=><button key={source.source_id??i} onClick={()=>onEvidence({...source,source:source.title,context_id:message.context?.context_id??source.context_id??conversation?.context?.context_id})}><FileTextOutlined/><span>{source.title??'相关资料'}{source.page?` · 第 ${source.page} 页`:''}</span></button>)}</details>}</div>}
        {message.proposals?.map(proposal => <div className="assistant-proposal" key={proposal.id}><strong>{proposal.title}</strong><p>{proposal.description}</p>{proposal.status === 'confirmed' ? <Tag color="success">已确认</Tag> : <Popconfirm title={proposal.kind === 'draft_task' ? '创建整改草稿？' : '生成此范围的报告？'} description="将使用该建议绑定的数据版本；外部发送仍需在整改页确认。" okText="确认执行" cancelText="返回" onConfirm={() => confirm(proposal)}><Button type="primary" size="small" loading={confirming === proposal.id}>{proposal.kind === 'draft_task' ? '确认创建草稿' : '确认生成报告'}</Button></Popconfirm>}</div>)}
      </article>)}
      {busy && <div className="assistant-progress" role="status"><span className="working-dot" />{turn?.stage_label??labelStage(turn?.stage ?? turn?.status ?? 'queued')}</div>}
      {turn?.status === 'cancelled' && <p className="muted">已取消本次请求，历史消息仍保留。</p>}
      {usage?.limit_exceeded&&<Alert type="warning" showIcon title="预估内容超过当前上下文窗口，请缩短问题或新建对话。"/>}
      {error && <Alert type="error" showIcon title={error} action={!busy && retryText ? <Button size="small" onClick={() => send(retryText)}>重试</Button> : undefined} />}
    </div>
    <div className="assistant-composer"><div className="assistant-context"><strong>当前范围</strong><span>{validSelection ? scope(selection) : '请先导入数据并选择分析范围'}</span></div>
      <div className="assistant-input-box"><Input.TextArea aria-label="向 AI 助手提问" title="Enter 发送；Shift + Enter 换行" variant="borderless" placeholder="询问当前数据，或提出下一步操作…" autoSize={{ minRows: 3, maxRows: 8 }} value={draft} maxLength={6000} onChange={e => setDraft(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }} />
      <div className="assistant-input-toolbar">
      <Tooltip trigger={['hover','focus']} title={usage?.context_window ? <div>本轮输入估算：{usage.estimated_input_tokens??usage.used_tokens??'—'} tokens（圆环弧长仅表示输入占用）<br/>配置容量：{usage.context_window} tokens<br/>预留输出：{usage.max_output_tokens??'—'} tokens<br/>剩余：{usage.available_tokens??'—'} tokens（颜色按扣除输出预留后的余量变化）<br/>{usage.estimate_note??'输入量为估算，实际消耗以服务商返回为准。'}{usage.last_usage?.total_tokens?<><br/>上次服务端用量：{usage.last_usage.total_tokens} tokens（不是本轮估算）</>:null}</div> : '当前型号未配置上下文窗口，容量与剩余量未知。可在模型连接中按服务商说明填写。'}>
       <button type="button" className="assistant-context-indicator" aria-label={usage?.context_window ? `上下文：估算输入 ${usage.estimated_input_tokens??usage.used_tokens??'未知'} tokens，容量 ${usage.context_window}，预留输出 ${usage.max_output_tokens??'未知'}，剩余 ${usage.available_tokens??'未知'}` : '上下文窗口未知；聚焦查看说明'}>
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="6.5" fill="none" stroke="#dfe5e8" strokeWidth="2.3"/><circle cx="9" cy="9" r="6.5" fill="none" stroke={remainingColor(usage?.context_window&&usage.available_tokens!=null?Number(usage.available_tokens)/Number(usage.context_window):null)} strokeWidth="2.3" strokeLinecap="round" strokeDasharray={`${usage?.context_window&&usage.estimated_input_tokens!=null?Math.max(0,Math.min(1,Number(usage.estimated_input_tokens)/Number(usage.context_window)))*40.84:0} 40.84`} transform="rotate(-90 9 9)"/></svg>
       </button>
      </Tooltip>
      <Dropdown trigger={['click']} disabled={busy} onOpenChange={open=>void readModels(open)} menu={{items:[{type:'group',label:'本次对话的模型',children:(modelOptions.length?modelOptions:selectedModel?[selectedModel]:[]).map(value=>({key:`model:${value}`,label:value,icon:value===selectedModel?<CheckOutlined/>:undefined}))},{type:'divider'},{key:'efforts',label:'推理强度',children:Object.entries(effortLabels).map(([value,label])=>({key:`effort:${value}`,label,icon:value===effort?<CheckOutlined/>:undefined}))},{type:'divider'},{key:'configure',label:'添加型号或配置模型连接'}],onClick:({key})=>{if(key.startsWith('model:'))setSelectedModel(key.slice(6));else if(key.startsWith('effort:'))setEffort(key.slice(7));else if(key==='configure')onConfigure()}}}>
       <Button type="text" className="assistant-inline-model" aria-label={`选择助手模型与推理强度，当前 ${selectedModel||'未选择模型'}，${effortLabels[effort]??effort}`}><span className="assistant-model-name">{selectedModel?selectedModel.replace(/^glm/i,'GLM'):'选择模型'}</span><span className="assistant-effort-name">{effortLabels[effort]??effort}</span><DownOutlined/></Button>
      </Dropdown>
      {busy ? <Tooltip title="停止等待，不发布迟到回答；已发给服务商的请求可能仍计费用。"><Button type="text" aria-label="停止生成" icon={<StopOutlined/>} onClick={cancel}/></Tooltip> : <Button type="primary" aria-label="发送消息" icon={<SendOutlined/>} disabled={!draft.trim()||!validSelection||usage?.limit_exceeded} onClick={()=>send()}/>}</div></div>

    </div>
  </section>;
}
