import { useCallback, useEffect, useRef, useState } from 'react';
import { Alert, Button, Dropdown, Input, Modal, Popconfirm, Segmented, Spin, Tag, Tooltip } from 'antd';
import { BarChartOutlined, CheckOutlined, CloseOutlined, DeleteOutlined, DownOutlined, EllipsisOutlined, FileTextOutlined, HistoryOutlined, FileSearchOutlined, InboxOutlined, PlusOutlined, PushpinFilled, PushpinOutlined, RobotOutlined, SendOutlined, StopOutlined } from '@ant-design/icons';
import { api, Selection } from './api';
import './assistant-tabs.css';

type Message = { id: string; turn_id?: string; context?: Partial<Selection>; mode?: string; model?: string; model_status?: string; related_reports?: any[]; related_tasks?: any[]; role: string; content: string; created_at?: string; facts?: any[]; sources?: any[]; proposals?: any[]; status?: string };
type ChatSummary = { id: string; title?: string; context?: any; selection?: Selection; is_open?: boolean; pinned?: boolean; archived?: boolean; created_at?: string; updated_at?: string };
type Conversation = ChatSummary & { messages: Message[]; active_turn_id?: string | null };
type HistoryMode = 'history' | 'archived';
const stages: Record<string, string> = { queued: '等待处理', running: '分析中', completed: '已完成', failed: '未完成', cancelled: '已取消', context: '读取当前数据', analysis: '核对成本指标', retrieval: '检索适用证据', planning: '组织查询步骤', model: '生成解释', answering: '整理结果', tools: '查询系统数据' };
const labelStage = (stage: string) => stages[stage?.toLowerCase()] ?? '正在处理请求';
// 推理强度三挡（2026-09-24 收窄）：旧 8 挡与后端 EFFORTS 对齐为 低/中/高 + 模型默认。
const effortLabels: Record<string, string> = { '': '跟随模型默认', low: '低', medium: '中', high: '高' };
const chatTitle = (chat: ChatSummary) => chat.title?.trim() || '新对话';
const chatDate = (chat: ChatSummary) => {
  const date = new Date(chat.updated_at || chat.created_at || '');
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
const chatRows = (value: any): ChatSummary[] => Array.isArray(value) ? value : value?.conversations ?? [];
const running = (value: any) => ['queued', 'running'].includes(String(value?.status).toLowerCase());
function remainingColor(ratio: number | null) {
  if (ratio === null) return '#a5afb5';
  const stops: [number, string][] = [[.05, '#dc3545'], [.2, '#d99b00'], [.4, '#2f6feb'], [.6, '#2f9e44']];
  if (ratio <= stops[0][0]) return stops[0][1];
  if (ratio >= stops[stops.length - 1][0]) return stops[stops.length - 1][1];
  const high = stops.findIndex(([value]) => value >= ratio), [from, a] = stops[high - 1], [to, b] = stops[high], t = (ratio - from) / (to - from);
  return 'rgb(' + [1, 3, 5].map(index => Math.round(parseInt(a.slice(index, index + 2), 16) * (1 - t) + parseInt(b.slice(index, index + 2), 16) * t)).join(',') + ')';
}
const scope = (value?: Partial<Selection>) => value ? [value.product, value.benchmark_right ? '分析工厂 ' + value.factory + ' / 基准 ' + value.benchmark_right : value.factory, value.month, value.analysis_type === 'quarterly' ? '季度' : value.analysis_type === 'special' ? '专题' : '月度', value.basis === 'total' ? '总额' : '单位成本'].filter(Boolean).join(' · ') : '';

export default function AssistantDock({ selection, onEvidence, onApplied, onConfigure }: { selection: Selection; onClose?: () => void; onEvidence: (value: any) => void; onApplied: (value: any) => void; onConfigure: () => void }) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [openChats, setOpenChats] = useState<ChatSummary[]>([]);
  const [activeId, setActiveId] = useState('');
  const [draft, setDraft] = useState(''), [turn, setTurn] = useState<any>(null), [error, setError] = useState('');
  const [loadingChat, setLoadingChat] = useState(true), [creating, setCreating] = useState(false), [mutation, setMutation] = useState('');
  const [pendingSends, setPendingSends] = useState<Set<string>>(() => new Set());
  const [model, setModel] = useState<any>(null), [retryText, setRetryText] = useState('');
  const [selectedModel, setSelectedModel] = useState(''), [effort, setEffort] = useState(''), [modelOptions, setModelOptions] = useState<string[]>([]), [usage, setUsage] = useState<any>(null);
  const [confirming, setConfirming] = useState(''), [modelsRead, setModelsRead] = useState(false);
  const [historyMode, setHistoryMode] = useState<HistoryMode | null>(null), [history, setHistory] = useState<ChatSummary[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false), [historyError, setHistoryError] = useState(''), [historySearch, setHistorySearch] = useState('');
  const [pendingDelete, setPendingDelete] = useState<ChatSummary | null>(null), [deleteError, setDeleteError] = useState('');
  const [atLatest, setAtLatest] = useState(true), [jumpedMessage, setJumpedMessage] = useState('');
  const scroll = useRef<HTMLDivElement>(null), activeConversation = useRef('');
  const drafts = useRef(new Map<string, string>()), draftValue = useRef('');
  const preferences = useRef(new Map<string, { model: string; effort: string }>());
  const viewSequence = useRef(0), listSequence = useRef(0), readSequence = useRef(0), historySequence = useRef(0);
  const alive = useRef(true), createPending = useRef(false), mutationPending = useRef(false), sendPending = useRef(new Set<string>());
  const followLatest = useRef(true), previousRendered = useRef('');
  const sendAttempts = useRef(new Map<string, { fingerprint: string; requestId: string }>());
  const busy = running(turn) || pendingSends.has(activeId);
  // 2026-09-24 审查：benchmark_right 由对标页注入，未选右厂时后端 min_length=1
  // 必然 422——空值视为选择未完成，不发上下文预取。
  const validSelection = Boolean(selection.context_id && selection.product && selection.factory && selection.month
    && (selection.benchmark_right === undefined || Boolean(selection.benchmark_right)));

  const loadModel = useCallback(() => Promise.all([api('/settings/models'), api('/settings/models/presets')]).then(([value, presets]) => {
    if (!alive.current) return;
    const connection = value.connections?.assistant ?? {};
    setModel(connection);
    setSelectedModel(current => current || connection.effective?.model || connection.model || '');
    setEffort(current => current || connection.effective?.reasoning_effort || connection.reasoning_effort || '');
    setModelOptions([...new Set<string>([connection.effective?.model, connection.model, ...[...(presets.api_vendors ?? []), ...(presets.local_vendors ?? [])].filter((vendor: any) => vendor.id === connection.vendor || vendor.base_url === connection.base_url).flatMap((vendor: any) => (vendor.models ?? []).map((item: any) => item.id))].filter(Boolean))]);
  }).catch(() => { if (alive.current) setModel(null); }), []);

  const loadOpenChats = useCallback(async () => {
    const request = ++listSequence.current;
    const rows = chatRows(await api('/assistant/conversations?state=open'));
    if (alive.current && request === listSequence.current) setOpenChats(previous => {
      // Selecting a chat must not reorder the tabs under the pointer or arrow-key focus.
      const positions = new Map(previous.map((chat, index) => [chat.id, index]));
      const incoming = new Map(rows.map((chat, index) => [chat.id, previous.length + index]));
      return [...rows].sort((left, right) => Number(Boolean(right.pinned)) - Number(Boolean(left.pinned))
        || (positions.get(left.id) ?? incoming.get(left.id) ?? 0) - (positions.get(right.id) ?? incoming.get(right.id) ?? 0));
    });
    return rows;
  }, []);

  const loadConversation = useCallback(async (id: string, view = viewSequence.current) => {
    if (activeConversation.current !== id || viewSequence.current !== view) return null;
    const request = ++readSequence.current;
    const result = await api<Conversation>('/assistant/conversations/' + encodeURIComponent(id));
    if (alive.current && activeConversation.current === id && viewSequence.current === view && readSequence.current === request) {
      setConversation(result);
      setOpenChats(rows => rows.map(item => item.id === id ? { ...item, ...result, messages: undefined } : item));
      setTurn((current: any) => result.active_turn_id ? current?.id === result.active_turn_id ? current : { id: result.active_turn_id, status: 'queued' } : running(current) ? null : current);
      setLoadingChat(false);
    }
    return result;
  }, []);

  const changeDraft = (value: string) => {
    draftValue.current = value;
    if (activeConversation.current) drafts.current.set(activeConversation.current, value);
    setDraft(value);
  };

  const activate = useCallback(async (id: string, markOpen = false) => {
    const view = ++viewSequence.current;
    if (activeConversation.current) drafts.current.set(activeConversation.current, draftValue.current);
    activeConversation.current = id;
    setActiveId(id); setConversation(null); setTurn(null); setUsage(null); setError(''); setRetryText(''); setJumpedMessage('');
    const nextDraft = drafts.current.get(id) ?? '';
    draftValue.current = nextDraft; setDraft(nextDraft);
    followLatest.current = true; setAtLatest(true); setLoadingChat(Boolean(id));
    if (!id) { sessionStorage.removeItem('pharma-assistant-conversation'); return; }
    sessionStorage.setItem('pharma-assistant-conversation', id);
    const preference = preferences.current.get(id);
    if (preference) { setSelectedModel(preference.model); setEffort(preference.effort); }
    try {
      if (markOpen) await api('/assistant/conversations/' + encodeURIComponent(id), { action: 'open' }, undefined, 'PATCH');
      await loadConversation(id, view);
      if (markOpen) await loadOpenChats();
    } catch (e: any) {
      if (alive.current && view === viewSequence.current) { setLoadingChat(false); setError(e.message); }
    }
  }, [loadConversation, loadOpenChats]);

  useEffect(() => {
    alive.current = true;
    const savedId = sessionStorage.getItem('pharma-assistant-conversation');
    sessionStorage.removeItem('pharma-assistant-turn'); // Running requests are restored from the server, scoped to their chat.
    void loadModel();
    void loadOpenChats().then(rows => {
      if (!alive.current) return;
      const next = rows.find(item => item.id === savedId) ?? rows[0];
      void activate(next?.id ?? '');
    }).catch(e => { if (alive.current) { setError(e.message); setLoadingChat(false); } });
    const reload = () => { preferences.current.clear(); setSelectedModel(''); setEffort(''); setModelsRead(false); void loadModel(); };
    window.addEventListener('pharma:model-saved', reload);
    return () => { alive.current = false; ++viewSequence.current; window.removeEventListener('pharma:model-saved', reload); };
  }, [activate, loadModel, loadOpenChats]);

  useEffect(() => {
    if (activeId) preferences.current.set(activeId, { model: selectedModel, effort });
  }, [activeId, selectedModel, effort]);

  useEffect(() => {
    setUsage(null);
    if (!validSelection || loadingChat) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      api('/assistant/context', { conversation_id: conversation?.id, selection, text: draft, overrides: { ...(selectedModel.trim() ? { model: selectedModel.trim() } : {}), reasoning_effort: effort } }, controller.signal).then(value => {
        if (!controller.signal.aborted) setUsage(value);
      }).catch(() => { if (!controller.signal.aborted) setUsage(null); });
    }, 450);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [conversation?.id, conversation?.messages?.length, selection, draft, selectedModel, effort, model, validSelection, loadingChat]);

  const readModels = async (open: boolean) => {
    if (!open || !model?.configured || modelsRead) return;
    setModelsRead(true);
    try {
      const value = await api('/settings/models/list?route=assistant', { model: selectedModel });
      if (alive.current && value.models?.length) setModelOptions([...new Set<string>([selectedModel, ...value.models.map((item: any) => typeof item === 'string' ? item : item.id)].filter(Boolean))]);
    } catch { /* Provider presets stay usable when discovery is unavailable. */ }
  };

  useEffect(() => {
    if (!turn?.id || !running(turn) || !activeId) return;
    const controller = new AbortController(), chatId = activeId, view = viewSequence.current;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const result = await api('/assistant/turns/' + encodeURIComponent(turn.id), undefined, controller.signal);
        if (controller.signal.aborted || activeConversation.current !== chatId || viewSequence.current !== view) return;
        setTurn({ ...result, id: result.turn_id ?? result.id });
        if (!running(result)) {
          if (String(result.status).toLowerCase() === 'failed') setError(result.error ?? '本次请求未完成，请重试。');
          await loadConversation(chatId, view);
          await loadOpenChats();
        } else timer = setTimeout(poll, 1200);
      } catch (e: any) {
        if (!controller.signal.aborted && activeConversation.current === chatId && viewSequence.current === view) {
          setError('进度读取失败：' + e.message);
          timer = setTimeout(poll, 3000);
        }
      }
    };
    void poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [turn?.id, activeId, loadConversation, loadOpenChats]);

  useEffect(() => {
    if (!conversation) return;
    const switched = previousRendered.current !== conversation.id;
    previousRendered.current = conversation.id;
    if (switched || followLatest.current) {
      const frame = requestAnimationFrame(() => { scroll.current?.scrollTo({ top: scroll.current.scrollHeight, behavior: 'auto' }); });
      return () => cancelAnimationFrame(frame);
    }
  }, [conversation?.id, conversation?.messages?.length]);

  const createConversation = async (): Promise<Conversation | null> => {
    if (createPending.current) return null;
    createPending.current = true; setCreating(true); setError('');
    try {
      const created = await api<Conversation>('/assistant/conversations', validSelection ? { selection } : {});
      if (!alive.current) return created;
      await loadOpenChats();
      await activate(created.id);
      return created;
    } catch (e: any) { if (alive.current) setError(e.message); return null; }
    finally { createPending.current = false; if (alive.current) setCreating(false); }
  };

  const send = async (text = draft) => {
    if (!text.trim() || busy || !validSelection || loadingChat || createPending.current) return;
    const initialId = activeConversation.current || '__new__';
    if (sendPending.current.has(initialId)) return;
    sendPending.current.add(initialId);
    let id = activeConversation.current;
    setError(''); setRetryText(text);
    try {
      if (!id) {
        const created = await createConversation();
        if (!created) return;
        id = created.id;
      }
      sendPending.current.add(id);
      if (alive.current) setPendingSends(current => new Set(current).add(id));
      if (activeConversation.current === id) { changeDraft(''); followLatest.current = true; setAtLatest(true); }
      const overrides = { ...(selectedModel.trim() ? { model: selectedModel.trim() } : {}), reasoning_effort: effort };
      const fingerprint = JSON.stringify({ text: text.trim(), selection, overrides });
      const previousAttempt = sendAttempts.current.get(id);
      const requestId = previousAttempt?.fingerprint === fingerprint ? previousAttempt.requestId : crypto.randomUUID();
      sendAttempts.current.set(id, { fingerprint, requestId });
      const result = await api('/assistant/conversations/' + encodeURIComponent(id) + '/messages', { text: text.trim(), selection, client_request_id: requestId, overrides });
      sendAttempts.current.delete(id);
      if (alive.current && activeConversation.current === id) setTurn({ ...result, id: result.turn_id ?? result.id });
      await loadConversation(id);
      await loadOpenChats();
    } catch (e: any) {
      if (alive.current && activeConversation.current === id) { setError(e.message); setRetryText(text); }
    } finally {
      sendPending.current.delete(initialId); sendPending.current.delete(id);
      if (alive.current) setPendingSends(current => { const next = new Set(current); next.delete(id); return next; });
    }
  };

  const cancel = async () => {
    const id = activeConversation.current, turnId = turn?.id;
    if (!turnId) return;
    try {
      const value = await api('/assistant/turns/' + encodeURIComponent(turnId) + '/cancel', {});
      if (alive.current && activeConversation.current === id) setTurn(value);
      await loadConversation(id);
    } catch (e: any) { if (activeConversation.current === id) setError(e.message); }
  };

  const loadHistory = useCallback(async (mode: HistoryMode) => {
    const request = ++historySequence.current;
    setHistoryLoading(true); setHistoryError('');
    try {
      const rows = chatRows(await api('/assistant/conversations?state=' + mode));
      if (alive.current && historySequence.current === request) setHistory(rows);
    } catch (e: any) { if (alive.current && historySequence.current === request) setHistoryError(e.message); }
    finally { if (alive.current && historySequence.current === request) setHistoryLoading(false); }
  }, []);
  useEffect(() => {
    setHistorySearch('');
    if (historyMode) { setHistory([]); void loadHistory(historyMode); }
    else ++historySequence.current;
  }, [historyMode, loadHistory]);

  const changeChat = async (chat: ChatSummary, action: 'close' | 'pin' | 'unpin' | 'archive') => {
    if (mutationPending.current) return;
    mutationPending.current = true; setMutation(chat.id); setError(''); setHistoryError('');
    try {
      await api('/assistant/conversations/' + encodeURIComponent(chat.id), { action }, undefined, 'PATCH');
      const rows = await loadOpenChats();
      if (['close', 'archive'].includes(action) && activeConversation.current === chat.id) await activate(rows.find(item => item.id !== chat.id)?.id ?? '');
      if (historyMode) await loadHistory(historyMode);
    } catch (e: any) { setError(e.message); if (historyMode) setHistoryError(e.message); }
    finally { mutationPending.current = false; if (alive.current) setMutation(''); }
  };

  const reopen = async (chat: ChatSummary) => {
    if (mutationPending.current) return;
    mutationPending.current = true; setMutation(chat.id); setHistoryError('');
    try {
      if (chat.archived) await api('/assistant/conversations/' + encodeURIComponent(chat.id), { action: 'unarchive' }, undefined, 'PATCH');
      await api('/assistant/conversations/' + encodeURIComponent(chat.id), { action: 'open' }, undefined, 'PATCH');
      await loadOpenChats();
      await activate(chat.id);
      setHistoryMode(null);
    } catch (e: any) { setHistoryError(e.message); }
    finally { mutationPending.current = false; if (alive.current) setMutation(''); }
  };

  const deleteConversation = async () => {
    if (!pendingDelete || mutationPending.current) return;
    const chat = pendingDelete;
    mutationPending.current = true; setMutation(chat.id); setDeleteError('');
    try {
      await api('/assistant/conversations/' + encodeURIComponent(chat.id), undefined, undefined, 'DELETE');
      drafts.current.delete(chat.id); preferences.current.delete(chat.id); sendAttempts.current.delete(chat.id);
      const rows = await loadOpenChats();
      if (activeConversation.current === chat.id) await activate(rows[0]?.id ?? '');
      if (historyMode) await loadHistory(historyMode);
      setPendingDelete(null);
    } catch (e: any) { setDeleteError(e.message); }
    finally { mutationPending.current = false; if (alive.current) setMutation(''); }
  };

  const confirm = async (proposal: any) => {
    const id = activeConversation.current;
    setConfirming(proposal.id); setError('');
    try {
      const result = await api('/assistant/proposals/' + encodeURIComponent(proposal.id) + '/confirm', {});
      await loadConversation(id);
      onApplied(result);
    } catch (e: any) { if (activeConversation.current === id) setError(e.message); }
    finally { if (alive.current) setConfirming(''); }
  };

  const jumpToMessage = (id: string) => {
    const container = scroll.current, element = document.getElementById('assistant-message-' + id);
    if (!container || !element) return;
    followLatest.current = false; setAtLatest(false); setJumpedMessage(id);
    container.scrollTo({ top: container.scrollTop + element.getBoundingClientRect().top - container.getBoundingClientRect().top - 44, behavior: 'smooth' });
    element.focus({ preventScroll: true });
  };

  const visibleChats = openChats.slice(0, 3);
  const currentChat = openChats.find(item => item.id === activeId);
  if (currentChat && !visibleChats.some(item => item.id === activeId)) visibleChats[2] = currentChat;
  const userTurns = conversation?.messages?.filter(message => message.role === 'user') ?? [];
  const matchingHistory = history.filter(item => chatTitle(item).toLocaleLowerCase().includes(historySearch.trim().toLocaleLowerCase()));
  const previousSelection = conversation?.selection ?? conversation?.context?.selection ?? conversation?.context;
  const scopeChanged = previousSelection?.context_id && ['context_id', 'factory', 'product', 'month', 'analysis_type', 'basis', 'benchmark_right'].some(key => String(previousSelection[key] ?? '') !== String((selection as any)[key] ?? ''));
  return <section className="assistant-panel" aria-label="智能对话">
    <header className="assistant-tabs-header">
      <div className="assistant-open-tabs" role="tablist" aria-label="已打开的对话">
        {visibleChats.map(chat => <div key={chat.id} className={'assistant-chat-tab' + (chat.id === activeId ? ' is-active' : '')}>
          <button className="assistant-chat-select" id={'assistant-tab-' + chat.id} role="tab" aria-selected={chat.id === activeId} aria-controls="assistant-active-chat" aria-label={chatTitle(chat)} title={chatTitle(chat)} disabled={creating} tabIndex={chat.id === activeId ? 0 : -1} onClick={() => { if (chat.id !== activeId) void activate(chat.id, true); }} onKeyDown={event => {
            const index = visibleChats.findIndex(item => item.id === chat.id);
            const next = event.key === 'ArrowRight' ? visibleChats[(index + 1) % visibleChats.length] : event.key === 'ArrowLeft' ? visibleChats[(index - 1 + visibleChats.length) % visibleChats.length] : event.key === 'Home' ? visibleChats[0] : event.key === 'End' ? visibleChats[visibleChats.length - 1] : null;
            if (next) { event.preventDefault(); document.getElementById('assistant-tab-' + next.id)?.focus(); void activate(next.id, true); }
          }}>{chat.pinned && <PushpinFilled className="assistant-chat-pinned" />}<span>{chatTitle(chat)}</span></button>
          <span className="assistant-chat-actions">
            <button type="button" title={(chat.pinned ? '取消固定：' : '固定对话：') + chatTitle(chat)} aria-label={(chat.pinned ? '取消固定：' : '固定对话：') + chatTitle(chat)} aria-pressed={Boolean(chat.pinned)} disabled={Boolean(mutation)} onClick={() => void changeChat(chat, chat.pinned ? 'unpin' : 'pin')}>{chat.pinned ? <PushpinFilled /> : <PushpinOutlined />}</button>
            <button type="button" title={'关闭对话：' + chatTitle(chat) + '（保留在历史记录）'} aria-label={'关闭对话：' + chatTitle(chat)} disabled={Boolean(mutation)} onClick={() => void changeChat(chat, 'close')}><CloseOutlined /></button>
          </span>
        </div>)}
      </div>
      <div className="assistant-tab-tools">
        {openChats.length > 3 && <Dropdown trigger={['click']} placement="bottomRight" autoFocus classNames={{ root: 'assistant-open-menu' }} menu={{ selectedKeys: [activeId], items: openChats.map(chat => ({ key: chat.id, icon: chat.pinned ? <PushpinFilled /> : undefined, label: <span title={chatTitle(chat)}>{chatTitle(chat)}</span> })), onClick: ({ key }) => { if (key !== activeId) void activate(key, true); } }}>
          <Button type="text" icon={<DownOutlined />} aria-label={'选择已打开的对话，共 ' + openChats.length + ' 个'} title="所有已打开的对话" />
        </Dropdown>}
        <Tooltip title="新建对话"><Button type="text" icon={<PlusOutlined />} aria-label="新建对话" loading={creating} disabled={Boolean(mutation) || loadingChat} onClick={() => void createConversation()} /></Tooltip>
        <Dropdown trigger={['click']} placement="bottomRight" autoFocus classNames={{ root: 'assistant-actions-menu' }} menu={{ items: [
          { key: 'history', icon: <HistoryOutlined />, label: '历史记录' },
          { key: 'archive', icon: <InboxOutlined />, label: '归档', children: [
            { key: 'archive-current', label: '归档当前对话', disabled: !conversation || Boolean(mutation) },
            { key: 'archived', label: '查看已归档' },
          ] },
          { type: 'divider' },
          { key: 'delete', icon: <DeleteOutlined />, label: '删除当前对话', danger: true, disabled: !conversation || Boolean(mutation) },
        ], onClick: ({ key }) => {
          if (key === 'history') setHistoryMode('history');
          else if (key === 'archived') setHistoryMode('archived');
          else if (key === 'archive-current' && conversation) void changeChat(conversation, 'archive');
          else if (key === 'delete' && conversation) { setDeleteError(''); setPendingDelete(conversation); }
        } }}><Button type="text" icon={<EllipsisOutlined />} aria-label="对话菜单" title="对话菜单" /></Dropdown>
      </div>
    </header>
    <div className="assistant-chat-body" id="assistant-active-chat" role="tabpanel" aria-labelledby={activeId ? 'assistant-tab-' + activeId : undefined} aria-label={!activeId ? '新对话' : undefined} aria-busy={loadingChat}>
      <div className="assistant-scroll" ref={scroll} onScroll={() => {
        const element = scroll.current;
        if (element) { const nearBottom = element.scrollHeight - element.clientHeight - element.scrollTop < 56; followLatest.current = nearBottom; setAtLatest(nearBottom); }
      }}>
      {!!userTurns.length && <div className="assistant-turn-navigation"><Dropdown trigger={['click']} placement="bottomRight" autoFocus classNames={{ root: 'assistant-turn-menu' }} menu={{ items: userTurns.map((message, index) => ({ key: message.id, label: <span title={message.content}>{index + 1}. {message.content.replace(/\s+/g, ' ')}</span> })), selectedKeys: jumpedMessage ? [jumpedMessage] : [], onClick: ({ key }) => jumpToMessage(key) }}>
        <button type="button" aria-label={'跳转到对话，共 ' + userTurns.length + ' 轮'}>对话导航 <span>{userTurns.length}</span><DownOutlined /></button>
      </Dropdown></div>}
      {loadingChat && <div className="assistant-chat-loading" role="status"><Spin size="small" /><span>正在读取对话…</span></div>}
      {scopeChanged && <Alert type="info" showIcon title="当前分析条件已变化" description="历史消息保留当时的数据和口径；新问题将使用当前分析条件。" />}
      {!loadingChat && !conversation?.messages?.length && <div className="assistant-empty"><RobotOutlined /><h3>想了解哪一项成本变化？</h3><p>查看当前数据、核对证据，或准备下一步行动。</p><div className="assistant-starters">{[{label:'解释变化',text:'解释当前成本变化',icon:<BarChartOutlined/>},{label:'核查数据',text:'检查数据和证据缺口',icon:<FileSearchOutlined/>},{label:'准备报告',text:'准备当前分析的报告',icon:<FileTextOutlined/>}].map(item => <Button key={item.text} icon={item.icon} disabled={!validSelection || busy || creating || loadingChat} onClick={() => send(item.text)}>{item.label}</Button>)}</div></div>}
      {conversation?.messages?.map(message => <article key={message.id} id={'assistant-message-' + message.id} data-jump-target={jumpedMessage === message.id} tabIndex={-1} className={`assistant-message ${message.role === 'user' ? 'from-user' : 'from-assistant'}`}>
        <div className="assistant-message-label">{message.role === 'user' ? '你' : '回答'}{message.mode&&<span>{message.mode==='model'?`模型解释${message.model?` · ${message.model}`:''}`:'规则分析'}</span>}{message.status && <Tag>{labelStage(message.status)}</Tag>}</div>
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
      {error && <Alert type="error" showIcon title={error} action={!busy && retryText && !loadingChat ? <Button size="small" onClick={() => send(retryText)}>重试</Button> : undefined} />}
      </div>
      {!atLatest && !!conversation?.messages?.length && <button type="button" className="assistant-jump-latest" onClick={() => { followLatest.current = true; setAtLatest(true); setJumpedMessage(''); scroll.current?.scrollTo({ top: scroll.current.scrollHeight, behavior: 'smooth' }); }}>回到最新 <DownOutlined /></button>}
    </div>
    <div className="assistant-composer"><div className="assistant-context"><span title={validSelection ? scope(selection) : undefined}>{validSelection ? scope(selection) : '导入并解析业务数据后即可开始分析'}</span></div>
      <div className="assistant-input-box"><Input.TextArea aria-label="向 AI 助手提问" title="Enter 发送；Shift + Enter 换行" variant="borderless" placeholder="询问当前数据，或提出下一步操作…" autoSize={{ minRows: 3, maxRows: 8 }} value={draft} maxLength={6000} onChange={e => changeDraft(e.target.value)} disabled={loadingChat || creating} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }} />
      <div className="assistant-input-toolbar">
      <Tooltip trigger={['hover','focus']} title={usage?.context_window ? <div>本轮输入估算：{usage.estimated_input_tokens??usage.used_tokens??'—'} tokens（圆环弧长仅表示输入占用）<br/>配置容量：{usage.context_window} tokens<br/>预留输出：{usage.max_output_tokens??'—'} tokens<br/>剩余：{usage.available_tokens??'—'} tokens（颜色按扣除输出预留后的余量变化）<br/>{usage.estimate_note??'输入量为估算，实际消耗以服务商返回为准。'}{usage.last_usage?.total_tokens?<><br/>上次服务端用量：{usage.last_usage.total_tokens} tokens（不是本轮估算）</>:null}</div> : '当前型号未配置上下文窗口，容量与剩余量未知。可在模型连接中按服务商说明填写。'}>
       <button type="button" className="assistant-context-indicator" aria-label={usage?.context_window ? `上下文：估算输入 ${usage.estimated_input_tokens??usage.used_tokens??'未知'} tokens，容量 ${usage.context_window}，预留输出 ${usage.max_output_tokens??'未知'}，剩余 ${usage.available_tokens??'未知'}` : '上下文窗口未知；聚焦查看说明'}>
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="6.5" fill="none" stroke="#dfe5e8" strokeWidth="2.3"/><circle cx="9" cy="9" r="6.5" fill="none" stroke={remainingColor(usage?.context_window&&usage.available_tokens!=null?Number(usage.available_tokens)/Number(usage.context_window):null)} strokeWidth="2.3" strokeLinecap="round" strokeDasharray={`${usage?.context_window&&usage.estimated_input_tokens!=null?Math.max(0,Math.min(1,Number(usage.estimated_input_tokens)/Number(usage.context_window)))*40.84:0} 40.84`} transform="rotate(-90 9 9)"/></svg>
       </button>
      </Tooltip>
      <Dropdown trigger={['click']} disabled={busy} onOpenChange={open=>void readModels(open)} menu={{items:[{type:'group',label:'本次对话的模型',children:(modelOptions.length?modelOptions:selectedModel?[selectedModel]:[]).map(value=>({key:`model:${value}`,label:value,icon:value===selectedModel?<CheckOutlined/>:undefined}))},{type:'divider'},{key:'efforts',label:'推理强度',children:Object.entries(effortLabels).map(([value,label])=>({key:`effort:${value}`,label,icon:value===effort?<CheckOutlined/>:undefined}))},{type:'divider'},{key:'configure',label:'添加型号或配置模型连接'}],onClick:({key})=>{if(key.startsWith('model:'))setSelectedModel(key.slice(6));else if(key.startsWith('effort:'))setEffort(key.slice(7));else if(key==='configure')onConfigure()}}}>
       <Button type="text" className="assistant-inline-model" aria-label={`选择助手模型与推理强度，当前 ${selectedModel||'未选择模型'}，${effortLabels[effort]??effort}`}><span className="assistant-model-name">{selectedModel?selectedModel.replace(/^glm/i,'GLM'):'选择模型'}</span><span className="assistant-effort-name">{effortLabels[effort]??effort}</span><DownOutlined/></Button>
      </Dropdown>
      {busy ? <Tooltip title="停止等待，不发布迟到回答；已发给服务商的请求可能仍计费用。"><Button type="text" aria-label="停止生成" icon={<StopOutlined/>} onClick={cancel}/></Tooltip> : <Button type="primary" aria-label="发送消息" icon={<SendOutlined/>} disabled={!draft.trim()||!validSelection||usage?.limit_exceeded||loadingChat||creating} onClick={()=>send()}/>}</div></div>

    </div>
    <Modal open={historyMode !== null} title="对话记录" footer={null} onCancel={() => setHistoryMode(null)} width={580} className="assistant-history-modal" destroyOnHidden>
      <div className="assistant-history-controls"><Segmented aria-label="记录分类" value={historyMode ?? 'history'} options={[{ value: 'history', label: '历史记录' }, { value: 'archived', label: '已归档' }]} onChange={value => setHistoryMode(value as HistoryMode)} /><Input.Search placeholder="搜索对话标题" aria-label="搜索对话标题" value={historySearch} onChange={event => setHistorySearch(event.target.value)} allowClear /></div>
      {historyError && <Alert type="error" showIcon title={historyError} />}
      <div className="assistant-history-list" aria-busy={historyLoading}>
        {historyLoading ? <div className="assistant-record-empty"><Spin size="small" /> 正在读取记录…</div> : !matchingHistory.length ? <p className="assistant-record-empty">{historySearch ? '没有匹配的对话' : historyMode === 'archived' ? '暂无已归档的对话' : '暂无历史对话'}</p> : matchingHistory.map(chat => <div className="assistant-history-row" key={chat.id}>
          <button type="button" className="assistant-history-open" disabled={Boolean(mutation)} onClick={() => void reopen(chat)} aria-label={(chat.archived ? '恢复并打开：' : '打开历史对话：') + chatTitle(chat)}><span>{chat.pinned && <PushpinFilled />}{chatTitle(chat)}</span><small>{chatDate(chat)}{chat.is_open ? ' · 已打开' : ''}{chat.archived ? ' · 点击恢复并打开' : ''}</small></button>
          <div className="assistant-history-actions">
            {!chat.archived && <Tooltip title="归档"><Button type="text" size="small" icon={<InboxOutlined />} aria-label={'归档对话：' + chatTitle(chat)} disabled={Boolean(mutation)} onClick={() => void changeChat(chat, 'archive')} /></Tooltip>}
            <Tooltip title="删除"><Button type="text" size="small" icon={<DeleteOutlined />} aria-label={'删除对话：' + chatTitle(chat)} disabled={Boolean(mutation)} onClick={() => { setDeleteError(''); setPendingDelete(chat); }} /></Tooltip>
          </div>
        </div>)}
      </div>
    </Modal>
    <Modal open={Boolean(pendingDelete)} title="删除此对话？" okText="删除对话" cancelText="保留" okButtonProps={{ danger: true }} confirmLoading={Boolean(mutation)} onOk={() => void deleteConversation()} onCancel={() => { if (!mutation) setPendingDelete(null); }}>
      <p className="assistant-delete-title">{pendingDelete ? chatTitle(pendingDelete) : ''}</p>
      <p>删除后无法从历史记录中恢复。正在生成的回答会停止接收，已生成的报告和整改任务仍保留。</p>
      {deleteError && <Alert type="error" showIcon title={deleteError} />}
    </Modal>
  </section>;
}
