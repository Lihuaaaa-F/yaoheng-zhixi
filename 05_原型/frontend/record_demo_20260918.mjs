/** Real local simulation: filters → report → verified downloads → draft → UI confirmation → receipt.
 * Reuse an existing job with PHARMA_DEMO_JOB_ID; its run_id and selection must match.
 * Browser plugin not available; reuse the project's installed Playwright/Chromium. */
import {chromium} from 'playwright';
import {mkdir, mkdtemp, readFile, writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';

export function requireLoopback(value) {
  const url = new URL(value), host = url.hostname.replace(/^\[|\]$/g, '');
  const ipv4 = host.split('.');
  const local = host === 'localhost' || host === '::1' ||
    (ipv4.length === 4 && ipv4[0] === '127' && ipv4.every(p => /^\d+$/.test(p) && Number(p) <= 255));
  if (!['http:', 'https:'].includes(url.protocol) || !local || url.username || url.password)
    throw Error('LOCAL_LOOPBACK_REQUIRED');
  return url;
}
export function validateHealth(health) {
  if (health.simulation !== true || health.rpa_mode !== 'local_simulator') throw Error('LOCAL_SIMULATION_REQUIRED');
  requireLoopback(health.rpa_base_url);
  return health;
}
export function validateJob(job, runId, selection) {
  if (!['SUCCEEDED', 'DEGRADED'].includes(job.status)) throw Error('REPORT_NOT_COMPLETE');
  if (job.input?.run_id !== runId) throw Error('REPORT_RUN_MISMATCH');
  for (const [key, value] of Object.entries(selection)) if (job.input?.[key] !== value) throw Error(`REPORT_SELECTION_MISMATCH:${key}`);
  for (const kind of ['docx', 'pdf']) {
    const artifact = job.result?.[kind];
    if (artifact?.status !== 'PASS' || !artifact.artifact_id || !/^[a-f0-9]{64}$/.test(artifact.sha256 ?? ''))
      throw Error(`REPORT_ARTIFACT_MISSING:${kind}`);
  }
  return job;
}
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export async function recordDemo() {
  const base = requireLoopback(process.env.PHARMA_E2E_URL ?? 'http://127.0.0.1:8765').origin;
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const runId = process.env.PHARMA_DEMO_RUN_ID;
  if (!runId) throw Error('PHARMA_DEMO_RUN_ID_REQUIRED');
  const scenario = process.env.PHARMA_DEMO_SCENARIO ?? 'S1';
  const attempt = process.env.PHARMA_DEMO_ATTEMPT_ID ?? `demo-${stamp}`;
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
  const out = process.env.PHARMA_E2E_OUT ?? path.join(root, '07_交付', `demo_${stamp}`);
  await mkdir(path.dirname(out), {recursive: true});
  await mkdir(out); // Existing runs are immutable, including failed runs.
  const receipt = {status: 'RUNNING', run_id: runId, attempt_id: attempt, scenario, base_url: base,
    viewport: {width: 1366, height: 768}, simulation: true, human_review: 'PENDING',
    browser: 'Browser plugin not available; installed Playwright/Chromium', scenes: [], artifacts: {}, errors: []};
  receipt.recorder_source_sha256 = sha(await readFile(fileURLToPath(import.meta.url)));
  let browser, context, page, video, timer;
  const request = async (url, options = {}) => {
    const target = new URL(url, base);
    if (requireLoopback(target.href).origin !== base) throw Error('CROSS_ORIGIN_REQUEST_BLOCKED');
    const response = await fetch(target, {...options, redirect: 'error', signal: AbortSignal.timeout(30000)});
    if (!response.ok) throw Error(`HTTP_${response.status}:${target.pathname}`);
    return response.json();
  };
  try {
    receipt.health = validateHealth(await request('/health'));
    let job = process.env.PHARMA_DEMO_JOB_ID ? await request(`/api/jobs/${encodeURIComponent(process.env.PHARMA_DEMO_JOB_ID)}`) : null;
    const source = job?.input ?? {};
    const selection = {
      context_id: process.env.PHARMA_DEMO_CONTEXT_ID ?? source.context_id ?? 'pharmaceutical:competition',
      factory: process.env.PHARMA_DEMO_FACTORY ?? source.factory ?? '中药一厂',
      product: process.env.PHARMA_DEMO_PRODUCT ?? source.product ?? '六味地黄胶囊',
      month: process.env.PHARMA_DEMO_MONTH ?? source.month ?? '2026-06',
      analysis_type: process.env.PHARMA_DEMO_ANALYSIS_TYPE ?? source.analysis_type ?? 'monthly',
      basis: process.env.PHARMA_DEMO_BASIS ?? source.basis ?? 'unit',
    };
    if (job) validateJob(job, runId, selection);
    receipt.selection = selection;
    receipt.reused_job = job?.id ?? null;
    if (process.env.PHARMA_DEMO_MANIFEST) {
      const bytes = await readFile(process.env.PHARMA_DEMO_MANIFEST), manifest = JSON.parse(bytes);
      const sourceScenario = manifest.scenarios?.find(row => row.id === scenario);
      if (manifest.run_id !== runId || !sourceScenario || (job && sourceScenario.job_id !== job.id))
        throw Error('SOURCE_MANIFEST_BINDING_MISMATCH');
      receipt.source_manifest = {sha256: sha(bytes), run_id: runId, scenario,
        attempt_id: sourceScenario.attempt_id, job_id: sourceScenario.job_id, revision: manifest.revision};
    }
    const temp = await mkdtemp(path.join(tmpdir(), 'yaoheng-video-'));
    browser = await chromium.launch({executablePath: process.env.PHARMA_CHROME_PATH, headless: true, args: ['--no-sandbox']});
    context = await browser.newContext({viewport: receipt.viewport, locale: 'zh-CN', acceptDownloads: true,
      recordVideo: {dir: temp, size: receipt.viewport}, serviceWorkers: 'block'});
    // Browser requests cannot redirect externally, including POSTs initiated by the UI.
    await context.route('**/*', async route => {
      try {
        const req = route.request(), url = requireLoopback(req.url());
        if (url.origin !== base) throw Error('EXTERNAL_BROWSER_REQUEST_BLOCKED');
        if (url.pathname.endsWith('/acknowledge')) throw Error('HUMAN_ACKNOWLEDGEMENT_PROHIBITED');
        const options = {maxRedirects: 0, timeout: 60000};
        if (url.pathname === '/api/reports' && req.method() === 'POST')
          options.postData = JSON.stringify({...req.postDataJSON(), run_id: runId});
        const response = await route.fetch(options);
        if (response.status() >= 300 && response.status() < 400) throw Error('BROWSER_REDIRECT_BLOCKED');
        await route.fulfill({response});
      } catch (error) {
        // Abort and retain the error; never turn a failed click/request into a PASS.
        receipt.errors.push(String(error));
        await route.abort();
      }
    });
    page = await context.newPage(); video = page.video();
    page.setDefaultTimeout(20000);
    page.on('pageerror', error => receipt.errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') receipt.errors.push(message.text()); });
    const caption = async text => {
      await page.evaluate(text => {
        let node = document.querySelector('#demo-caption');
        if (!node) { node = document.createElement('div'); node.id = 'demo-caption'; document.body.appendChild(node); }
        node.textContent = `本地模拟演示 · 非真人确认｜${text}`;
        node.style.cssText = 'position:fixed;bottom:12px;left:230px;right:18px;padding:10px 16px;background:#143d43ed;color:white;border-radius:8px;z-index:99999;font:17px "Noto Sans CJK SC",sans-serif;pointer-events:none';
      }, text);
      receipt.scenes.push({text, at: new Date().toISOString()});
      await page.waitForTimeout(5500);
    };
    const clickResponse = async (locator, endpoint, method = 'POST') => {
      const [response] = await Promise.all([
        page.waitForResponse(r => new URL(r.url()).pathname === endpoint && r.request().method() === method), locator.click()]);
      if (!response.ok()) throw Error(`UI_HTTP_${response.status()}:${endpoint}`);
      return response.json();
    };
    const workflow = async () => {
      await page.goto(`${base}/?context_id=${encodeURIComponent(selection.context_id)}`, {waitUntil: 'domcontentloaded'});
      await page.locator('.metric').first().waitFor();
      await caption('选择分析条件，观察真实数据随筛选更新');
      for (const [label, key] of [['产品', 'product'], ['工厂', 'factory'], ['报告范围', 'analysis_type'], ['月份', 'month']])
        await page.getByLabel(label, {exact: true}).selectOption(selection[key]);
      // Exercise a real change and then return to the recorded cost basis.
      await page.getByRole('group', {name: '成本口径'}).getByRole('button', {name: selection.basis === 'unit' ? '总额' : '单位', exact: true}).click();
      await page.locator('.metric').first().waitFor();
      await page.getByRole('group', {name: '成本口径'}).getByRole('button', {name: selection.basis === 'unit' ? '单位' : '总额', exact: true}).click();
      await page.locator('.metric').first().waitFor();
      await page.locator('.metric').first().evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption('程序计算成本与差异；缺失数据和解释能力分别说明');
      await page.screenshot({path: path.join(out, 'analysis_1366x768.png')});
      await page.locator('.chart-grid').first().evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption('趋势、结构与差异图联动当前筛选；预测仍是实验性原型');
      await page.screenshot({path: path.join(out, 'charts_1366x768.png')});
      await page.getByRole('button', {name: /报告与任务/}).click();
      await page.getByRole('heading', {name: '报告生成与下载'}).waitFor();
      await page.getByRole('heading', {name: '报告生成与下载'}).evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption(job ? '复用本次运行已验证报告，实际下载 Word 与 PDF' : '提交本次运行报告并等待实际文件生成');
      const submitted = await clickResponse(page.getByRole('button', {name: '生成报告', exact: true}), '/api/reports');
      if (job && submitted.job_id !== job.id) throw Error('EXPECTED_CACHE_REUSE_MISSED');
      receipt.job_id = submitted.job_id;
      for (;;) {
        job = await request(`/api/jobs/${encodeURIComponent(submitted.job_id)}`);
        if (['SUCCEEDED', 'DEGRADED', 'FAILED'].includes(job.status)) break;
        await page.waitForTimeout(1000);
      }
      validateJob(job, runId, selection);
      receipt.tested_code = {revision: job.input.revision, commit: job.input.commit, revision_kind: job.input.revision_kind};
      receipt.snapshot_id = job.input.snapshot_id;
      receipt.job_status = job.status;
      receipt.model_identity = job.result.narrative?.model_identity;
      for (const kind of ['docx', 'pdf']) {
        const artifact = job.result[kind];
        const link = page.locator(`a[href="/api/artifacts/${artifact.artifact_id}"]`).first();
        await link.waitFor();
        await link.scrollIntoViewIfNeeded();
        await caption(`实际下载 ${kind === 'docx' ? 'Word' : 'PDF'}，文件与本次报告绑定`);
        const [download] = await Promise.all([page.waitForEvent('download'), link.click()]);
        if (await download.failure()) throw Error(`DOWNLOAD_FAILED:${kind}`);
        const filename = `report.${kind}`, target = path.join(out, filename);
        await download.saveAs(target);
        const actual = sha(await readFile(target));
        if (actual !== artifact.sha256) throw Error(`ARTIFACT_HASH_MISMATCH:${kind}`);
        receipt.artifacts[kind] = {artifact_id: artifact.artifact_id, sha256: actual, path: filename};
      }
      await caption('报告文件已实际下载并核对；专业原因、可读性与版式仍待真人评审');
      await page.getByLabel('载入当前报告建议').selectOption('0');
      await page.getByLabel('载入当前报告建议').evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption('载入当前报告的可执行建议，展示核查对象、预期证据与责任角色');
      const selectedSuggestion = await page.getByLabel('建议内容', {exact: true}).inputValue();
      const clean = value => String(value ?? '').replace(/\\r\\n|\\n|\\r/g, '\n').replace(/\\t/g, ' ').trim();
      const sourceFinding = (job.result.narrative?.findings ?? []).find(f =>
        clean(f.suggestion) === selectedSuggestion && clean(f.rendered_text ?? f.text_template));
      if (!sourceFinding) throw Error('DRAFT_SUGGESTION_REPORT_MISMATCH');
      receipt.source_finding = {job_id: job.id, suggestion: sourceFinding.suggestion,
        metric_refs: sourceFinding.metric_refs, evidence_refs: sourceFinding.evidence_refs};
      // A unique, visibly synthetic recipient gives this recording its own draft.
      await page.getByLabel('责任人', {exact: true}).fill(`模拟演示-${attempt.slice(-18)}`);
      const draft = await clickResponse(page.getByRole('button', {name: '生成任务草稿', exact: true}), '/api/actions');
      if (draft.status !== 'DRAFT' || draft.metadata?.snapshot_id !== receipt.snapshot_id) throw Error('NEW_BOUND_DRAFT_REQUIRED');
      receipt.action = {task_id: draft.id, payload_hash: draft.payload_hash, payload: draft.payload, metadata: draft.metadata};
      const task = page.locator(`[data-task-id="${draft.id}"]`);
      await task.evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption('从报告建议创建草稿，核对责任角色、核查对象与期限；下面执行模拟发送确认');
      validateHealth(await request('/health')); // Preflight immediately before confirmation.
      await clickResponse(task.getByRole('button', {name: '确认并发送模拟通知', exact: true}), `/api/actions/${draft.id}/confirm`);
      receipt.confirmation = {actor: 'automated_local_simulation', payload_hash: draft.payload_hash, at: new Date().toISOString(), human_acknowledgement: false};
      let action;
      for (;;) {
        action = await request(`/api/actions/${draft.id}`);
        if (action.delivery?.notification === 'SIMULATED_SENT') break;
        if (['FAILED', 'CONFLICT', 'DELIVERY_UNKNOWN'].includes(action.status)) throw Error(`SIMULATED_DELIVERY_${action.status}`);
        await page.waitForTimeout(1000);
      }
      const queried = await clickResponse(task.getByRole('button', {name: '查询模拟通知状态', exact: true}), `/api/actions/${draft.id}/refresh`);
      if (queried.delivery?.notification !== 'SIMULATED_SENT' || queried.payload_hash !== draft.payload_hash || queried.responsibility_confirmation)
        throw Error('BOUND_SIMULATION_RECEIPT_REQUIRED');
      receipt.delivery = queried;
      await task.evaluate(node => node.scrollIntoView({block: 'start'}));
      await caption('本地模拟 RPA 已记录通知送达；责任人确认和真实整改由真人另行完成');
      await page.screenshot({path: path.join(out, 'simulated_delivery_1366x768.png')});
      if (receipt.errors.length) throw Error('BROWSER_REQUEST_OR_RUNTIME_FAILED');
    };
    await Promise.race([workflow(), new Promise((_, reject) => {timer = setTimeout(() => reject(Error('DEMO_240_SECONDS_TIMEOUT')), 240000);})]);
    clearTimeout(timer);
    await context.close(); context = null;
    const videoPath = path.join(out, 'yaoheng_demo_narrated.webm');
    await video.saveAs(videoPath);
    const {stdout} = await promisify(execFile)('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', videoPath]);
    const duration = Number(stdout.trim());
    if (!(duration > 0 && duration <= 300)) throw Error('VIDEO_DURATION_OUT_OF_RANGE');
    receipt.video = {path: path.basename(videoPath), duration_seconds: duration, sha256: sha(await readFile(videoPath))};
    receipt.status = 'PASS';
  } catch (error) {
    receipt.status = 'FAIL'; receipt.errors.push(String(error)); process.exitCode = 1;
  } finally {
    clearTimeout(timer);
    for (const resource of [context, browser]) if (resource) {
      try { await resource.close(); }
      catch (error) { receipt.status = 'FAIL'; receipt.errors.push(`CLEANUP:${String(error)}`); process.exitCode = 1; }
    }
    receipt.finished_at = new Date().toISOString();
    await writeFile(path.join(out, 'demo_receipt.json'), JSON.stringify(receipt, null, 2));
  }
  console.log(JSON.stringify({status: receipt.status, run_id: runId, job_id: receipt.job_id, out}));
  return receipt;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  recordDemo().catch(error => {console.error(String(error)); process.exitCode = 1;});
}
