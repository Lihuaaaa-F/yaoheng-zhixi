"""Tab state must never be confused with chat retention or running turn state."""
import json
import sqlite3

import pytest

from pharma.assistant import AssistantStore


def test_additive_migration_preserves_legacy_history(tmp_path):
    path = tmp_path / 'old.sqlite3'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE conversations(id TEXT PRIMARY KEY,title TEXT,context TEXT,created_at TEXT,updated_at TEXT)')
        db.executemany('INSERT INTO conversations VALUES(?,?,?,?,?)', [
            ('old', '早期提问', '{}', '2026-01-01', '2026-01-01'),
            ('recent', '最近提问', '{}', '2026-02-01', '2026-02-01')])
    ledger = AssistantStore(path)
    assert len(ledger.list(state='history')) == 2
    assert [c['id'] for c in ledger.list(state='open')] == ['recent']
    ledger.update('recent', 'close')
    # Reopening the service does not undo a user's close or re-run the migration.
    assert AssistantStore(path).list(state='open') == []
    assert ledger.conversation('old')['title'] == '早期提问'


def test_close_pin_archive_restore_have_distinct_persistent_meanings(tmp_path):
    ledger = AssistantStore(tmp_path / 'chat.sqlite3')
    first = ledger.create()['id']
    second = ledger.create()['id']
    ledger.update(first, 'pin')
    assert ledger.list(state='open')[0]['id'] == first
    ledger.update(first, 'close')
    assert [c['id'] for c in ledger.list(state='open')] == [second]
    assert len(ledger.list(state='history')) == 2
    assert ledger.conversation(first)['pinned'] is True
    ledger.update(first, 'open')
    ledger.update(first, 'archive')
    assert [c['id'] for c in ledger.list(state='history')] == [second]
    assert ledger.list(state='archived')[0]['id'] == first
    with pytest.raises(ValueError):
        ledger.update(first, 'open')
    ledger.update(first, 'unarchive')
    assert not ledger.conversation(first)['is_open']
    ledger.update(first, 'open')
    assert AssistantStore(ledger.path).conversation(first)['is_open'] is True


def test_close_preserves_running_answer_but_archive_discards_late_answer(tmp_path):
    ledger = AssistantStore(tmp_path / 'chat.sqlite3')
    cid = ledger.create()['id']
    turn = ledger.enqueue(cid, '第一轮', {}, 'one')
    ledger.stage(turn['id'], 'generating')
    ledger.update(cid, 'close')
    assert ledger.finish(turn['id'], {'content': '已保存回答'})
    assert len(ledger.conversation(cid)['messages']) == 2
    with pytest.raises(ValueError):
        ledger.enqueue(cid, '关闭后发送', {}, 'invalid')
    ledger.update(cid, 'open')
    later = ledger.enqueue(cid, '第二轮', {}, 'two')
    ledger.stage(later['id'], 'generating')
    ledger.update(cid, 'archive')
    assert ledger.turn(later['id'])['status'] == 'cancelled'
    assert not ledger.finish(later['id'], {'content': '不应晚到的回答'})
    assert len(ledger.conversation(cid)['messages']) == 3


def test_delete_removes_only_chat_and_never_resurrects_a_late_response(tmp_path):
    ledger = AssistantStore(tmp_path / 'chat.sqlite3')
    target, other = ledger.create()['id'], ledger.create()['id']
    turn = ledger.enqueue(target, '准备报告', {}, 'one')
    ledger.stage(turn['id'], 'generating')
    proposal = {'id': 'proposal-one', 'kind': 'generate_report'}
    ledger.finish(turn['id'], {'content': '待确认', 'proposals': [proposal]}, [proposal])
    pending = ledger.enqueue(target, '在途请求', {}, 'two')
    ledger.stage(pending['id'], 'generating')
    assert ledger.delete(target) == {'id': target, 'deleted': True}
    assert ledger.delete(target)['deleted']  # Idempotent UI retries.
    assert not ledger.finish(pending['id'], {'content': '迟到内容'})
    assert ledger.conversation(other)['messages'] == []
    with pytest.raises(KeyError):
        ledger.conversation(target)
    with pytest.raises(KeyError):
        ledger.proposal('proposal-one')
    with ledger.db() as db:
        assert db.execute('SELECT count(*) FROM messages').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM turns').fetchone()[0] == 0


def test_archived_proposal_cannot_execute_before_restore(tmp_path):
    ledger = AssistantStore(tmp_path / 'chat.sqlite3')
    cid = ledger.create()['id']
    turn = ledger.enqueue(cid, '准备报告', {}, 'one')
    ledger.stage(turn['id'], 'generating')
    proposal = {'id': 'proposal-one', 'kind': 'generate_report'}
    ledger.finish(turn['id'], {'content': '待确认'}, [proposal])
    ledger.update(cid, 'archive')
    called = []
    with pytest.raises(ValueError):
        ledger.confirm('proposal-one', lambda p: called.append(p))
    assert not called


def test_history_and_open_overflow_are_not_truncated_at_one_hundred(tmp_path):
    ledger = AssistantStore(tmp_path / 'chat.sqlite3')
    for _ in range(123):
        ledger.create({'context_id': 'workspace'})
    assert len(ledger.list('workspace', 'open')) == 123
    assert len(ledger.list(state='history')) == 123
    assert not ledger.list('other', 'open')


def test_http_lifecycle_contract(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from pharma import api
    monkeypatch.setattr(api, 'assistant_store', AssistantStore(tmp_path / 'api.sqlite3'))
    monkeypatch.delenv('PHARMA_API_TOKEN', raising=False)
    client = TestClient(api.app)
    created = client.post('/api/assistant/conversations', json={})
    assert created.status_code == 201
    cid = created.json()['id']
    assert created.json()['is_open'] is True
    assert client.patch(f'/api/assistant/conversations/{cid}', json={'action': 'pin'}).json()['pinned'] is True
    assert client.patch(f'/api/assistant/conversations/{cid}', json={'action': 'close'}).status_code == 200
    assert client.get('/api/assistant/conversations?state=open').json()['conversations'] == []
    assert len(client.get('/api/assistant/conversations?state=history').json()['conversations']) == 1
    assert client.patch(f'/api/assistant/conversations/{cid}', json={'action': 'invalid'}).status_code == 422
    assert client.delete(f'/api/assistant/conversations/{cid}').json()['deleted']
    assert client.get(f'/api/assistant/conversations/{cid}').status_code == 404
