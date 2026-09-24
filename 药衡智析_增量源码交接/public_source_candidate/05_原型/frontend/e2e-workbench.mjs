/**
 * Current UI smoke: actual backend, read-only browser actions, no provider generation.
 * Start an ISOLATED instance with PHARMA_AUTO_EXPLAIN=0 and no cloud model keys.
 * Never point this runner at a shared production instance: analysis reads may warm caches.
 * PHARMA_E2E_URL is mandatory. PHARMA_CHROME_PATH reuses an installed Chromium;
 * otherwise Playwright's existing browser cache is used (nothing is downloaded here).
 * PHARMA_E2E_OUT chooses the screenshot/JSON directory; PHARMA_API_TOKEN is optional.
 * Scope: navigation, runtime errors, overflow, and assistant controls. This is not
 * model quality, generated report, RPA delivery, or human visual acceptance evidence.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

if (!process.env.PHARMA_E2E_URL) {
  console.error('请先启动隔离测试实例（PHARMA_AUTO_EXPLAIN=0，移除云端模型密钥），再执行：PHARMA_E2E_URL=http://127.0.0.1:8000 npm run e2e。可用 PHARMA_CHROME_PATH 指定已有 Chromium，PHARMA_E2E_OUT 指定输出目录。');
  process.exit(2);
}
const base = new URL(process.env.PHARMA_E2E_URL);
assert.ok(['http:', 'https:'].includes(base.protocol), 'PHARMA_E2E_URL 必须为 HTTP(S) 地址');
assert.ok(!base.username && !base.password, '访问令牌请通过 PHARMA_API_TOKEN 提供，不要写入 URL');
const out = path.resolve(process.env.PHARMA_E2E_OUT ?? path.join(os.tmpdir(), 'yaoheng-workbench-ui'));
const pages = [
  ['analysis', '成本分析'], ['benchmark', '跨厂对标'], ['reports', '分析报告'], ['actions', '问题整改'],
  ['business', '业务数据'], ['knowledge', '知识库'], ['templates', '报告模板'], ['models', '模型连接'], ['settings', '系统设置'],
];
const checks = [], errors = [], blockedWrites = [];
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.PHARMA_CHROME_PATH || undefined, headless: true, args: ['--no-sandbox'] });
try {
  for (const viewport of [{ width: 1366, height: 768 }, { width: 390, height: 844 }]) {
    const context = await browser.newContext({ viewport, locale: 'zh-CN', reducedMotion: 'reduce' });
    await context.route('**/api/**', route => {
      const request = route.request(), pathname = new URL(request.url()).pathname;
      const readPost = request.method() === 'POST' && ['/api/analyses', '/api/assistant/context', '/api/kb/search'].includes(pathname);
      if (!['GET', 'HEAD', 'OPTIONS'].includes(request.method()) && !readPost) {
        blockedWrites.push({ method: request.method(), path: pathname });
        return route.abort('blockedbyclient');
      }
      // The benchmark UI normally requests async explanations; that GET may enqueue a report.
      // This read-only smoke explicitly asks for numeric comparison without generation.
      const readUrl = new URL(request.url());
      if (pathname === '/api/benchmarks') readUrl.searchParams.set('explain', 'none');
      return route.continue({
        url: readUrl.href,
        ...(process.env.PHARMA_API_TOKEN ? { headers: { ...request.headers(), 'X-API-Token': process.env.PHARMA_API_TOKEN } } : {}),
      });
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);
    page.on('pageerror', error => errors.push({ type: 'pageerror', message: error.message }));
    page.on('console', message => { if (message.type() === 'error') errors.push({ type: 'console', message: message.text() }); });
    for (const [key, heading] of pages) {
      const url = new URL(base); url.searchParams.set('page', key);
      await page.goto(url.href, { waitUntil: 'domcontentloaded' });
      await page.getByRole('main', { name: `${heading}工作区`, exact: true }).waitFor();
      // Wait for the shell's read requests, not animations or arbitrary long sleeps.
      await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
      await page.locator('.business-loading').waitFor({ state: 'hidden', timeout: 60000 });
      assert.equal(await page.locator('vite-error-overlay').count(), 0, `${heading}: Vite 错误遮罩`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, `${heading}: 页面横向溢出`);
      assert.equal(await page.locator('.workbench-content').evaluate(node => node.scrollWidth <= node.clientWidth + 1), true, `${heading}: 业务区横向溢出`);
      assert.equal(await page.getByRole('combobox', { name: '数据范围', exact: true }).count(), 0, '不应出现数据范围选择器');
      if (key === 'analysis') {
        assert.equal(await page.getByRole('heading', { level: 1, name: '成本分析', exact: true }).count(), 0, '不应保留多余的成本分析标题');
        const tabs = page.getByRole('navigation', { name: '工作台分区导航', exact: true });
        const before = (await tabs.boundingBox()).y;
        await page.locator('.workspace-scroll').evaluate(node => { node.scrollTop = 500; });
        assert.ok(Math.abs((await tabs.boundingBox()).y - before) < 1, '工作区分区导航应保持固定');
        await page.locator('.workspace-scroll').evaluate(node => { node.scrollTop = 0; });
      }
      if (key === 'analysis' && viewport.width === 390) await page.getByRole('button', { name: '打开对话', exact: true }).click();
      if (viewport.width === 1366 || key === 'analysis') {
        const composer = page.locator('.assistant-composer:visible');
        await composer.waitFor();
        const ring = composer.locator('.assistant-context-indicator');
        assert.equal((await ring.innerText()).trim(), '', '上下文圆环不应常驻文字');
        assert.equal(await ring.locator('svg').count(), 1, '上下文圆环应为真实控件');
        assert.doesNotMatch(await composer.innerText(), /模型连接在左侧设置|数字来自分析引擎|数字由分析引擎提供|外部操作需确认/);
        await composer.getByRole('button', { name: /选择助手模型与推理强度/ }).waitFor();
        await composer.getByRole('textbox', { name: '向 AI 助手提问' }).waitFor();
        if (viewport.width === 390) await page.locator('.ant-drawer:visible .ant-drawer-close').click();
      }
      await page.screenshot({ path: path.join(out, `${key}-${viewport.width}.png`) });
      checks.push({ page: key, viewport, heading, no_horizontal_overflow: true });
    }
    await context.close();
  }
  assert.deepEqual(blockedWrites, [], '浏览器读页面意外触发了写入请求');
  assert.deepEqual(errors, [], '存在浏览器控制台或运行时错误');
  await writeFile(path.join(out, 'qa.json'), JSON.stringify({ status: 'PASS', scope: '只读工作台导航与浏览器合同；不包含模型、报告、RPA或真人验收', checks, errors, blockedWrites }, null, 2));
  console.log(JSON.stringify({ status: 'PASS', pages: pages.length, viewports: 2, out }));
} catch (error) {
  await writeFile(path.join(out, 'failure.json'), JSON.stringify({ status: 'FAIL', error: String(error), checks, errors, blockedWrites }, null, 2));
  throw error;
} finally { await browser.close(); }
