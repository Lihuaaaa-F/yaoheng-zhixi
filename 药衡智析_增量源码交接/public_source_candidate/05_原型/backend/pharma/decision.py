"""Agent 自主决策引擎（赛题加分项）：自动判断“需要生成报告”还是“仅更新看板”。

设计原则：
- 决策本体是确定性策略（策略版本化），任何模型输出都不能翻转决策结果，
  大模型只负责把决策依据转写成一段自然语言说明（走独立的小模型路由）；
- 每次决策写入 SQLite 台账，含信号、依据、模型说明与后续执行的任务号，
  保证“自主决策”可审计、可回放；
- 判定输入只来自已固化的分析快照与任务队列状态，不猜测外部事实。
"""
import json
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .config import RUNTIME

# 策略版本：判定规则变化时递增，回执据此区分新旧口径。
DECISION_POLICY_VERSION = 'report-vs-dashboard-v1'
ADVISORY_PROMPT_VERSION = 'decision-advisory-v1'
# 决策说明同样禁止自由数字：与 narrative 校验器同口径（数字/中文数词）。
_FREE_NUMBER = re.compile(r'\d|百分之[零一二三四五六七八九十百千万亿两]+|[零一二三四五六七八九十百千万亿两]+(?:元|盒|粒|袋|支|小时|个月|份|条)')


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


def advise(evaluation, snapshot, gateway_factory=None):
    """用决策路由（默认小模型）把决策依据转写为一段说明文字。

    约束：模型只允许返回 {"rationale": str}；超长、夹带数字或请求失败时
    返回降级说明，确定性决策保持不变。
    """
    route = (gateway_factory or _default_gateway_factory)('decision')
    if not getattr(route, 'key', ''):
        return {**evaluation, 'advisory_status': 'NO_KEY', 'advisory_model': route.model,
                'rationale': '未配置决策路由模型密钥，以上为确定性策略结论。'}
    system = ('你是成本分析系统的决策说明员。只返回JSON对象 {"rationale": "..."}。'
              'rationale 用不超过120字中文说明为什么建议该决策，只可复述输入中的信号，'
              '不得引入新数字、新结论或改变决策。')
    user = json.dumps({'decision': evaluation['decision'], 'reason': evaluation['reason'],
                       'signals': [{'id': s['id'], 'value': s['value'], 'detail': s['detail']} for s in evaluation['signals']],
                       'product': snapshot.get('product'), 'month': snapshot.get('month'),
                       'factory': snapshot.get('factory')}, ensure_ascii=False)
    try:
        raw, _usage, _identity = route.complete(system, user, operation='decision', prompt_version=ADVISORY_PROMPT_VERSION)
        parsed = json.loads(raw)
        rationale = parsed.get('rationale') if isinstance(parsed, dict) else None
        if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 120:
            raise ValueError('INVALID_ADVISORY_SHAPE')
        if _FREE_NUMBER.search(rationale):
            # 模型说明不得引入任何数字，与“模型不拥有数字”合同一致
            raise ValueError('ADVISORY_CONTAINS_NUMBERS')
        return {**evaluation, 'advisory_status': 'PASS', 'advisory_model': route.model,
                'advisory_prompt_version': ADVISORY_PROMPT_VERSION, 'rationale': rationale.strip()}
    except Exception as exc:
        return {**evaluation, 'advisory_status': 'DEGRADED', 'advisory_model': route.model,
                'rationale': '模型说明不可用（%s），以上为确定性策略结论。' % type(exc).__name__}


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
