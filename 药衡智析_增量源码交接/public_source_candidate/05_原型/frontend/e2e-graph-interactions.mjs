/** Read-only graph regression: real canvas gestures, camera projection and
 * scroll ownership. No report generation, provider calls or data mutations.
 * PHARMA_E2E_URL points to an already running local app. Browser assets are reused.
 */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
assert.ok(process.env.PHARMA_E2E_URL, '请设置 PHARMA_E2E_URL');
const url = new URL(process.env.PHARMA_E2E_URL);
url.searchParams.set('page', 'knowledge'); url.searchParams.set('graph', '1');
const out = process.env.PHARMA_E2E_OUT ?? path.join(os.tmpdir(), 'yaoheng-graph-qa');
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.PHARMA_CHROME_PATH, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, locale: 'zh-CN' });
const errors = [], checks = [], measurements = {};
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
const chart = page.getByRole('img', { name: '知识图谱三维视图' });
const camera = () => page.evaluate(() => [...window.__chart3d.values()][0].getOption().grid3D[0].viewControl);
const scroll = () => page.locator('.workspace-scroll').evaluate(el => el.scrollTop);
const reset = async () => { await page.getByRole('button', { name: '重置图谱视角' }).click(); await chart.scrollIntoViewIfNeeded(); await page.waitForTimeout(350); };
const project = () => page.evaluate(() => {
  const c = [...window.__chart3d.values()][0], series = c.getModel().getSeriesByIndex(1), coord = series.coordinateSystem, camera = coord.viewGL.camera;
  const mul = (m, v) => [0, 1, 2, 3].map(i => m[i] * v[0] + m[4 + i] * v[1] + m[8 + i] * v[2] + m[12 + i] * v[3]);
  const option = c.getOption();
  return { width: c.getWidth(), height: c.getHeight(), edgePoints: option.series[0].data.length, nodes: option.series[1].data.map(n => {
    const world = coord.dataToPoint(n.value), clip = mul(camera.projectionMatrix.array, mul(camera.viewMatrix.array, [...world, 1]));
    return { name: n.name, type: n.tooltip_kind, value: n.value, world, x: (clip[0] / clip[3] + 1) * c.getWidth() / 2, y: (1 - clip[1] / clip[3]) * c.getHeight() / 2 };
  }) };
});
const drag = async (dx, dy, button = 'left', position = null) => {
  const box = await chart.boundingBox();
  const x = box.x + (position?.x ?? box.width / 2), y = box.y + (position?.y ?? box.height / 2);
  await page.mouse.move(x, y); await page.mouse.down({ button });
  await page.mouse.move(x + dx, y + dy, { steps: 10 }); await page.mouse.up({ button }); await page.waitForTimeout(500);
};
try {
  const graphResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/api/kb/graph' && r.status() === 200);
  await page.goto(url.href); const graph = await (await graphResponse).json();
  await chart.waitFor(); await chart.scrollIntoViewIfNeeded(); await page.waitForTimeout(600);
  assert.match(await page.title(), /药衡智析/); assert.equal(new URL(page.url()).searchParams.get('page'), 'knowledge');
  assert.equal(await page.locator('vite-error-overlay').count(), 0);
  checks.push('页面身份、有效内容与无错误覆盖层');
  const initial = await camera(), initialProjection = await project();
  assert.equal(initialProjection.nodes.length, graph.nodes.length);
  assert.equal(initialProjection.edgePoints, graph.edges.length * 41);
  const spans = [0, 1, 2].map(axis => Math.max(...initialProjection.nodes.map(n => n.world[axis])) - Math.min(...initialProjection.nodes.map(n => n.world[axis])));
  assert.ok(spans[2] / spans[0] > .35, '渲染后的图谱必须保留真实纵深');
  for (const [left, right] of [['原料', '产品'], ['产品', '工序']]) {
    const xs = type => initialProjection.nodes.filter(n => n.type === type).map(n => n.value[0]);
    assert.ok(Math.max(...xs(left)) < Math.min(...xs(right)), '同类节点仍须集中且分区');
  }
  measurements.geometry = { nodes: graph.nodes.length, edges: graph.edges.length, worldSpans: spans };
  checks.push('真实节点与关系完整、类型分区及三维纵深');
  const rotation = [];
  for (const [dx, dy] of [[40, 0], [0, 40], [0, -40]]) {
    await reset(); await drag(dx, dy); const c = await camera(); rotation.push({ alpha: c.alpha - initial.alpha, beta: c.beta - initial.beta });
  }
  const horizontal = Math.abs(rotation[0].beta);
  assert.ok(horizontal > 25, '旋转应对短距离拖拽及时响应');
  for (const c of rotation.slice(1)) assert.ok(Math.abs(c.alpha) / horizontal > .8 && Math.abs(c.alpha) / horizontal < 1.2, '横纵同像素拖动应基本等速');
  measurements.rotation40px = rotation; checks.push('左键横纵等速旋转');
  await reset();
  const node = (await project()).nodes.find(n => n.type === '产品');
  await drag(40, 0, 'left', node);
  assert.ok(Math.abs((await camera()).beta - initial.beta) > 25, '从节点上按下也应能旋转');
  const afterNodeDrag = await camera();
  const hoverNode = (await project()).nodes.find(n => n.type === '产品'), hoverBox = await chart.boundingBox();
  await page.mouse.move(hoverBox.x + hoverNode.x, hoverBox.y + hoverNode.y); await page.waitForTimeout(450);
  assert.ok(Math.abs((await camera()).beta - afterNodeDrag.beta) < 1, '悬停不应重置相机');
  checks.push('节点上起拖及悬停保持视角');
  // A middle-button drag should move the scene with the cursor, without runaway scaling.
  await reset(); const panBefore = await project(); await drag(45, 0, 'middle'); const panAfter = await project();
  const shift = panAfter.nodes[0].x - panBefore.nodes[0].x;
  assert.ok(shift > 25 && shift < 70, '平移距离应接近鼠标位移');
  measurements.pan45px = shift; checks.push('中键平移跟随鼠标');
  await reset(); const box = await chart.boundingBox(), startScroll = await scroll();
  await page.evaluate(() => { window.__middleDefaults = []; document.addEventListener('mousedown', e => { if (e.button === 1) window.__middleDefaults.push(e.defaultPrevented); }); });
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2); await page.mouse.down({ button: 'middle' });
  await page.mouse.move(box.x + box.width / 2, box.y - 35, { steps: 10 });
  await page.mouse.wheel(0, 180); await page.waitForTimeout(200);
  assert.equal(await scroll(), startScroll, '拖出画布后也不能带动页面滚动');
  assert.ok(await page.evaluate(() => window.__middleDefaults.some(Boolean)), '必须阻止中键原生自动滚动');
  await page.mouse.up({ button: 'middle' }); await page.waitForTimeout(150);
  const released = await camera(); await page.mouse.move(box.x + box.width / 2 + 35, box.y - 30); await page.waitForTimeout(200);
  assert.deepEqual((await camera()).center, released.center, '出界松开后必须停止平移');
  await page.mouse.wheel(0, -150); await page.waitForTimeout(250);
  assert.ok(Math.abs((await scroll()) - startScroll) > 30, '松开后应恢复页面滚动');
  measurements.outsideDragPageScroll = 0; checks.push('中键默认行为、出界拖拽、出界松开及页面滚动恢复');
  // Interruptions must release ownership and leave neither orbit nor page scroll stuck.
  for (const interruption of ['blur', 'pointercancel', 'Escape']) {
    await reset(); const b = await chart.boundingBox();
    await page.mouse.move(b.x + b.width / 2, b.y + b.height / 2); await page.mouse.down({ button: 'middle' });
    if (interruption === 'Escape') await page.keyboard.press('Escape');
    else await page.evaluate(kind => {
      if (kind === 'blur') window.dispatchEvent(new Event('blur'));
      else document.dispatchEvent(new PointerEvent('pointercancel', { pointerId: 1, bubbles: true }));
    }, interruption);
    const stopped = await camera();
    await page.mouse.move(b.x + b.width / 2 + 30, b.y - 30, { steps: 4 }); await page.waitForTimeout(150);
    assert.deepEqual((await camera()).center, stopped.center, `${interruption}必须结束拖拽`);
    await page.mouse.up({ button: 'middle' }); const before = await scroll();
    await page.mouse.wheel(0, -80); await page.waitForTimeout(200); assert.notEqual(await scroll(), before);
  }
  checks.push('失焦、取消和Escape中断后的交互恢复');
  await reset(); const zoomBox = await chart.boundingBox(), scrollBeforeZoom = await scroll();
  await page.mouse.move(zoomBox.x + zoomBox.width / 2, zoomBox.y + zoomBox.height / 2);
  const zoomBefore = await camera(); await page.mouse.wheel(0, -120); await page.waitForTimeout(500); const zoomIn = await camera();
  assert.ok(zoomIn.distance < zoomBefore.distance - 5); assert.equal(await scroll(), scrollBeforeZoom);
  await page.mouse.wheel(0, 120); await page.waitForTimeout(500); assert.ok((await camera()).distance > zoomIn.distance + 5);
  checks.push('滚轮缩放且不滚动页面');
  await reset(); await drag(35, 20); const beforeFullscreen = await camera();
  await page.getByRole('button', { name: '全屏', exact: true }).click(); await page.waitForFunction(() => !!document.fullscreenElement); await page.waitForTimeout(500);
  assert.ok(Math.abs((await camera()).beta - beforeFullscreen.beta) < 1, '进入全屏保留已旋转视角');
  const fullBefore = await camera(); await drag(25, 0); assert.ok(Math.abs((await camera()).beta - fullBefore.beta) > 15);
  const fullAfter = await camera(); await page.getByRole('button', { name: '退出全屏', exact: true }).click(); await page.waitForFunction(() => !document.fullscreenElement); await page.waitForTimeout(500);
  assert.ok(Math.abs((await camera()).beta - fullAfter.beta) < 1, '退出全屏保留视角');
  checks.push('全屏、退出全屏保留视角且旋转正常');
  await chart.dblclick(); await page.waitForFunction(() => !!document.fullscreenElement);
  await chart.dblclick(); await page.waitForFunction(() => !document.fullscreenElement);
  checks.push('双击进入和退出全屏');
  await reset(); assert.ok(Math.abs((await camera()).beta - initial.beta) < .01); assert.deepEqual((await camera()).center, [0, 0, 0]);
  await page.locator('.kg-disclosure').screenshot({ path: path.join(out, '桌面图谱.png') });
  await drag(35, 15); await page.locator('.kg-disclosure').screenshot({ path: path.join(out, '旋转后的图谱.png') });
  await page.setViewportSize({ width: 390, height: 844 }); await reset();
  const mobile = await project();
  for (const n of mobile.nodes) assert.ok(n.x > 8 && n.x < mobile.width - 8 && n.y > 10 && n.y < mobile.height - 10, `手机画布应容纳节点：${n.name}`);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true);
  await page.locator('.kg-disclosure').screenshot({ path: path.join(out, '手机图谱.png') });
  // Tap a mobile node: small-screen hidden labels remain discoverable.
  const mobileNode = mobile.nodes.find(n => n.type === '原料'), mobileBox = await chart.boundingBox();
  await page.mouse.click(mobileBox.x + mobileNode.x, mobileBox.y + mobileNode.y); await page.waitForTimeout(150);
  assert.ok((await page.locator('.kg-tooltip').innerText()).includes(mobileNode.name));
  checks.push('重置、手机视口可见性及节点点击详情');
  // Unmount during an active drag: document-level scroll guards must be removed.
  await page.setViewportSize({ width: 1440, height: 1000 }); await reset(); const finalBox = await chart.boundingBox();
  await page.mouse.move(finalBox.x + finalBox.width / 2, finalBox.y + finalBox.height / 2); await page.mouse.down({ button: 'middle' });
  await page.locator('.kg-disclosure>summary').evaluate(el => el.click());
  await page.mouse.up({ button: 'middle' });
  const cleanup = await page.evaluate(() => { const e = new WheelEvent('wheel', { bubbles: true, cancelable: true, deltaY: 100 }); document.dispatchEvent(e); return !e.defaultPrevented; });
  assert.equal(cleanup, true); checks.push('折叠卸载后不残留全局滚动拦截');
  assert.deepEqual(errors, []);
  await writeFile(path.join(out, 'qa.json'), JSON.stringify({ status: 'PASS', scope: '本机真实知识图谱与浏览器交互；无模型调用，不替代用户视觉验收', url: url.href, checks, measurements, errors }, null, 2));
  console.log(JSON.stringify({ status: 'PASS', checks: checks.length, measurements, errors }));
} catch (error) {
  await writeFile(path.join(out, 'failure.json'), JSON.stringify({ checks, measurements, error: error.message, errors }, null, 2));
  await page.screenshot({ path: path.join(out, 'failure.png') }); throw error;
} finally { await browser.close(); }
