/** Independent two-product fixtures; no model, RPA, or contest-data changes. */
import {chromium} from 'playwright';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const out=process.env.PHARMA_E2E_OUT??'/tmp/yaoheng-dashboard-ui';
const base=process.env.PHARMA_E2E_URL??'http://127.0.0.1:5179';
await mkdir(out,{recursive:true});
const cid='synthetic:two-products',requests=[],errors=[],checks=[];
const products=['独立产品甲','独立产品乙'],months=['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06'];
const snapshot=s=>({snapshot_id:`${s.product}:${s.month}:${s.basis}`,context_id:cid,...s,period:{start:s.month,end:s.month},metrics:{unit_cost:{value:'110.0001',unit:'USD/item'},total_cost:{value:'220.0002',unit:'USD'},quantity:{value:'2',unit:'item'},mom:{value:'10.0001'},yoy:{value:null},budget:{value:null}},elements:[],trend:[],focus:{items:[{element_key:'energy',element:'独立能耗',basis:'unit',rate:'10.0001',text:'独立能耗单位成本由 100 USD/item 变为 110.0001 USD/item，环比上升 10.0001%，严格超过 ±10%，列为重点分析。',missing_evidence:['缺少经核实的业务原因与对应原始记录。']}],missing:[{element_key:'other',element:'未提供要素',basis:'unit',reason:'缺少完整可比基期'}],model_status:'DISABLED'}});
const browser=await chromium.launch({headless:true,executablePath:process.env.PHARMA_CHROME_PATH,args:['--no-sandbox']});
try{
 const page=await browser.newPage({viewport:{width:1366,height:768}});
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route('**/api/**',async route=>{const r=route.request(),u=new URL(r.url()),body=r.postDataJSON();requests.push({path:u.pathname,query:Object.fromEntries(u.searchParams),body});let data={};
 if(u.pathname==='/api/industry/catalog')data={default_context_id:cid,contexts:[{context_id:cid,industry_id:'synthetic',industry_name:'独立样本',company_id:'two-products',company_name:'合成企业',data_label:'独立双产品合成样本'}]};
 else if(u.pathname==='/api/catalog')data={products,months,factories:['合成厂']};
 else if(u.pathname==='/api/analyses')data=snapshot(body);
 else if(u.pathname==='/api/jobs')data=[];
 else if(u.pathname==='/api/forecast')data={status:'INSUFFICIENT_HISTORY',reason:'独立样本未提供连续历史'};
 else if(u.pathname==='/api/agent/decision')data={decision:'REPORT_NEEDED',reason:'合成规则说明',signals:[],policy_version:'synthetic',advisory_status:'DISABLED'};
 else if(u.pathname==='/api/dashboard/heatmap'){const unit=u.searchParams.get('basis')==='unit'?'USD/item':'USD';data={products,months,elements:[{key:'all',name:'全部成本'},{key:'energy',name:'独立能耗'}],cells:products.flatMap((product,y)=>months.map((month,x)=>({product,month,status:y===1&&x===4?'MISSING':'AVAILABLE',reason:y===1&&x===4?'该产品缺少完整月份数据':null,values:y===1&&x===4?{}:{all:{value:y?'9.87654321':'1.23456789',unit},energy:{value:y?'4.00012345':'2.00054321',unit}}})))};}
 await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
 });
 await page.goto(base);await page.getByRole('heading',{name:'自动重点分析'}).waitFor();
 assert.match(await page.locator('title').textContent(),/药衡/);assert.equal(await page.locator('vite-error-overlay').count(),0);
 assert.match(await page.getByLabel('自动重点分析').innerText(),/110.0001 USD\/item/);assert.match(await page.getByLabel('自动重点分析').innerText(),/缺少完整可比基期/);checks.push('precise deterministic focus and missing-baseline explanation render immediately');
 await page.getByRole('img',{name:'产品月份成本热力图'}).waitFor();await page.getByText('查看产品月份精确值与缺失状态',{exact:true}).click();
 await page.getByRole('button',{name:'独立产品乙 2026-06 9.87654321 USD/item',exact:true}).waitFor();assert.match(await page.locator('main').innerText(),/缺失：该产品缺少完整月份数据/);
 await page.getByLabel('热力图成本要素').selectOption('energy');await page.getByRole('button',{name:'独立产品乙 2026-06 4.00012345 USD/item',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('select[aria-label="产品"]').value==='独立产品乙');
 assert.equal((requests.filter(r=>r.path==='/api/analyses').at(-1)).body.analysis_type,'monthly');checks.push('two-product grid preserves exact values, missing cells and element-click analysis linkage');
 await page.getByRole('button',{name:'总额',exact:true}).click();await page.getByRole('button',{name:'独立产品乙 2026-06 4.00012345 USD',exact:true}).waitFor();checks.push('cost basis selector changes grid units');
 await page.getByRole('heading',{name:'产品 × 月份成本热力图'}).scrollIntoViewIfNeeded();await page.screenshot({path:`${out}/grid-desktop.png`});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
 await page.reload();await page.getByRole('heading',{name:'自动重点分析'}).waitFor();assert.equal(requests.filter(r=>r.path==='/api/reports').length,0);assert.equal(requests.filter(r=>r.path==='/api/agent/decision'&&r.query.with_advisory==='true').length,0);checks.push('page refresh does not initiate model explanation or reports without configuration');
 await page.getByRole('heading',{name:'自动重点分析'}).scrollIntoViewIfNeeded();await page.screenshot({path:`${out}/focus-desktop.png`});
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:`${out}/focus-mobile.png`});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);checks.push('1366x768 and 390x844 no overflow, framework overlay or console errors');
 const receipt={status:'PASS',scope:'mocked independent synthetic browser contracts; not model or contest acceptance',browser:'Browser plugin not available; local Playwright',url:base,checks,errors};await writeFile(`${out}/qa.json`,JSON.stringify(receipt,null,2));console.log(JSON.stringify(receipt));
}finally{await browser.close()}
