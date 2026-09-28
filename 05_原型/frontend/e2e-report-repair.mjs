/** UI contracts with independent fixtures. No model calls or human review submission. */
import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const base=process.env.PHARMA_E2E_URL;
assert.ok(base,'Set an isolated PHARMA_E2E_URL');
const out=process.env.PHARMA_E2E_OUT;
assert.ok(out,'Set PHARMA_E2E_OUT outside delivery originals');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.PHARMA_CHROME_PATH,headless:true,args:['--no-sandbox']});
const checks=[],errors=[],requests=[];
let ready=false,jobs=[],savedSelection;
const cid='pharmaceutical:imp-browser-fixture';
try {
 const page=await browser.newPage({viewport:{width:1366,height:900},locale:'zh-CN'});
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.route('**/health',r=>r.fulfill({json:{status:'ok'}}));
 await page.route('**/api/**',async route=>{
  const req=route.request(),path=new URL(req.url()).pathname,body=req.postData()?JSON.parse(req.postData()):null;
  requests.push({path,method:req.method(),body});let value={};
  if(path==='/api/workspace')value={status:'READY',context_id:cid,context:{context_id:cid,company_name:'独立界面测试企业'},issues:[],pending_files:0};
  else if(path==='/api/catalog')value={products:['独立测试制剂'],factories:['测试药厂'],months:['2031-06']};
  else if(path==='/api/analyses'){savedSelection=body;value={...body,snapshot_id:'fixture',metrics:{},elements:[],period:{start:body.month,end:body.month}};}
  else if(path==='/api/reports/preflight')value={ready,missing_elements:ready?[]:['直接人工','制造费用'],message:ready?'要素齐备':'完整报告缺少：直接人工、制造费用。当前有效数据仍可用于看板。'};
  else if(path==='/api/jobs')value=jobs;
  else if(path==='/api/reports')value={job_id:'fixture-report',status:'QUEUED'};
  else if(path==='/api/actions')value=[{id:'fixture-action',status:'DRAFT',payload:{task_title:'专题默认主题整改',source:{product:'独立测试制剂'},assignee:{name:'测试岗位',department:'测试部门'}},metadata:{context_id:cid,selection:{...savedSelection,topic:'成本变化与证据核查'}}}];
  else if(path.endsWith('/reviews'))value={reviews:[]};
  else if(path==='/api/assistant/conversations')value=[];
  else if(path==='/api/templates')value={templates:[]};
  else if(path==='/api/imports')value=[];
  else if(path==='/api/system/status')value={deployment:{label:'本地隔离测试'},network:{status:'not_checked'},data:{}};
  await route.fulfill({status:200,json:value});
 });
 const url=new URL(base);url.searchParams.set('page','reports');url.searchParams.set('analysis_type','special');url.searchParams.set('topic','  ');
 await page.goto(url.href);await page.getByText(/完整报告缺少：直接人工、制造费用/).waitFor();
 assert.equal(await page.getByRole('button',{name:'生成报告',exact:true}).isDisabled(),true);
 assert.equal(requests.filter(r=>r.path==='/api/reports').length,0);checks.push('缺要素生成前明确提示且不提交报告');
 ready=true;await page.reload();await page.getByRole('button',{name:'生成报告',exact:true}).waitFor();
 await page.getByRole('button',{name:'生成报告',exact:true}).click();
 assert.equal(requests.filter(r=>r.path==='/api/reports').at(-1).body.generation_mode,'reuse');
 jobs=[{id:'fixture-report',kind:'report',status:'DEGRADED',input:{...savedSelection,topic:'成本变化与证据核查'},result:{capability_status:'PASS',human_review_status:'PASS',narrative:{status:'PASS',findings:[]},docx:{artifact_id:'fixture-docx',status:'PASS'},pdf:{artifact_id:'fixture-pdf',status:'PASS'}}}];
 await page.reload();await page.getByRole('link',{name:'Word 下载（人工审核通过）',exact:true}).waitFor();
 assert.equal(await page.getByLabel('查看历史报告及失败记录').isChecked(),false);checks.push('空白主题报告在当前列表可见；下载显示真实审核状态');
 await page.getByRole('button',{name:'重新调用模型',exact:true}).click();
 assert.equal(requests.filter(r=>r.path==='/api/reports').at(-1).body.generation_mode,'fresh_model');
 await page.getByRole('button',{name:'仅修复产物',exact:true}).click();
 assert.equal(requests.filter(r=>r.path==='/api/reports').at(-1).body.generation_mode,'repair_artifacts');checks.push('普通复用、新增模型调用、仅修复产物分别传递');
 await page.screenshot({path:out+'/reports.png'});
 url.searchParams.set('page','actions');await page.goto(url.href);await page.locator('[data-task-id="fixture-action"]').waitFor();checks.push('默认专题整改任务可见');
 url.searchParams.set('page','templates');await page.goto(url.href);await page.getByText(/内置制药与用户导入报告均使用完整 Word 模板/).waitFor();checks.push('模板说明与报告页一致');
 assert.ok(requests.filter(r=>r.path==='/api/reports/preflight').every(r=>['context_id','factory','product','month'].every(k=>typeof r.body[k]==='string' && r.body[k].trim())));
 checks.push('工作区条件初始化完成后才发预检请求');
 assert.deepEqual(errors,[]);
 await writeFile(out+'/qa.json',JSON.stringify({status:'PASS',checks,errors,scope:'独立界面夹具；非业务人工评审'},null,2));
 console.log(JSON.stringify({status:'PASS',checks,errors}));
} finally {await browser.close();}
