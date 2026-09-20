/**
 * 药衡智析 · 全流程演示视频录制脚本（2026-09-20）
 *
 * 产物：单段连续 WebM（Playwright recordVideo，帧保持、时长=真实墙钟），
 *       后续经 ffmpeg 转 H.264 MP4 交付。
 * 特性：
 *  - 页内 DOM 光标（SVG 箭头，easeInOutQuad，速度按距离自适应＝适中）
 *  - 每次操作叠加中文注释（顶部/底部横幅，避开正文关键区）
 *  - 节奏：光标移动到位后停留 1s；每次操作后按信息量停 2-4s
 *  - 真实点击带涟漪特效；所有交互走真实 UI 控件（预置数据已预热，无现场等待）
 * 运行：cd 05_原型/frontend && node record_full_demo_20260920.mjs
 */
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const BASE = process.env.DEMO_BASE ?? 'http://127.0.0.1:8765';
const OUT_DIR = process.env.DEMO_OUT ?? 'D:/yh_video';
mkdirSync(OUT_DIR, { recursive: true });

const MOVE_HOLD = 1000;   // 纯光标移动到位后的间隔：1 秒
const OP2 = 2000, OP3 = 3000, OP4 = 4000; // 操作后间隔按信息量 2-4 秒

let T0 = Date.now();
const log = (...a) => console.log(`[${((Date.now() - T0) / 1000).toFixed(1)}s]`, ...a);
const sleep = ms => page.waitForTimeout(ms);

let page;

const DRIVER = () => {
  document.getElementById('demo-cursor')?.remove();
  document.getElementById('demo-anno')?.remove();
  const cur = document.createElement('div');
  cur.id = 'demo-cursor';
  cur.innerHTML = '<svg width="30" height="34" viewBox="0 0 30 34"><path d="M3 1 L3 27 L10 20.5 L15 31 L20 28.6 L15 18.5 L24 17.5 Z" fill="#111" stroke="#fff" stroke-width="1.6"/></svg>';
  cur.style.cssText = 'position:fixed;left:0;top:0;z-index:999998;pointer-events:none;will-change:transform;filter:drop-shadow(1px 2px 3px rgba(0,0,0,.35))';
  document.body.appendChild(cur);
  const st = { x: 700, y: 400, from: null, t0: 0, dur: 0, tx: 700, ty: 400 };
  window.__cur = st;
  function loop(t) {
    if (st.from) {
      const k = Math.min(1, (t - st.t0) / st.dur);
      const e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      st.x = st.from.x + (st.tx - st.from.x) * e;
      st.y = st.from.y + (st.ty - st.from.y) * e;
      if (k >= 1) st.from = null;
    } else { st.x += Math.sin(t / 650) * 0.3; }
    cur.style.transform = `translate(${st.x}px,${st.y}px)`;
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
  window.__move = (x, y, dur) => { st.from = { x: st.x, y: st.y }; st.tx = x; st.ty = y; st.t0 = performance.now(); st.dur = dur; };
  window.__ripple = (x, y) => {
    const r = document.createElement('div');
    r.style.cssText = `position:fixed;left:${x - 16}px;top:${y - 16}px;width:32px;height:32px;border:3px solid #1b8a94;border-radius:50%;z-index:999997;pointer-events:none;transition:transform .38s ease-out,opacity .38s ease-out;transform:scale(.4);opacity:.95`;
    document.body.appendChild(r);
    requestAnimationFrame(() => { r.style.transform = 'scale(2.1)'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 450);
  };
  window.__anno = (text, pos) => {
    document.getElementById('demo-anno')?.remove();
    const d = document.createElement('div');
    d.id = 'demo-anno';
    d.style.cssText = `position:fixed;left:50%;transform:translateX(-50%);${pos === 'bottom' ? 'bottom:26px' : 'top:74px'};z-index:999999;background:rgba(13,42,53,.94);color:#fff;padding:11px 26px;border-radius:10px;font:600 22px/1.5 "Microsoft YaHei","Noto Sans CJK SC",sans-serif;box-shadow:0 6px 22px rgba(0,0,0,.42);pointer-events:none;white-space:nowrap;border:1px solid rgba(122,179,187,.5)`;
    d.textContent = text;
    document.body.appendChild(d);
  };
};

async function move(x, y) {
  const from = await page.evaluate(() => ({ x: window.__cur.x, y: window.__cur.y }));
  const dist = Math.hypot(x - from.x, y - from.y);
  const dur = Math.min(1400, Math.max(480, Math.round(dist / 0.55))); // ~0.55px/ms，适中
  await page.evaluate(([x, y, dur]) => window.__move(x, y, dur), [x, y, dur]);
  await sleep(dur + MOVE_HOLD);
}
async function ripple(x, y) { await page.evaluate(([x, y]) => window.__ripple(x, y), [x, y]); }
async function anno(text, pos = 'top', hold = OP3) {
  log('注', text);
  await page.evaluate(([t, p]) => window.__anno(t, p), [text, pos]);
  await sleep(hold);
}
async function center(locator) {
  const b = await locator.boundingBox();
  if (!b) throw new Error('no bbox');
  return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
}
async function clickEl(locator, after = OP3) {
  const c = await center(locator);
  await move(c.x, c.y);
  await ripple(c.x, c.y);
  await locator.click();
  await sleep(after);
}
async function glideOver(locators, per = 1100) {
  for (const loc of locators) { const c = await center(loc); await move(c.x, c.y); await sleep(per - MOVE_HOLD > 0 ? per - MOVE_HOLD : 0); }
}
async function smoothTo(top) {
  await page.evaluate(t => window.scrollTo({ top: t, behavior: 'smooth' }), top);
  await sleep(1000);
}
async function scrollElInto(locator) {
  const b = await locator.boundingBox();
  if (!b) return;
  const top = await page.evaluate(() => window.scrollY);
  await smoothTo(Math.max(0, top + b.y - 140));
}

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({
    viewport: { width: 1366, height: 768 },
    recordVideo: { dir: OUT_DIR, size: { width: 1366, height: 768 } },
  });
  page = await context.newPage();
  page.setDefaultTimeout(15000);
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await sleep(3000);
  await page.evaluate(DRIVER);
  T0 = Date.now();
  log('=== 开始录制流程 ===');

  /* ---------- 第一幕：分析工作台 ---------- */
  await anno('① 赛题原始数据已载入：中药一厂 · 月度成本分析工作台', 'top', OP3);
  await anno('② 选择分析条件：将产品切换为 银黄口服液', 'top', 2500);
  const productSel = page.getByRole('combobox', { name: '产品' });
  const pc = await center(productSel);
  await move(pc.x, pc.y);
  await ripple(pc.x, pc.y);
  await productSel.selectOption({ label: '银黄口服液' });
  await sleep(OP3); // 指标与告警刷新

  await anno('③ 成本看板：单位成本 / 环比 / 同比 / 预算偏差，全部为确定性计算', 'bottom', 3500);
  const cards = [
    page.getByRole('button', { name: /单位成本/ }).first(),
    page.getByRole('button', { name: /环比/ }).first(),
    page.getByRole('button', { name: /同比/ }).first(),
    page.getByRole('button', { name: /预算偏差/ }).first(),
  ];
  for (const c of cards) { const p = await center(c); await move(p.x, p.y); }

  await anno('④ 点击指标卡，可查看计算口径与数据行来源', 'top', 2500);
  await clickEl(page.getByRole('button', { name: /单位成本/ }).first(), OP3);
  await anno('⑤ 口径详情：公式、数据行与版本逐项可核对（数字可验证）', 'bottom', OP4);
  await clickEl(page.getByRole('button', { name: '关闭' }), OP2);

  await anno('⑥ 自动重点分析：成本要素环比严格超过 ±10% 自动列为重点', 'top', OP3);
  await scrollElInto(page.getByRole('heading', { name: '自动重点分析' }));
  const alertCards = page.locator('article').filter({ hasText: /环比/ });
  const n = Math.min(await alertCards.count(), 3);
  for (let i = 0; i < n; i++) { const p = await center(alertCards.nth(i)); await move(p.x, p.y); }
  await anno('⑦ 每条告警附带业务事实与核查建议，原因仍需人工核验', 'bottom', OP3);

  await scrollElInto(page.locator('.chart').first());
  await anno('⑧ 图表：近月成本趋势与结构（ECharts 渲染）', 'top', OP3);

  /* ---------- 第二幕：跨厂对标（三步法完整顺序） ---------- */
  await anno('⑨ 进入跨厂对标：中药一厂 对比 中药二厂（同产品·同规格·同期间）', 'top', OP3);
  await clickEl(page.getByRole('button', { name: '02跨厂对标' }), OP3);
  await page.locator('.table-scroll table').first().waitFor({ state: 'visible', timeout: 20000 }).catch(() => log('warn: 对标表格未及时出现'));
  await sleep(OP2);
  await anno('⑩ 三步法 · 第一步 找差异：差异总览表（差异金额与差异率）', 'bottom', OP4);
  const summaryRows = page.locator('.table-scroll tbody tr');
  const sn = Math.min(await summaryRows.count(), 3);
  for (let i = 0; i < sn; i++) { const p = await center(summaryRows.nth(i)); await move(p.x, p.y); }

  await page.evaluate(() => window.scrollBy({ top: 300, behavior: 'smooth' }));
  await sleep(1200);
  await anno('⑪ 三步法 · 第二步 拆结构：总差异按成本要素拆解，贡献度定位主因', 'top', OP4);
  const elementRows = page.locator('table').filter({ hasText: /贡献/ }).locator('tbody tr');
  const en = Math.min(await elementRows.count(), 3);
  for (let i = 0; i < en; i++) { const p = await center(elementRows.nth(i)); await move(p.x, p.y); }

  await page.evaluate(() => window.scrollBy({ top: 380, behavior: 'smooth' }));
  await sleep(1200);
  await anno('⑫ 三步法 · 第三步 拆原因：RAG 检索制药知识，大模型生成归因假设', 'bottom', OP4);
  const hyp = page.locator('.finding, blockquote').filter({ hasText: /可能|待核|证据/ }).first();
  if (await hyp.count()) { const p = await center(hyp); await move(p.x, p.y); }
  await anno('⑬ 归因均标注证据来源与适用范围；证据不足时明确说明，不编造原因', 'top', OP3);

  /* ---------- 第三幕：报告与整改闭环 ---------- */
  await anno('⑭ 生成正式报告：固定输入版本，模板渲染与逐项验收', 'top', OP3);
  await clickEl(page.getByRole('button', { name: '03报告与整改' }), OP3);
  await clickEl(page.getByRole('button', { name: '生成报告' }), OP2);
  await page.getByRole('link', { name: /Word 下载/ }).first().waitFor({ state: 'visible', timeout: 30000 }).catch(() => log('warn: 报告卡片未出现'));
  await sleep(OP3);
  await anno('⑮ 报告生成完成：六个固定章节，模型参与归因（人工评审待评）', 'bottom', OP4);
  const dlWord = page.getByRole('link', { name: /Word 下载/ }).first();
  const dlPdf = page.getByRole('link', { name: /PDF 下载/ }).first();
  if (await dlWord.count()) { const p = await center(dlWord); await move(p.x, p.y); }
  if (await dlPdf.count()) { const p = await center(dlPdf); await move(p.x, p.y); }
  await anno('⑯ 可下载 Word / PDF 报告及机器审计附件', 'top', OP3);

  await anno('⑰ 将报告建议转为整改任务：载入可执行建议', 'top', OP3);
  const loadSel = page.getByRole('combobox', { name: '载入当前报告建议' });
  const lc = await center(loadSel);
  await move(lc.x, lc.y);
  await ripple(lc.x, lc.y);
  await loadSel.selectOption({ index: 1 });
  await sleep(OP3);
  await scrollElInto(page.getByLabel('责任人'));
  await anno('⑱ 任务草稿含责任人、核查对象、预期证据与期限依据', 'bottom', OP3);
  await clickEl(page.getByRole('button', { name: '生成任务草稿' }), OP3);
  await scrollElInto(page.locator('article.task').first());
  await anno('⑲ 核对完整内容后，确认并发送模拟 RPA 通知', 'top', OP3);
  await clickEl(page.getByRole('button', { name: '确认并发送模拟通知' }), OP4);
  await page.locator('article.task .badge').filter({ hasText: '模拟通知已发送' }).first()
    .waitFor({ state: 'visible', timeout: 20000 }).catch(() => log('warn: 送达徽标未出现'));
  await sleep(OP2);
  await anno('⑳ 模拟通知已送达：模拟送达不等于整改完成', 'bottom', OP3);
  await smoothTo(0);
  await anno('㉑ 任务看板：已生成 / 已送达 / 责任人确认 分别统计', 'top', OP3);
  const tiles = page.locator('.task-summary > div');
  const tn = await tiles.count();
  for (let i = 0; i < Math.min(tn, 3); i++) { const p = await center(tiles.nth(i)); await move(p.x, p.y); }
  await anno('㉒ 全流程闭环完成：分析 → 对标 → 报告 → 整改任务 → 模拟送达', 'bottom', OP4);
  await move(700, 430);
  await sleep(1500);

  log('=== 流程结束，收尾 ===');
  await context.close();
  const path = await page.video().path();
  await browser.close();
  console.log('VIDEO_PATH=' + path);
  console.log('ELAPSED=' + ((Date.now() - T0) / 1000).toFixed(1) + 's');
})().catch(e => { console.error('FAILED:', e); process.exitCode = 1; });
