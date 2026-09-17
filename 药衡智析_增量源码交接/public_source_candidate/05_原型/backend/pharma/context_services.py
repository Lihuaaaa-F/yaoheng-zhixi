"""Scope-bound service adapters shared by HTTP handlers and queued jobs."""
from hashlib import sha256
from .knowledge import Knowledge, source_snapshot


def retrieve(snapshot, query, *, mode='hybrid', limit=8):
    context = snapshot.get('analysis_context') or {}
    if not context:
        knowledge = Knowledge()
    elif context.get('industry_id') == 'pharmaceutical' and context.get('enterprise_id') == 'competition':
        knowledge = Knowledge(context=context)
        if source_snapshot(knowledge.source_dir) != context.get('knowledge_snapshot'):
            raise ValueError('KNOWLEDGE_SNAPSHOT_CHANGED')
    else:
        from .industry import knowledge_entry_for_context, AnalysisContext
        entry = knowledge_entry_for_context(AnalysisContext.model_validate(context))
        if sha256(entry.read_bytes()).hexdigest() != context.get('knowledge_snapshot'):
            raise ValueError('KNOWLEDGE_SNAPSHOT_CHANGED')
        knowledge = Knowledge(context=context, source_files=(entry,))
    return knowledge.search(query, product=snapshot.get('product'), factory=snapshot.get('factory'),
                            period=snapshot.get('period'), specification=snapshot.get('specification'),
                            mode=mode, limit=limit)
