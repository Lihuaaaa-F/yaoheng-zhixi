"""Report eligibility and selection contracts; no rendering or layout mutations."""
DEFAULT_TOPIC = '成本变化与证据核查'


def normalize_topic(analysis_type, topic=None):
    return ((topic or '').strip() or DEFAULT_TOPIC) if analysis_type == 'special' else ''


def report_readiness(snapshot):
    from .reports import _is_import, _full_template_context
    missing = []
    if _full_template_context(snapshot.get('context_id')) and _is_import(snapshot):
        present = {e['key'] for e in snapshot.get('elements', [])}
        for keys, label in (({'material', 'materials'}, '直接材料'), ({'labor'}, '直接人工'), ({'overhead'}, '制造费用')):
            if not present.intersection(keys): missing.append(label)
    return {'ready': not missing, 'missing_elements': missing,
            'message': ('完整报告缺少：'+'、'.join(missing)+'。请补充并映射这些成本要素；当前有效数据仍可用于看板。') if missing else '数据满足完整报告要素要求'}
