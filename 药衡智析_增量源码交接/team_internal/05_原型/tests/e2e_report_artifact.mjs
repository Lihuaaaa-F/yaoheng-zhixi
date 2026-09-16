import {chromium} from '../frontend/node_modules/playwright/index.mjs';
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
process.env.TMPDIR='/tmp';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const html=await fs.readFile(path.join(root,'07_交付/药析证链_制药成本智能分析一等奖方案.html'));
const server=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html)});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
let browser;const result={status:'RUNNING',browser_plugin:'ABSENT: Browser plugin not available; regular Playwright',checks:[],console_errors:[]};
try{
 browser=await chromium.launch({executablePath:'/mnt/d/AI_Cache/ms-playwright/chromium-1228/chrome-linux64/chrome',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1366,height:768}});page.on('pageerror',e=>result.console_errors.push(String(e)));
 await page.goto(`http://127.0.0.1:${server.address().port}/`,{waitUntil:'networkidle'});
 await page.waitForFunction(()=>document.documentElement.dataset.dataAnalyticsPortableReader==='ready',{timeout:30000});
 const body=await page.locator('body').innerText();
 const reportSources=JSON.parse(await fs.readFile(path.join(root,'06_评测/scenario_reports.json'),'utf8'));
 for(const [name,pass] of [['current_project',body.includes('药衡智析')],['reviewed_four_report_statuses',reportSources.length===4&&reportSources.every(r=>body.includes(r.scenario+'：'+r.status))],['current_stack',body.includes('React')&&body.includes('Chroma')],['no_stale_stack',!body.includes('Vue 3')&&!body.includes('Python 3.11')],['html_no_horizontal_overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)],['no_runtime_errors',result.console_errors.length===0]]){
  result.checks.push({name,status:pass?'PASS':'FAIL'});if(!pass)throw new Error(name);
 }
 result.chart_elements=await page.locator('svg,canvas').count();
 await page.screenshot({path:path.join(root,'06_评测/report_artifact_browser.png'),fullPage:false});
 for(const [index,title] of ['当前49项要求的证据状态','三个场景的单位成本比较','知识库文档页数分布'].entries()){
 const heading=page.locator('#data-analytics-portable-reader').getByText(title,{exact:true}).first();await heading.scrollIntoViewIfNeeded();await page.screenshot({path:path.join(root,`06_评测/report_artifact_chart_${index+1}.png`),fullPage:false});
}
 const reader=await page.evaluate(()=>window.__DATA_ANALYTICS_PORTABLE_ARTIFACT__);
 result.checks.push({name:'runtime_artifact_matches_disk',status:JSON.stringify(reader)===JSON.stringify(JSON.parse(await fs.readFile(path.join(root,'07_交付/artifact.json'),'utf8')))?'PASS':'FAIL'});
 result.status=result.checks.every(c=>c.status==='PASS')?'PASS':'FAIL';
}catch(e){result.status='FAIL';result.error=String(e)}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));await fs.writeFile(path.join(root,'06_评测/report_artifact_browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));if(result.status!=='PASS')process.exitCode=1;}
