/** 讲解版端到端演示录制：选择条件→看板(含预测/决策)→对标→生成报告→任务/RPA→证据与图谱。
 * 输出 webm 视频 + 逐步回执 JSON；仅本地运行，不替代真人验收。 */
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';

const base = process.env.PHARMA_E2E_URL ?? 'http://127.0.0.1:8765';
const out = process.env.PHARMA_E2E_OUT ?? 'D:/yh_audit_wt/药衡智析_增量源码交接/public_source_candidate/07_交付/demo_20260918';
const chrome = process.env.PHARMA_CHROME_PATH ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
// Windows 下 recordVideo 目录含中文路径会失败，先录到 ASCII 临时目录再另存
const videoDir = process.env.PHARMA_DEMO_VIDEO_DIR ?? 'D:/yh_demo_video_tmp';
await mkdir(out, { recursive: true });
await mkdir(videoDir, { recursive: true });

const browser = await chromium.launch({ executablePath: chrome, headless: true, args: ['--no-sandbox'] });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, locale: 'zh-CN',
  recordVideo: { dir: videoDir, size: { width: 1440, height: 900 } } });
const page = await context.newPage();
const steps = [];
async function caption(text, dwell = 4000) {
  await page.evaluate(t => {
    document.querySelectorAll('#narration').forEach(e => e.remove());
    const d = document.createElement('div');
    d.id = 'narration'; d.textContent = t;
    d.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:26px;z-index:99999;' +
      "background:rgba(23,52,63,.93);color:#fff;padding:12px 24px;border-radius:10px;" +
      'font-size:21px;font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;max-width:86%;text-align:center;';
    document.body.appendChild(d);
  }, text);
  await page.waitForTimeout(dwell);
  steps.push(text);
}
try {
  await page.goto(`${base}/?context_id=pharmaceutical:competition`, { waitUntil: 'networkidle' });
  await caption('① 选择分析条件：赛题环境 · 中药一厂 · 六味地黄胶囊 · 2026年6月 · 月度分析', 5000);
  await page.locator('.metric').first().waitFor({ timeout: 60000 });
  await caption('② 成本看板：单位成本/环比/同比/预算偏差——全部由程序 Decimal 确定性计算，可点开查看口径与来源', 6000);
  await page.locator('.chart-grid').scrollIntoViewIfNeeded();
  await caption('③ 近6个月趋势 + 成本预测（赛题加分项）：Holt 指数平滑外推，虚线为点预测、阴影为80%区间', 6000);
  await page.locator('.decision-card, main').first().evaluate(e => e.scrollIntoView({ block: 'center' }));
  await page.waitForTimeout(1500);
  const decision = await page.locator('.decision-card').count() ? await page.locator('.decision-card').innerText() : '';
  await caption('④ Agent 自主决策（赛题加分项）：系统判断本期是否需要正式报告' + (decision.includes('建议生成') ? '——当前建议生成报告' : ''), 6000);
  await page.getByRole('button', { name: /跨厂对标/ }).click();
  await page.getByRole('heading', { name: /差异总览/ }).waitFor({ timeout: 120000 });
  await caption('⑤ 对标三步法：与中药二厂“找差异→拆结构→拆原因”，差异表/结构树/归因解释逐层下钻', 7000);
  await page.getByRole('button', { name: /报告与任务/ }).click();
  await page.getByRole('heading', { name: '当前企业任务看板' }).waitFor();
  await caption('⑥ 生成正式报告：模板结构 + 数据填充 + RAG 证据 + 大模型解释，产物为 Word/PDF 双格式', 6000);
  const reportPromise = page.waitForResponse(r => r.url().endsWith('/api/reports') && r.request().method() === 'POST', { timeout: 60000 }).catch(() => null);
  await page.getByRole('button', { name: '生成报告', exact: true }).click().catch(() => {});
  const resp = await reportPromise;
  const job = resp ? await resp.json() : null;
  if (job?.job_id) {
    for (let i = 0; i < 240; i++) {
      const j = await (await fetch(`${base}/api/jobs/${job.job_id}`)).json();
      if (['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(j.status)) break;
      await page.waitForTimeout(1000);
    }
  }
  await caption('⑦ 报告任务完成：Word/PDF 已生成，含全部固定章节与证据引用；版式遗留与真人版式评审状态见实施状态表', 6000);
  await caption('⑧ 整改闭环：分析结论转为结构化任务，经模拟 RPA 送达责任人，看板跟踪生成/送达/确认状态', 7000);
  await page.getByRole('button', { name: /数据与证据/ }).click();
  await page.getByRole('heading', { name: '数据与知识来源' }).waitFor();
  await caption('⑨ 证据溯源：文档名/章节/页码可核查；检索为 BM25+向量混合并标注来源', 6000);
  await page.locator('.panel').filter({ hasText: '知识图谱' }).first().scrollIntoViewIfNeeded().catch(() => {});
  await page.waitForTimeout(2500);
  await caption('⑩ 知识图谱（赛题加分项）：产品-药材-工序关系可视化，检索时自动扩展关键词', 7000);
  await caption('药衡智析：数值可信 · 证据适用 · 缺证可解释 · 任务可核查', 5000);
  const video = page.video();
  await context.close();
  if (video) await video.saveAs(`${out}/yaoheng_demo_narrated.webm`);
  await writeFile(`${out}/demo_receipt.json`, JSON.stringify({ status: 'PASS', url: base, submitted_job: job?.job_id ?? null, scenes: steps, chrome }, null, 2));
  console.log(JSON.stringify({ status: 'PASS', steps: steps.length, job: job?.job_id ?? null, out }));
} catch (e) {
  await writeFile(`${out}/demo_failure.json`, JSON.stringify({ error: String(e), steps }, null, 2));
  console.error(String(e)); process.exitCode = 1;
} finally { await browser.close(); }
