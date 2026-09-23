"""Scope-bound service adapters shared by HTTP handlers and queued jobs."""
from hashlib import sha256
import json
import os
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .knowledge import Knowledge, source_snapshot, scoped_knowledge_snapshot, knowledge_context_id

PURPOSE_STRATEGY_VERSION='current-period-event-reservation-graph-v3-keyword-only'


class EventPurpose(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1,max_length=80,pattern=r'^[a-z_]+$')
    query_terms:list[str]=Field(min_length=1,max_length=4)
    event_match_terms:list[str]=Field(min_length=1,max_length=4)
    reserved_slots:Literal[1]=1


class RetrievalPolicy(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version:str=Field(min_length=1,max_length=40)
    max_supplemental_queries:Literal[1]=1
    purpose:EventPurpose


def retrieval_policy(context):
    """Only an installed, validated pack can supply this bounded JSON policy."""
    if not context or not context.get('industry_id'):return None
    from .industry import PACKS,load_pack
    pack=load_pack(context['industry_id'])
    path=PACKS/pack.id/'retrieval.json'
    if not path.is_file():return None
    policy=RetrievalPolicy.model_validate(json.loads(path.read_text(encoding='utf-8')))
    for term in [*policy.purpose.query_terms,*policy.purpose.event_match_terms]:
        if not term.strip() or len(term)>40 or any(c in term for c in ('[',']','{','}','\n')):
            raise ValueError('INVALID_RETRIEVAL_PURPOSE_TERM')
    return policy


def _graph_enabled():
    return os.getenv('PHARMA_GRAPH_ENABLED','true').strip().lower() not in ('0','false','no','off')


def _policy_version(policy, graph_enabled=None):
    value={'strategy':PURPOSE_STRATEGY_VERSION,'policy':policy.model_dump() if policy else None,
           'graph_enabled':_graph_enabled() if graph_enabled is None else graph_enabled}
    return sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def retrieval_policy_version(context):
    return _policy_version(retrieval_policy(context))


def _matching_event(row,snapshot,purpose):
    period=snapshot.get('period') or {};event=row.get('event_period')
    if not event or not period.get('start') or not period.get('end') or not period['start']<=event<=period['end']:return False
    if not any(term in row.get('text','') for term in purpose.event_match_terms):return False
    return Knowledge.evidence_applicability(row,product=snapshot.get('product'),factory=snapshot.get('factory'),
        period=period,specification=snapshot.get('specification'),context=snapshot.get('analysis_context'))['applicable']


def knowledge_for_context(context=None):
    """Resolve exactly one enterprise's sources for HTTP, reports and assistants."""
    context = context.model_dump() if hasattr(context, 'model_dump') else dict(context or {})
    if not context:
        return Knowledge()
    context_id = knowledge_context_id(context)
    if context_id == 'pharmaceutical:competition':
        knowledge = Knowledge(context=context)
        if scoped_knowledge_snapshot(context_id, source_snapshot(knowledge.source_dir)) != context.get('knowledge_snapshot'):
            raise ValueError('KNOWLEDGE_SNAPSHOT_CHANGED')
    else:
        from .industry import knowledge_entry_for_context, AnalysisContext
        entry = knowledge_entry_for_context(AnalysisContext.model_validate(context))
        if scoped_knowledge_snapshot(context_id, sha256(entry.read_bytes()).hexdigest()) != context.get('knowledge_snapshot'):
            raise ValueError('KNOWLEDGE_SNAPSHOT_CHANGED')
        knowledge = Knowledge(context=context, source_files=(entry,))
    return knowledge


def retrieve(snapshot, query, *, mode='hybrid', limit=8, graph_enabled=None):
    if not isinstance(limit,int) or isinstance(limit,bool) or not 1<=limit<=100:raise ValueError('INVALID_RETRIEVAL_LIMIT')
    context = snapshot.get('analysis_context') or {}
    policy=retrieval_policy(context)
    knowledge = knowledge_for_context(context)
    scope={'product':snapshot.get('product'),'factory':snapshot.get('factory'),
           'period':snapshot.get('period'),'specification':snapshot.get('specification'),'mode':mode,'limit':limit}
    # 知识图谱增强（赛题加分项）：制药上下文且图谱存在时，把该产品的
    # 配方药材/工序名补充进 BM25 查询词；向量检索与适用性合同保持不变。
    graph_enabled=_graph_enabled() if graph_enabled is None else graph_enabled
    expansion={'status':'NOT_APPLICABLE' if graph_enabled else 'DISABLED','terms':[]}
    if graph_enabled and context.get('industry_id')=='pharmaceutical':
        try:
            from .graph import KnowledgeGraph
            expansion=KnowledgeGraph(knowledge).expansion_terms(snapshot.get('product'),query)
        except Exception as exc:
            expansion={'status':'DEGRADED','terms':[],'reason':type(exc).__name__}
    effective=query if not expansion.get('terms') else query+' '+' '.join(expansion['terms'])
    result=knowledge.search(query,**scope,keyword_query=effective)
    # 增益状态：2026-09-23 小样本对照（scripts/eval_graph_gain.py，10 查询 Top-5+MRR）
    # 实测本查询集无正增益（基线已 10/10 命中）——如实标注，不宣称检索收益。
    expansion.update(experimental=True,scope='bm25_only',gain_status='EVALUATED_SMALL_SAMPLE_NO_GAIN',
                     gain_evidence='docs/validation/graph_gain_20260923.json')
    result['graph_expansion']=expansion
    result['retrieval_policy_version']=_policy_version(policy,graph_enabled)
    diagnostic={'query_budget':1+(policy.max_supplemental_queries if policy else 0),'queries_executed':1,
                'total_evidence_limit':limit,'status':'NOT_CONFIGURED'}
    result['purpose_retrieval']=diagnostic
    if not policy:return result
    purpose=policy.purpose;diagnostic['purpose_id']=purpose.id
    if any(_matching_event(row,snapshot,purpose) for row in result.get('evidence',[])):
        diagnostic['status']='ALREADY_COVERED';return result
    period=snapshot.get('period') or {}
    if not snapshot.get('product') or not period.get('start') or not period.get('end'):
        diagnostic['status']='MISSING_EVENT_SCOPE';return result
    supplemental_query=snapshot['product']+' '+' '.join(purpose.query_terms)
    extra=knowledge.search(supplemental_query,**scope,event_only=True)
    if extra.get('knowledge_version')!=result.get('knowledge_version'):raise ValueError('KNOWLEDGE_CHANGED_DURING_PURPOSE_RETRIEVAL')
    selected=[row for row in extra.get('evidence',[]) if _matching_event(row,snapshot,purpose)][:purpose.reserved_slots]
    diagnostic.update(queries_executed=2,status='RECALLED' if selected else 'NO_APPLICABLE_EVENT_RECALLED',
                      eligible_event_count=extra.get('eligible_count'),selected_count=len(selected),
                      retrieval_status=extra.get('retrieval_status'),reason=extra.get('reason'))
    if selected:
        ids={row['evidence_id'] for row in selected}
        baseline=[];seen=set(ids)
        for row in result.get('evidence',[]):
            if row['evidence_id'] not in seen:baseline.append(row);seen.add(row['evidence_id'])
        result['evidence']=baseline[:max(0,limit-len(selected))]+[{**row,'retrieval_purpose':purpose.id} for row in selected]
        result['recall_status']='RECALLED'
    if extra.get('status')!='PASS':
        result['status']='DEGRADED';result['retrieval_status']='DEGRADED'
        result['reason']=result.get('reason') or 'PURPOSE_RETRIEVAL_'+str(extra.get('reason') or extra.get('status'))
    return result
