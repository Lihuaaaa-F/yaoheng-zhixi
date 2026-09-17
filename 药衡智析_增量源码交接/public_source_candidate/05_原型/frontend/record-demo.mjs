/** Record real localhost screens from public, independently synthetic contexts only. */
import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const base=process.env.PHARMA_E2E_URL??'http://127.0.0.1:8765';
const out=process.env.PHARMA_DEMO_OUT??path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../../07_交付/demo');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.PHARMA_CHROME_PATH,headless:true,args:['--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN',recordVideo:{dir:out,size:{width:1440,height:1000}}});
const page=await context.newPage(),video=page.video();
// Fail closed before any private dataset can enter the recording.
await page.route('**/api/**',route=>{const request=route.request();return /competition/.test(request.url()+(request.postData()??''))?route.abort('blockedbyclient'):route.continue()});
const scenes=[];
async function scene(title,fn){console.log(title);await fn();await page.evaluate(title=>{let node=document.getElementById('demo-caption');if(!node){node=document.createElement('div');node.id='demo-caption';node.style.cssText='position:fixed;bottom:16px;left:240px;right:24px;padding:12px 18px;background:#143d43ee;color:white;border-radius:8px;z-index:9999;font:15px sans-serif;box-shadow:0 4px 18px #0002;';document.body.append(node)}node.textContent=`独立合成演示 · 无真人评分｜${title}`},title);scenes.push(title);await page.waitForTimeout(4500)}
try{
 await page.goto(`${base}/?context_id=pharmaceutical:synthetic-pharma`);
 await page.locator('.metric').first().waitFor({timeout:30000});
 if((await page.getByLabel('企业',{exact:true}).inputValue())!=='pharmaceutical:synthetic-pharma')throw Error('Refusing to record a private context');
 await scene('制药包：数值可追溯，模型与人工评审状态分别记录',async()=>{await page.evaluate(()=>scrollTo(0,0))});
 await scene('机械零部件：按件归集，成本要素和专用指标随行业切换',async()=>{await page.getByLabel('行业包').selectOption('mechanical_demo');await page.locator('.metric').first().getByText('30.00',{exact:false}).waitFor()});
 await scene('季度加权：季度成本 9,400 ÷ 产量 320 = 29.375 元/件',async()=>{await page.getByLabel('报告范围').selectOption('quarterly');await page.locator('.metric').first().getByText('29.38',{exact:false}).waitFor()});
 await scene('三步对标：先找差异，再拆结构；缺明细时不推算原因',async()=>{await page.getByRole('button',{name:/跨厂对标/}).click();await page.getByRole('heading',{name:/差异总览/}).waitFor({timeout:120000});await page.getByRole('heading',{name:/差异总览/}).scrollIntoViewIfNeeded()});
 await scene('化工流程：kg、批次、合格产出与单位能耗',async()=>{await page.getByRole('button',{name:/成本分析/}).click();await page.getByLabel('行业包').selectOption('chemical_demo');await page.locator('.metric').first().getByText('12.00',{exact:false}).waitFor();await page.getByRole('heading',{name:/行业专用指标/}).scrollIntoViewIfNeeded()});
 await scene('证据隔离：相同产品 ID 也仅检索当前企业与行业知识',async()=>{await page.getByRole('button',{name:/数据与证据/}).click();await page.getByLabel('知识检索问题').fill('批次 能耗');await page.getByRole('button',{name:'检索证据',exact:true}).click();await page.locator('.evidence-result').first().waitFor();await page.evaluate(()=>scrollTo(0,0))});
 await scene('任务看板：生成、模拟送达、责任人确认分别统计',async()=>{await page.getByRole('button',{name:/报告与任务/}).click();await page.getByRole('heading',{name:'当前企业任务看板'}).waitFor();await page.getByRole('heading',{name:'当前企业任务看板'}).scrollIntoViewIfNeeded()});
 await scene('能力边界：未实现的在制品与联副产品分配明确显示缺口',async()=>{await page.evaluate(()=>scrollTo(0,0));await page.locator('.capabilities summary').click()});
 await context.close();await video.saveAs(path.join(out,'synthetic-framework-demo.webm'));await video.delete();
 await writeFile(path.join(out,'README.md'),'# 合成演示素材\n\n本视频录制自真实本地 Web/API，仅使用三个独立公开合成包。无旁白，未使用私有赛题数据；不代表真实行业部署、模型实调通过、RPA送达通过或真人评分完成。这是可播放演示素材，仍须队友补充讲解与最终比赛演示剪辑。\n\n复现：启动本地服务后，在 `05_原型/frontend` 执行 `npm run demo:record`。浏览器路径可用 `PHARMA_CHROME_PATH` 指定，已有 Playwright 缓存可用 `PLAYWRIGHT_BROWSERS_PATH` 只读复用，不自动下载。`PHARMA_E2E_URL` 设置本地地址，`PHARMA_DEMO_OUT` 指定输出目录。\n\n场景：\n'+scenes.map((s,i)=>`${i+1}. ${s}`).join('\n')+'\n');
 console.log(JSON.stringify({status:'RECORDED',out,scenes}));
}finally{await browser.close()}
