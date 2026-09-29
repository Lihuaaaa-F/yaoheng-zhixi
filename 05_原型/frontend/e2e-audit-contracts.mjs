/** Synthetic UI audit regressions. Run against a Vite dev server; all API calls are intercepted. */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
assert.ok(process.env.PHARMA_E2E_URL, 'Set PHARMA_E2E_URL to an isolated Vite dev server');
const out = process.env.PHARMA_E2E_OUT ?? path.join(os.tmpdir(), 'yaoheng-audit-ui');
await mkdir(out, { recursive: true });
const selection = { context_id: 'synthetic:audit-ui', factory: '合成工厂', product: '合成产品', month: '2026-06', analysis_type: 'monthly', basis: 'unit' };
const snapshot = { ...selection, snapshot_id: 'synthetic-snapshot', metrics: {}, period: { start: '2026-06', end: '2026-06' }, comparison: { mom: { base: '10', current: '12' } }, elements: [{ key: 'material', name: '缺基期要素', unit: '12', total: '120', delta: null }] };
const action = { id: 'rejected', status: 'FAILED', error: 'HTTP_422:截止日期无效', retryable_edit: true, payload_hash: 'synthetic-hash', metadata: { context_id: selection.context_id, snapshot_id: snapshot.snapshot_id, selection }, payload: { task_title: '合成拒收任务', source: { product: selection.product, analysis_month: selection.month, finding: '合成问题' }, assignee: { name: '合成责任人', department: '合成部门' }, suggestion: '核查记录', priority: 'medium', action_details: { verification_target: '记录', expected_evidence: ['核查记录'], responsible_role: '核查员', deadline_basis: '复盘前' } } };
let jobs = [], reviewsFail = true;
const checks = [], failures = [], errors = [], requests = [];
const browser = await chromium.launch({ executablePath: process.env.PHARMA_CHROME_PATH || undefined, args: ['--no-sandbox'] });
try {
 const page = await browser.newPage({ viewport: { width: 1366, height: 768 }, reducedMotion: 'reduce' });
 page.on('pageerror', e => errors.push(e.message));
 page.on('console', message => { if (message.type() === 'error' && !message.text().includes('503')) errors.push(message.text()); });
 await page.addInitScript(() => localStorage.setItem('yaoheng.ui-preferences.v1', JSON.stringify({ taskNotifications: true })));
 await page.route('**/health', r => r.fulfill({ json: { status: 'ok' } }));
 await page.route('**/api/**', async route => {
  const req = route.request(), url = new URL(req.url()); requests.push({ path: url.pathname, method: req.method() });
  let value = {};
  if (url.pathname === '/api/workspace') value = { status: 'READY', context_id: selection.context_id, context: { company_name: '合成企业' }, data_snapshot: 'v1' };
  else if (url.pathname === '/api/catalog') value = { products: [selection.product], months: [selection.month], factories: [selection.factory] };
  else if (url.pathname === '/api/analyses') value = snapshot;
  else if (url.pathname === '/api/jobs') value = jobs;
  else if (url.pathname === '/api/actions') value = [action];
  else if (url.pathname === '/api/actions/rejected' && req.method() === 'PUT') { action.status = 'DRAFT'; action.retryable_edit = false; action.error = null; value = action; }
  else if (url.pathname.endsWith('/reviews')) {
   if (reviewsFail) return route.fulfill({ status: 503, json: { detail: '合成评审服务暂不可用' } });
   value = { reviews: [] };
  }
  else if (url.pathname === '/api/reports/preflight') value = { ready: true };
  else if (url.pathname === '/api/assistant/conversations') value = [];
  else if (url.pathname === '/api/settings/models') value = { connections: {} };
  else if (url.pathname === '/api/system/status') value = { deployment: { label: '合成环境' }, network: {} };
  await route.fulfill({ json: value });
 });
 const goto = async pageName => { const url = new URL(process.env.PHARMA_E2E_URL); url.searchParams.set('page', pageName); await page.goto(url.href); await page.getByRole('heading', { name: pageName === 'actions' ? '企业任务看板' : pageName === 'reports' ? '报告生成与下载' : '成本结构', exact: true }).waitFor(); };
 const check = async (name, run) => { try { await run(); checks.push(name); } catch(e) { failures.push({ name, error: e.message }); } };
 await goto('actions');
 await check('cleanText normalizes actual and escaped CRLF/tab', async () => {
  const actual = await page.evaluate(async () => { const { cleanText } = await import('/src/presentation.tsx'); return [cleanText(' 甲\r\n乙\t丙\r丁 '), cleanText('甲\\n乙\\t丙')]; });
  assert.deepEqual(actual, ['甲\n乙 丙\n丁', '甲\n乙 丙']);
 });
 await check('HTTP 422 rejection is visible and editable, save requires new confirmation', async () => {
  const card = page.locator('[data-task-id="rejected"]');
  assert.match(await card.innerText(), /HTTP_422:截止日期无效/);
  await card.scrollIntoViewIfNeeded(); await page.screenshot({ path: path.join(out, 'rejected-action.png') });
  await card.getByRole('button', { name: '修改后重新确认', exact: true }).click({ timeout: 3000 });
  await page.getByLabel('建议截止日期', { exact: true }).fill('2026-06-30');
  await page.getByRole('button', { name: '保存草稿修改', exact: true }).click();
  await card.getByRole('button', { name: '确认并发送模拟通知', exact: true }).waitFor();
  assert.equal(requests.some(r => r.path.endsWith('/confirm')), false);
 });
 await check('knowledge completion notification routes to knowledge', async () => {
  jobs = [{ id: 'kb-fixture', kind: 'kb', status: 'RUNNING', input: {} }];
  await page.getByRole('button', { name: '刷新状态', exact: true }).click();
  await page.waitForTimeout(100);
  jobs = [{ ...jobs[0], status: 'SUCCEEDED' }];
  await page.getByRole('button', { name: '刷新状态', exact: true }).click();
  const notice = page.locator('.ant-notification-notice'); await notice.waitFor({ timeout: 3000 });
  assert.match(await notice.innerText(), /知识库构建完成/);
  await notice.click(); await page.waitForURL('**page=knowledge**');
 });
 jobs = [{ id: 'report-fixture', kind: 'report', status: 'SUCCEEDED', input: selection, result: { snapshot, docx: { artifact_id: 'synthetic-docx' }, pdf: { artifact_id: 'synthetic-pdf' } } }];
 // The actual page heading is part of the contract, but avoid depending on report button names.
 const reportUrl = new URL(process.env.PHARMA_E2E_URL); reportUrl.searchParams.set('page', 'reports'); await page.goto(reportUrl.href);
 await page.locator('.job').waitFor();
 await check('review read failure is distinct from empty history and supports retry', async () => {
  const warning = page.getByRole('alert').filter({ hasText: '评审历史加载失败' });
  await warning.waitFor({ timeout: 3000 }); assert.match(await warning.innerText(), /合成评审服务暂不可用/);
  await warning.scrollIntoViewIfNeeded(); await page.screenshot({ path: path.join(out, 'reviews-error.png') });
  reviewsFail = false; await warning.getByRole('button', { name: '重试' }).click();
  await page.getByText('尚无评审记录。', { exact: true }).waitFor({ timeout: 3000 });
 });
 await page.screenshot({ path: path.join(out, 'reports-desktop.png') });
 jobs = [];
 await goto('analysis'); await page.locator('#g-bridge > summary').click();
 await check('missing bridge delta remains null with a missing-data tooltip', async () => {
  const state = await page.evaluate(async () => {
   const echarts = await import('/node_modules/.vite/deps/echarts_core.js');
   const chart = echarts.getInstanceByDom(document.querySelector('[aria-label="成本要素变动瀑布图"]'));
   const option = chart.getOption();
   return { value: option.series[1].data[1], tooltip: option.tooltip[0].formatter([{ dataIndex: 1, axisValue: '缺基期要素' }]) };
  });
  assert.equal(state.value, null); assert.match(state.tooltip, /无可比期/);
 });
 await page.setViewportSize({ width: 390, height: 844 });
 await page.locator('[aria-label="成本要素变动瀑布图"]').scrollIntoViewIfNeeded();
 await page.screenshot({ path: path.join(out, 'analysis-mobile.png') });
 assert.match(await page.title(), /药衡/);
 assert.ok((await page.locator('body').innerText()).includes('成本结构'));
 assert.equal(await page.locator('vite-error-overlay').count(), 0);
 const result = { status: failures.length || errors.length ? 'FAIL' : 'PASS', checks, failures, errors, page: page.url(), title: await page.title(), viewports: ['1366x768', '390x844'], browser: 'Playwright (Browser plugin not available)', scope: 'Synthetic intercepted APIs; no live models or actual human acceptance' };
 await writeFile(path.join(out, 'qa.json'), JSON.stringify(result, null, 2)); console.log(JSON.stringify(result, null, 2));
 if (result.status !== 'PASS') process.exitCode = 1;
} finally { await browser.close(); }
