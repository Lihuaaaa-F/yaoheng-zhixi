/** Independent UI regressions. Requires an isolated app URL; all API calls are fixtures.
 * No cloud model request, enterprise-data mutation, or human review is performed.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

assert.ok(process.env.PHARMA_E2E_URL, '请用 PHARMA_E2E_URL 指定隔离测试实例');
const out = path.resolve(process.env.PHARMA_E2E_OUT ?? path.join(os.tmpdir(), 'yaoheng-delivery-ui'));
await mkdir(out, { recursive: true });
const selection = { context_id: 'synthetic:ui-contract', factory: '测试一厂', product: '独立测试产品', month: '2026-06', analysis_type: 'monthly', basis: 'unit' };
const action = (id, factory, snapshotId) => ({ id, status: 'DRAFT', payload_hash: 'independent-fixture',
  payload: { task_title: `${factory}整改`, source: { analysis_type: 'monthly', analysis_month: '2026-06', product: selection.product, finding: '独立测试问题' }, suggestion: '核查本厂设备记录', priority: 'medium', deadline: '2026-06-30', assignee: { name: '测试岗位', department: '测试部门' } },
  metadata: { context_id: selection.context_id, snapshot_id: snapshotId, selection: { ...selection, factory }, verification_target: '设备记录', expected_evidence: ['停机记录'], responsible_role: '设备维护员', deadline_basis: '复盘前核查' } });
const actions = [action('first', '测试一厂', 'first-snapshot'), action('second', '测试二厂', 'second-snapshot')];
const requests = [], errors = [], checks = [];
let modelLoadBarrier = null;
const browser = await chromium.launch({ executablePath: process.env.PHARMA_CHROME_PATH || undefined, headless: true, args: ['--no-sandbox'] });
try {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 }, locale: 'zh-CN', reducedMotion: 'reduce' });
  await page.addInitScript(() => {
    window.__workspaceAnimations = [];
    const original = Element.prototype.animate;
    Element.prototype.animate = function (...args) {
      if (this.classList.contains('business-main')) window.__workspaceAnimations.push(args);
      return original.apply(this, args);
    };
  });
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.route('**/health', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{"status":"ok"}' }));
  await page.route('**/api/**', async route => {
    const request = route.request(), url = new URL(request.url());
    const body = request.postData() ? JSON.parse(request.postData()) : null;
    requests.push({ path: url.pathname, method: request.method(), body });
    let value = {};
    if (url.pathname === '/api/workspace') value = { status: 'READY', context_id: selection.context_id, context: { context_id: selection.context_id, company_name: '独立测试企业' }, issues: [], pending_files: 0, data_snapshot: 'fixture-v1' };
    else if (url.pathname === '/api/catalog') value = { products: [selection.product], months: ['2026-06'], factories: ['测试一厂', '测试二厂'] };
    else if (url.pathname === '/api/analyses') value = { ...body, snapshot_id: body.factory === '测试一厂' ? 'first-snapshot' : 'second-snapshot', metrics: {}, elements: [], period: { start: body.month, end: body.month } };
    else if (url.pathname === '/api/actions') value = actions;
    else if (url.pathname.startsWith('/api/actions/')) value = actions.find(item => item.id === url.pathname.split('/').at(-1));
    else if (['/api/jobs', '/api/assistant/conversations'].includes(url.pathname)) value = [];
    else if (url.pathname === '/api/settings/models') {
      if (modelLoadBarrier) await modelLoadBarrier;
      value = { connections: { assistant: {}, analysis: {} } };
    }
    else if (url.pathname === '/api/settings/models/presets') value = { api_vendors: [], local_vendors: [] };
    else if (url.pathname === '/api/system/status') value = { deployment: { label: '本地运行' }, network: { status: 'not_checked' }, data: { updated_at: null } };
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(value) });
  });
  const url = new URL(process.env.PHARMA_E2E_URL); url.searchParams.set('page', 'actions');
  await page.goto(url.href);
  await page.locator('[data-task-id="first"]').waitFor();
  assert.deepEqual(await page.locator('[data-task-id]').evaluateAll(nodes => nodes.map(node => node.dataset.taskId)), ['first']);
  checks.push('同产品同月份的其他工厂任务不会混入当前筛选');
  await page.getByRole('combobox', { name: '工厂', exact: true }).click();
  await page.getByText('测试二厂', { exact: true }).last().click();
  await page.locator('[data-task-id="second"]').waitFor();
  await page.locator('[data-task-id="first"]').waitFor({ state: 'hidden' });
  checks.push('切换工厂后任务列表同步切换');
  await page.getByLabel('查看全部任务').check();
  await page.locator('[data-task-id="first"]').getByRole('button', { name: '编辑草稿' }).click();
  await Promise.all([
    page.waitForResponse(response => response.request().method() === 'PUT' && response.url().endsWith('/api/actions/first')),
    page.getByRole('button', { name: '保存草稿修改' }).click(),
  ]);
  assert.equal(requests.find(item => item.path === '/api/actions/first' && item.method === 'PUT').body.snapshot_id, 'first-snapshot');
  checks.push('从全部任务编辑历史草稿保留原快照');
  assert.equal(await page.evaluate(() => window.__workspaceAnimations.length), 0);
  checks.push('系统减少动态模式不执行工作区位移动画');
  const composer = page.getByRole('textbox', { name: '向 AI 助手提问', exact: true });
  await composer.fill('核对单位成本变化');
  assert.equal(await composer.inputValue(), '核对单位成本变化', '助手输入框应保留真实键盘输入');
  assert.equal(await page.getByRole('button', { name: '发送消息', exact: true }).isEnabled(), true);
  checks.push('助手输入框能编辑中文并启用发送');
  let releaseModelLoad;
  modelLoadBarrier = new Promise(resolve => { releaseModelLoad = resolve; });
  await page.getByRole('menuitem', { name: /模型连接/ }).click();
  const modelName = page.getByLabel('模型名称', { exact: true });
  await modelName.waitFor();
  assert.equal(await modelName.isEnabled(), false, '读取模型配置期间禁止输入，避免晚到响应覆盖草稿');
  assert.equal(await page.getByRole('button', { name: /保存设置/ }).isEnabled(), false);
  await page.getByRole('tab', { name: '对话助手', exact: true }).click();
  assert.equal(await modelName.isEnabled(), false, '切换路由后继续等待对应配置');
  modelLoadBarrier = null;
  releaseModelLoad();
  await modelName.fill('independent-local-model');
  assert.equal(await modelName.inputValue(), 'independent-local-model');
  assert.equal(await page.getByRole('button', { name: /保存设置/ }).isEnabled(), true);
  checks.push('模型配置读取期间不可编辑或保存；路由切换后仅启用当前配置');
  assert.deepEqual(errors, []);
  await page.screenshot({ path: path.join(out, 'rectification.png') });
  const result = { status: 'PASS', scope: 'Independent synthetic browser contracts; not a human acceptance or live provider test', checks, errors };
  await writeFile(path.join(out, 'qa.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally { await browser.close(); }
