from pharma.actions import ActionStore as StrictActionStore

class ActionStore(StrictActionStore):
    """Legacy scenarios supply explicit synthetic fields required by v2 contract."""
    def draft(self,*args,**kwargs):
        defaults=dict(verification_target="合成台账",expected_evidence=["合成签字记录"],responsible_role="成本会计",deadline_basis="月度核查前")
        return super().draft(*args,**{**defaults,**kwargs})

def test_confirm_is_required_and_duplicate_confirmation_is_idempotent(tmp_path):
    s=ActionStore(tmp_path/'actions.sqlite')
    snapshot={'snapshot_id':'fixture-1','analysis_type':'quarterly','month':'2026-06','product':'合成产品','period':{'start':'2026-04','end':'2026-06'}}
    draft=s.draft(snapshot,'核查记录',{'name':'演示责任人','department':'演示部'},'先核查，变更须批准','medium')
    assert draft['status']=='DRAFT'
    assert s.pending()==[]
    confirmed=s.confirm(draft['id'],draft['payload_hash'])
    assert confirmed['status']=='QUEUED'
    assert s.confirm(draft['id'],draft['payload_hash'])['id']==draft['id']
    assert len(s.pending())==1
    assert confirmed['payload']['source']['analysis_month']=='2026-06'

def prepared(tmp_path):
    s=ActionStore(tmp_path/'actions.sqlite')
    a=s.draft({'snapshot_id':'external-fixture','analysis_type':'monthly','month':'2026-03','product':'合成品'},'检查设备记录',{'name':'演示责任人','department':'演示部'},'先核查记录')
    return s,s.confirm(a['id'],a['payload_hash'])

def test_read_timeout_reconciles_payload_without_second_send(tmp_path):
    import httpx
    s,a=prepared(tmp_path);posts=[]
    def handler(request):
        if request.method=='POST':
            posts.append(1);raise httpx.ReadTimeout('fixture timeout',request=request)
        return httpx.Response(200,json={'code':200,'data':{**a['payload'],'status':'sent','notify_status':{'wechat':'已发送至 演示责任人(演示部)','sent_at':'fixture'}}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        assert s.deliver_one(a['id'],c)['status']=='SENT'
        assert s.deliver_one(a['id'],c)['status']=='SENT'
    assert len(posts)==1

def test_duplicate_400_conflict_and_422_are_distinct(tmp_path):
    import httpx
    for code,conflict,expected in [(400,False,'SENT'),(400,True,'CONFLICT'),(422,False,'FAILED')]:
        folder=tmp_path/str(code)/str(conflict);folder.mkdir(parents=True)
        s,a=prepared(folder)
        def handler(request):
            if request.method=='POST':return httpx.Response(code,json={'detail':'原mock错误格式'})
            remote={**a['payload'],'status':'sent','notify_status':{'wechat':'已发送至 演示责任人(演示部)','sent_at':'fixture'}}
            if conflict:remote['suggestion']='不同内容'
            return httpx.Response(200,json={'code':200,'data':remote})
        with httpx.Client(transport=httpx.MockTransport(handler)) as c:assert s.deliver_one(a['id'],c)['status']==expected

def test_disconnect_unknown_and_remote_restart_never_resends(tmp_path):
    import httpx
    s,a=prepared(tmp_path);posts=[]
    def disconnected(request):
        posts.append(request.method);raise httpx.ConnectError('offline',request=request)
    with httpx.Client(transport=httpx.MockTransport(disconnected)) as c:
        assert s.deliver_one(a['id'],c)['status']=='DELIVERY_UNKNOWN'
        assert s.deliver_one(a['id'],c)['status']=='DELIVERY_UNKNOWN'
    assert posts==['POST','GET']
    other=tmp_path/'other';other.mkdir();s,a=prepared(other)
    def accepted(request):return httpx.Response(200,json={'code':200,'data':{'task_id':a['id'],'status':'sent','notify_status':{'wechat':'已发送至 演示责任人(演示部)','sent_at':'now'}}})
    with httpx.Client(transport=httpx.MockTransport(accepted)) as c:assert s.deliver_one(a['id'],c)['status']=='SENT'
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(404,json={'detail':'restart'}))) as c:
        assert s.refresh(a['id'],c)['status']=='REMOTE_UNKNOWN'
        assert s.deliver_one(a['id'],c)['status']=='REMOTE_UNKNOWN'

def test_edit_requires_matching_confirmation_hash(tmp_path):
    import pytest
    s=ActionStore(tmp_path/'actions.sqlite')
    a=s.draft({'snapshot_id':'edit','analysis_type':'monthly','month':'2026-03','product':'合成'},'原原因',{'name':'演示责任人','department':'演示部'},'核查')
    b=s.edit(a['id'],{'finding':'修订原因','suggestion':'修订建议'})
    assert '修订原因' in b['payload']['source']['finding']
    assert b['payload_hash']!=a['payload_hash']
    with pytest.raises(ValueError,match='RECONFIRM'):s.confirm(a['id'],a['payload_hash'])
    assert s.confirm(a['id'],b['payload_hash'])['status']=='QUEUED'


def test_received_is_not_notification_sent(tmp_path):
    import httpx
    s,a=prepared(tmp_path)
    def handler(request):
        if request.method=='POST':raise httpx.ReadTimeout('fixture',request=request)
        return httpx.Response(200,json={'code':200,'data':{**a['payload'],'status':'received'}})
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        result=s.deliver_one(a['id'],c)
        assert result['status']=='ACCEPTED'
        assert result['delivery']['http_accepted']
        assert result['delivery']['notification']=='UNKNOWN'
        assert s.deliver_one(a['id'],c)['status']=='ACCEPTED'


def test_action_details_edit_requires_reconfirmation(tmp_path):
    import pytest
    s=ActionStore(tmp_path/'details.sqlite')
    a=s.draft({'snapshot_id':'details','analysis_type':'monthly','month':'2026-05','product':'合成'},'核查材料',{'name':'待分配','department':'财务'},'核对单据',verification_target='入库单',expected_evidence=['入库价'],responsible_role='成本会计',deadline_basis='月度复核前')
    b=s.edit(a['id'],{'verification_target':'入库单和退料单'})
    assert b['payload_hash']!=a['payload_hash']
    assert b['metadata']['verification_target']=='入库单和退料单'
    with pytest.raises(ValueError,match='RECONFIRM'):s.confirm(a['id'],a['payload_hash'])

def test_original_draft_can_be_recreated_after_edit_without_overwrite(tmp_path):
    s=ActionStore(tmp_path/'edited.sqlite')
    args=({'snapshot_id':'same','analysis_type':'monthly','month':'2026-05','product':'合成'},'核查',{'name':'待分配','department':'财务'},'核查原始单据')
    first=s.draft(*args,verification_target='原始对象')
    edited=s.edit(first['id'],{'verification_target':'修订对象'})
    new=s.draft(*args,verification_target='原始对象')
    assert new['id']!=edited['id']
    assert s.get(edited['id'])['metadata']['verification_target']=='修订对象'
    assert s.draft(*args,verification_target='原始对象')['id']==new['id']
