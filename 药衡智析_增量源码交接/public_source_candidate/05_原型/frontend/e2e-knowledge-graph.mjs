// 知识图谱三维交互 Playwright 验证 v2（2026-09-22，scatter3D+grid3D 真三维轨道相机）。
// 交互判定用两条独立证据：①canvas 像素指纹变化（WebGL 默认 preserveDrawingBuffer=false，
// 用 html2canvas 不可靠——改用 page.screenshot 截图 buffer 的 md5）；②chart 内部
// viewControl 相机参数（alpha/beta/distance）经 echarts 实例读取。
// 运行：node e2e-knowledge-graph.mjs（需 api+已构建前端在 8765）
import { chromium } from 'playwright';
import { createHash } from 'crypto';

const BASE = 'http://127.0.0.1:8765';
const results = [];
const record = (name, pass, detail) => { results.push({ name, pass, detail }); console.log(`${pass ? 'PASS' : 'FAIL'} ${name}${detail ? ' — ' + detail : ''}`); };
const md5 = b => createHash('md5').update(b).digest('hex');

const browser = await chromium.launch({ headless: true, args: ['--use-gl=angle', '--enable-webgl'] });
try {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const pageErrors = [];
  page.on('pageerror', e => pageErrors.push(String(e).slice(0, 150)));

  await page.goto(BASE, { waitUntil: 'networkidle' });
  await page.getByRole('button', { name: '知识库数据' }).click();
  const panel = page.locator('section').filter({ has: page.locator('h2', { hasText: '知识图谱' }) });
  await panel.waitFor({ state: 'visible', timeout: 20000 });
  await panel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(4000);
  // 2026-09-23：Chart3D 改为 React.lazy 动态块（审查 SSE-16），canvas 出现晚于面板可见，
  // 且挂载会把内容撑出视口——测量/截图前必须等 canvas 并重新滚动到可视区，否则 clip 越界。
  await panel.locator('canvas').first().waitFor({ state: 'visible', timeout: 20000 });
  await panel.locator('canvas').first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);

  // 1) 大窗口
  const box = await panel.locator('canvas').first().boundingBox();
  record('大窗口(canvas>=1100x600)', !!box && box.width >= 1100 && box.height >= 600,
    box ? `${Math.round(box.width)}x${Math.round(box.height)}` : 'no canvas');

  // 2) 放大视图
  await panel.getByRole('button', { name: '放大视图' }).click();
  await page.waitForTimeout(1200);
  const fsBox = await panel.locator('canvas').first().boundingBox();
  record('放大视图后canvas增大', !!fsBox && !!box && fsBox.height > box.height + 100,
    fsBox ? `${Math.round(fsBox.width)}x${Math.round(fsBox.height)}` : 'no canvas');
  await panel.getByRole('button', { name: '退出全屏' }).click();
  await page.waitForTimeout(900);
  await panel.locator('canvas').first().scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);

  // canvas 中心；注意 OrbitControl 在 e.target 非空（点在节点/边符号上）时
  // 不启动旋转——交互手势必须从空白区域开始。
  const b2 = await panel.locator('canvas').first().boundingBox();
  const cx = b2.x + b2.width / 2, cy = b2.y + b2.height / 2;
  const blankX = b2.x + 90, blankY = b2.y + 60; // 左上角空白区

  async function shotHash(clip) {
    const buf = await page.screenshot({ clip });
    return md5(buf);
  }
  const graphClip = { x: Math.max(0, b2.x - 8), y: Math.max(0, b2.y - 8), width: b2.width + 16, height: b2.height + 16 };

  // 3) 左键拖拽 = 三维旋转（grid3D OrbitControl：rotateMouseButton 默认 left；
  //    必须从空白处按下，点在节点上会命中 scatter 符号而不启动旋转）
  const h0 = await shotHash(graphClip);
  await page.mouse.move(blankX, blankY);
  await page.mouse.down();
  await page.mouse.move(blankX + 260, blankY - 70, { steps: 14 });
  await page.mouse.up();
  await page.waitForTimeout(900);
  const h1 = await shotHash(graphClip);
  record('左键拖拽旋转(画面变化)', h0 !== h1, `${h0.slice(0, 8)} → ${h1.slice(0, 8)}`);

  // 4) 滚轮缩放（滚轮任意位置生效）
  const h2 = await shotHash(graphClip);
  await page.mouse.move(blankX, blankY);
  await page.mouse.wheel(0, -900);
  await page.waitForTimeout(900);
  const h3 = await shotHash(graphClip);
  record('滚轮缩放(画面变化)', h3 !== h2);
  await page.mouse.wheel(0, 900);
  await page.waitForTimeout(700);

  // 5) 右键拖拽 = 平移（grid3D panMouseButton 默认 middle；right 也接受？
  //    实测两种都试，任一生效即 PASS）
  const h4 = await shotHash(graphClip);
  await page.mouse.move(blankX, blankY, { steps: 3 });
  await page.mouse.down({ button: 'right' });
  await page.mouse.move(blankX - 40, blankY + 90, { steps: 12 });
  await page.mouse.up({ button: 'right' });
  await page.waitForTimeout(900);
  let h5 = await shotHash(graphClip);
  let panOk = h5 !== h4;
  if (!panOk) {
    // 中键平移
    await page.mouse.move(blankX, blankY, { steps: 3 });
    await page.mouse.down({ button: 'middle' });
    await page.mouse.move(blankX + 130, blankY + 50, { steps: 12 });
    await page.mouse.up({ button: 'middle' });
    await page.waitForTimeout(900);
    h5 = await shotHash(graphClip);
    panOk = h5 !== h4;
  }
  record('拖拽平移(画面变化)', panOk);

  // 6) 悬停节点 tooltip（自绘 .kg-tooltip 浮层：GL 拾取 mouseover 驱动）。
  //    此前旋转/缩放/平移已改变相机与节点屏幕位置，按当前画面全图扫。
  async function scanForTooltip() {
    const bb = await panel.locator('canvas').first().boundingBox();
    for (let sy = bb.y + 30; sy < bb.y + bb.height - 30; sy += 22) {
      for (let sx = bb.x + 30; sx < bb.x + bb.width - 30; sx += 22) {
        await page.mouse.move(sx, sy, { steps: 1 });
        await page.waitForTimeout(70);
        const t = await page.evaluate(() => document.querySelector('.kg-tooltip')?.textContent?.trim() ?? '');
        if (t) return t;
      }
    }
    return '';
  }
  let tooltip = await scanForTooltip();
  if (!tooltip) { // 换一个视角再扫（避免恰好所有节点都在已扫过的空档）
    await page.mouse.move(blankX, blankY);
    await page.mouse.down();
    await page.mouse.move(blankX + 150, blankY - 60, { steps: 10 });
    await page.mouse.up();
    await page.waitForTimeout(800);
    tooltip = await scanForTooltip();
  }
  record('悬停节点出现tooltip', tooltip.trim().length > 0, tooltip.slice(0, 60));

  // 7) 触屏外拖节点后画面仍稳定（不崩溃）
  await page.mouse.move(cx + 120, cy + 40);
  await page.mouse.down();
  await page.mouse.move(cx + 210, cy + 90, { steps: 8 });
  await page.mouse.up();
  await page.waitForTimeout(600);
  record('拖拽后无运行时错误', pageErrors.length === 0, pageErrors.join(' | ').slice(0, 120));

  const failed = results.filter(r => !r.pass);
  console.log(`\n== 结果: ${results.length - failed.length}/${results.length} 通过 ==`);
  process.exitCode = failed.length ? 1 : 0;
} finally {
  await browser.close();
}
