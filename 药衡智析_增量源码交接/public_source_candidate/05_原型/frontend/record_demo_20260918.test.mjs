import test from 'node:test';
import assert from 'node:assert/strict';
import {requireLoopback, validateHealth, validateJob} from './record_demo_20260918.mjs';

test('recording refuses external services before confirmation', () => {
  for (const url of ['https://example.com', 'http://127.0.0.1.evil.test', 'http://user:secret@localhost', 'file:///tmp/a'])
    assert.throws(() => requireLoopback(url));
  for (const url of ['http://localhost:8765', 'http://127.0.0.2:8765', 'http://[::1]:8765']) assert.doesNotThrow(() => requireLoopback(url));
  assert.throws(() => validateHealth({simulation: true, rpa_mode: 'local_simulator', rpa_base_url: 'https://external.invalid'}));
  assert.throws(() => validateHealth({simulation: false, rpa_mode: 'local_simulator', rpa_base_url: 'http://127.0.0.1:8090'}));
  assert.throws(() => validateHealth({simulation: true, rpa_mode: 'unverified', rpa_base_url: 'http://127.0.0.1:8090'}));
});

test('report readiness binds run, selection and both real artifact hashes', () => {
  const selection = {product: '合成产品', factory: '甲厂', month: '2026-06'};
  const artifact = {status: 'PASS', artifact_id: 'fixture-id', sha256: 'a'.repeat(64)};
  const job = {status: 'DEGRADED', input: {...selection, run_id: 'run-fixture'}, result: {docx: artifact, pdf: artifact}};
  assert.equal(validateJob(job, 'run-fixture', selection), job);
  assert.throws(() => validateJob(job, 'different-run', selection));
  assert.throws(() => validateJob(job, 'run-fixture', {...selection, product: '另一产品'}));
  assert.throws(() => validateJob({...job, status: 'FAILED'}, 'run-fixture', selection));
  assert.throws(() => validateJob({...job, result: {docx: artifact}}, 'run-fixture', selection));
});
