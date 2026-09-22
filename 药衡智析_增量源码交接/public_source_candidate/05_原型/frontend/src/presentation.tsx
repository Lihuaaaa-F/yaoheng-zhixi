import { fmt } from './api';
// Presentation only: original Decimal strings remain in API evidence and exact tables.
export const displayNumber=(value:unknown)=>value==null?'N/A':Number(value).toLocaleString('zh-CN',{maximumFractionDigits:4});
export function displayFocusRate(value:unknown){
 const raw=String(value), number=Number(value);
 // Do not round a just-over-threshold rate back onto the strict ±10% boundary.
 if (/^-?10\.0*[1-9]/.test(raw)&&Math.abs(Number(number.toFixed(4)))===10)return raw;
 return displayNumber(value);
}

export const cleanText = (value: unknown) => String(value ?? '').replace(/\\r\\n|\\n|\\r/g, '\n').replace(/\\t/g, ' ').trim();
export function sourceLabel(e: any) {
 const source = e.source_file ?? e.source ?? e.table ?? '来源待核对';
 const name = String(source).split(/[\\/]/).at(-1);
 const location = e.page ? `第 ${e.page} 页` : e.location;
 return [name, e.heading ?? e.section, location, e.product, e.period].filter(v=>typeof v==='string'||typeof v==='number').join(' · ');
}
// Business views deliberately omit engineering hashes, raw paths and debug JSON.
export function DeveloperDetails(_props: {value:any}) { return null }
export function AnalysisStatus({narrative,review}: {narrative:any;review?:any}) {
 const mode=narrative?.generation_mode;
 const generation=mode==='llm'&&narrative?.model_live===true?'模型解释':mode==='mixed'?'模型与规则混合解释':mode==='rules'?'规则分析':'解释来源待核验';
 const verified=Boolean(review?.readability?.reviewer&&review?.visual_quality?.reviewer); const reviewedScore=review?.human_attribution_score;
 return <p className={narrative?.status==='PASS'?'muted':'notice'}>解释来源：{generation}。{narrative?.status==='PASS'?'数字与证据自动校验已通过。':'部分解释未通过数字与证据自动校验，已降级为基础分析；可重新生成。'}人工审核：{verified?'已审核':review?.status==='STALE'?'原审核已失效，待重审':'待评'}{verified&&Number.isFinite(reviewedScore)?`；归因评分 ${reviewedScore}/5`:''}。</p>;
}
const dimensions=[['file_openable','文件可打开'],['calculation_consistency','计算一致'],['section_completeness','章节实质完整'],['evidence_applicability','证据适用'],['readability','内容可读'],['visual_quality','视觉合格'],['task_actionability','任务可执行'],['model_participation','模型实际参与']];
const statusText=(s:any)=>({PASS:'通过',FAIL:'未通过',FAILED:'未通过',PENDING:'待评',PENDING_HUMAN:'待人工评审',NOT_RUN:'未验证',DEGRADED:'未通过',NOT_APPLICABLE:'不适用',BLOCKED:'未通过',UNVERIFIED:'未验证'}[String(s)]??'待评');
export function Acceptance({result}:{result:any}) {
 const acceptance=result?.acceptance??result?.report_acceptance??{};
 const values=acceptance.dimensions??acceptance;
 const humanAllPass=(['section_completeness','readability','visual_quality'] as const).every(k=>(values[k]?.status??values[k])==='PASS');
 const allPass=dimensions.every(([key])=>(values[key]?.status??values[key])==='PASS');
 const overall=acceptance.overall==='PASS'&&allPass?'合格':humanAllPass?'人工验收已通过 · 系统分项存在未通过项':'尚未合格／待评';
 return <div className="acceptance"><p><strong>报告验收：{overall}</strong> · 文件生成成功仅代表产生文件；人工验收以上传的验收文档为准。</p><dl>{dimensions.map(([key,label])=>{const item=values[key];let state=item?.status??item;return <div key={key}><dt>{label}</dt><dd title={typeof item?.reason==='string'?item.reason:undefined}>{statusText(state)}</dd></div>})}</dl><p className="muted">人工归因评分：{Number.isFinite(acceptance.human_attribution_score)&&values.readability?.reviewer?`${acceptance.human_attribution_score}/5（${values.readability.reviewer}）`:"待真人评审"}。可读性与版式以绑定当前产物的实际审核记录为准。</p></div>;
}
export function periodLabel(period:any){ if(!Array.isArray(period)) return String(period ?? ''); const p=period.map(String); return p.length>2 ? `${p[0]}–${p[p.length-1]}（${p.length}个月）` : p.join(' 至 '); }
export function MetricDetails({value}:{value:any}) {return <><p className="muted">{value.product} {value.factory} {value.period?.start}{value.period?.end&&value.period?.end!==value.period?.start?` 至 ${value.period.end}`:""}</p>{value.row_keys?.length>0&&<p>数据来源：{[...new Set(value.row_keys.map((key:string)=>key.replace(/:\d+$/,'')))].join("；")} · {value.product} · {value.period?.end??"所选期间"}</p>}<dl className="task-details">{value.value!==undefined&&<><dt>指标数值</dt><dd>{fmt(value.value)} {value.unit}</dd></>}{value.formula&&<><dt>计算口径</dt><dd>{cleanText(value.formula)}</dd></>}{value.comparison_period&&<><dt>比较期间</dt><dd>{periodLabel(value.comparison_period)}</dd></>}{value.numerator!==undefined&&<><dt>分子</dt><dd>{fmt(value.numerator)}</dd></>}{value.denominator!==undefined&&<><dt>分母</dt><dd>{fmt(value.denominator)}</dd></>}</dl></>}
