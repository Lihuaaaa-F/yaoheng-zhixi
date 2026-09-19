"""Agent 自主决策引擎（赛题加分项）：自动判断“需要生成报告”还是“仅更新看板”。

设计原则：
- 决策本体是确定性策略（策略版本化），任何模型输出都不能翻转决策结果，
  大模型只负责把决策依据转写成一段自然语言说明（走独立的小模型路由）；
- 每次决策写入 SQLite 台账，含信号、依据、模型说明与后续执行的任务号，
  保证“自主决策”可审计、可回放；
- 判定输入只来自已固化的分析快照与任务队列状态，不猜测外部事实。
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .config import RUNTIME

# 策略版本：判定规则变化时递增，回执据此区分新旧口径。
DECISION_POLICY_VERSION = 'report-vs-dashboard-v1'
ADVISORY_PROMPT_VERSION = 'decision-advisory-v2-signal-selection'


def _matching_report_jobs(jobs, selection):
    """从任务列表中筛出与当前选择完全同口径的报告任务。

    口径 = 企业上下文 + 工厂 + 产品 + 期间 + 分析类型 + 成本口径；
    任务创建时把这些字段冻结在 input 里，之后数据变化不影响旧任务。
    """
    wanted = (selection.get('context_id'), selection.get('factory'), selection.get('product'),
              selection.get('month'), selection.get('analysis_type'), selection.get('basis'))
    matched = []
    for job in jobs:
        payload = job.get('input') or {}
        actual = (payload.get('context_id'), payload.get('factory'), payload.get('product'),
                  payload.get('month'), payload.get('analysis_type'), payload.get('basis'))
        if job.get('kind') == 'report' and actual == wanted:
            matched.append(job)
    return matched


def evaluate(snapshot, jobs):
    """对当前快照执行确定性决策：REPORT_NEEDED 或 DASHBOARD_ONLY。

    策略（按优先级）：
    1. 本口径本期间尚无终态报告 → REPORT_NEEDED（新周期的正式交付物缺失）；
    2. 最新报告绑定的快照与当前快照不同 → REPORT_NEEDED（底层数据已变化，
       报告必须基于当前版本重出，旧报告自动进入待复核状态）；
    3. 报告存在且绑定同一快照 → DASHBOARD_ONLY（正式报告仍是当前版本，
       看板随实时分析更新即可，不重复消耗渲染与审核资源）。
    """
    from .narrative import required_alerts
    selection = {k: snapshot.get(k) for k in ('context_id', 'factory', 'product', 'month', 'analysis_type', 'basis')}
    alerts = required_alerts(snapshot)
    reports = [j for j in _matching_report_jobs(jobs, selection) if j.get('status') in ('SUCCEEDED', 'DEGRADED')]
    signals = []
    signals.append({'id': 'active_alerts', 'label': '超阈值告警数', 'value': len(alerts),
                    'detail': '；'.join(a['fact_summary'] for a in alerts[:3]) or '无告警'})
    if not reports:
        decision = 'REPORT_NEEDED'
        reason = '当前口径与期间还没有正式报告'
        signals.append({'id': 'report_for_period', 'label': '本期间报告', 'value': '缺失', 'detail': reason})
    else:
        latest = max(reports, key=lambda j: j.get('created') or '')
        bound = (latest.get('input') or {}).get('snapshot_id')
        current = snapshot.get('snapshot_id')
        if bound != current:
            decision = 'REPORT_NEEDED'
            reason = '底层数据版本已变化，正式报告需要基于当前快照重新生成'
            signals.append({'id': 'snapshot_binding', 'label': '报告绑定快照', 'value': '过期',
                            'detail': f'报告绑定 {str(bound)[:12]}，当前快照 {str(current)[:12]}'})
        else:
            decision = 'DASHBOARD_ONLY'
            reason = '正式报告已覆盖当前数据版本，看板更新即可'
            signals.append({'id': 'snapshot_binding', 'label': '报告绑定快照', 'value': '一致',
                            'detail': f'报告 {latest["id"][:8]} 与当前快照一致'})
    return {'decision': decision, 'reason': reason, 'policy_version': DECISION_POLICY_VERSION,
            'engine': 'deterministic', 'signals': signals, 'selection': selection,
            'alert_count': len(alerts), 'evaluated_at': time.time()}


def _rationale(evaluation, signal_ids):
    # All wording is derived from verified rule signals; no free model prose is accepted.
    parts = [evaluation['reason'].rstrip('。')]
    if 'active_alerts' in signal_ids:
        parts.append('存在成本要素超阈值变化，需要结合证据核查' if evaluation['alert_count']
                     else '当前没有成本要素超阈值变化')
    parts.append('建议生成报告' if evaluation['decision'] == 'REPORT_NEEDED' else '仅更新看板即可')
    return '；'.join(parts) + '。'


def advise(evaluation, snapshot, gateway_factory=None):
    """模型只选择已验证信号；程序生成与确定性动作一致的说明。"""
    route = (gateway_factory or _default_gateway_factory)('decision')
    result = {**evaluation, 'advisory_model': route.model,
              'advisory_prompt_version': ADVISORY_PROMPT_VERSION,
              'advisory_identity': {'requested_model': route.model, 'returned_model': None,
                                    'identity_status': 'NOT_CHECKED'},
              'rationale': _rationale(evaluation, [])}
    if not getattr(route, 'key', ''):
        return {**result, 'advisory_status': 'NO_KEY'}
    system = ('你是成本分析系统的决策依据选择员。只返回JSON对象 '
              '{"decision": "输入的决策", "signal_ids": ["输入信号ID"]}。'
              '不能改变决策，只从输入选择相关信号，必须包含报告缺失或快照绑定信号。'
              '不输出自由说明文字，程序将依据所选信号生成说明。')
    user = json.dumps({'decision': evaluation['decision'], 'reason': evaluation['reason'],
                       'signals': evaluation['signals']}, ensure_ascii=False)
    try:
        raw, _usage, identity = route.complete(system, user, operation='decision', prompt_version=ADVISORY_PROMPT_VERSION)
        result['advisory_identity'] = identity or result['advisory_identity']
        from .narrative import classify_identity
        verified = classify_identity(route.model, result['advisory_identity'].get('returned_model'))[0]
        if (result['advisory_identity'].get('identity_status') not in ('VERIFIED_EXACT', 'VERIFIED_ALIAS')
                or verified not in ('VERIFIED_EXACT', 'VERIFIED_ALIAS')
                or result['advisory_identity'].get('requested_model') != route.model):
            raise ValueError('ADVISORY_IDENTITY_UNVERIFIED')
        parsed = json.loads(raw)
        if (not isinstance(parsed, dict) or set(parsed) != {'decision', 'signal_ids'}
                or parsed['decision'] != evaluation['decision']):
            raise ValueError('INVALID_ADVISORY_SHAPE_OR_DECISION')
        selected = parsed['signal_ids']
        allowed = {s['id'] for s in evaluation['signals']}
        if (not isinstance(selected, list) or not selected
                or any(not isinstance(item, str) or item not in allowed for item in selected)
                or len(selected) != len(set(selected))
                or not (set(selected) & {'report_for_period', 'snapshot_binding'})):
            raise ValueError('INVALID_ADVISORY_SIGNALS')
        return {**result, 'advisory_status': 'PASS', 'advisory_signal_ids': selected,
                'rationale': _rationale(evaluation, selected)}
    except Exception as exc:
        return {**result, 'advisory_status': 'DEGRADED',
                'advisory_error': str(exc) if isinstance(exc, ValueError) and str(exc).startswith(('ADVISORY_', 'INVALID_ADVISORY')) else type(exc).__name__}


def _default_gateway_factory(route):
    from .narrative import ModelGateway
    return ModelGateway.for_route(route)


class DecisionStore:
    """决策台账：追加式记录每次决策及其后续执行，供审计与回放。"""

    def __init__(self, path=None):
        self.path = Path(path) if path else RUNTIME / 'decision.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as c:
            c.execute('CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, created_at REAL,'
                      'context_id TEXT, selection TEXT, decision TEXT, signals TEXT, rationale TEXT,'
                      'advisory_status TEXT, advisory_model TEXT, applied_job_id TEXT)')
            if 'advisory_evidence' not in {r[1] for r in c.execute('PRAGMA table_info(decisions)')}:
                c.execute('ALTER TABLE decisions ADD COLUMN advisory_evidence TEXT')

    @contextmanager
    def _db(self):
        # 显式关闭连接：Windows 下滞留句柄会持有 SQLite 写锁
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get(self, decision_id):
        with self._db() as c:
            row = c.execute('SELECT * FROM decisions WHERE id=?', (decision_id,)).fetchone()
            return dict(row) if row else None

    def append(self, evaluation):
        with self._db() as c:
            cursor = c.execute('INSERT INTO decisions(created_at,context_id,selection,decision,signals,rationale,'
                               'advisory_status,advisory_model,applied_job_id) VALUES(?,?,?,?,?,?,?,?,NULL)',
                               (evaluation['evaluated_at'], evaluation['selection'].get('context_id'),
                                json.dumps(evaluation['selection'], ensure_ascii=False), evaluation['decision'],
                                json.dumps(evaluation['signals'], ensure_ascii=False), evaluation.get('rationale'),
                                evaluation.get('advisory_status'), evaluation.get('advisory_model')))
            c.execute('UPDATE decisions SET advisory_evidence=? WHERE id=?',
                      (json.dumps({k: v for k, v in evaluation.items() if k.startswith('advisory_')}, ensure_ascii=False), cursor.lastrowid))
            return cursor.lastrowid

    def bind_job(self, decision_id, job_id):
        with self._db() as c:
            c.execute('UPDATE decisions SET applied_job_id=? WHERE id=?', (job_id, decision_id))

    def list(self, context_id=None, limit=50):
        sql = 'SELECT * FROM decisions'
        params = []
        if context_id:
            sql += ' WHERE context_id=?'
            params.append(context_id)
        sql += ' ORDER BY id DESC LIMIT ?'
        params.append(limit)
        with self._db() as c:
            return [dict(r) for r in c.execute(sql, params)]
