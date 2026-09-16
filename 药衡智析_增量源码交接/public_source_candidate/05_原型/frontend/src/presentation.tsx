import { fmt } from './api';
export const cleanText = (value: unknown) => String(value ?? '').replace(/\\r\\n|\\n|\\r/g, '\n').replace(/\\t/g, ' ').trim();
export function sourceLabel(e: any) {
 const source = e.source_file ?? e.source ?? e.table ?? '来源待核对';
 const name = String(source).split(/[\\/]/).at(-1);
 const location = e.page ? `第 ${e.page} 页` : e.location;
 return [name, e.heading ?? e.section, location, e.product, e.period].filter(v=>typeof v==='string'||typeof v==='number').join(' · ');
}
export function DeveloperDetails({value}: {value:any}) { return <details className="developer-details"><summary>开发者详情（机器审计）</summary><pre>{JSON.stringify(value,null,2)}</pre></details> }
export function AnalysisStatus({narrative}: {narrative:any}) {
 const live = narrative?.model_live === true && narrative?.generation_mode !== 'rules';
 return <p className={live && narrative?.status === 'PASS' ? 'muted' : 'notice'}>{live ? (narrative?.status==='PASS' ? '本次有模型辅助解释；原因归因及可读性仍待人工审核。' : '本次部分解释采用基础分析，受影响章节的原因解释待复核。') : '本次采用基础分析，原因解释待复核。'} 人工归因评分：待评。</p>;
}
const dimensions=[['file_openable','文件可打开'],['calculation_consistency','计算一致'],['section_completeness','章节实质完整'],['evidence_applicability','证据适用'],['readability','内容可读'],['visual_quality','视觉合格'],['task_actionability','任务可执行'],['model_participation','模型实际参与']];
const statusText=(s:any)=>({PASS:'通过',FAIL:'未通过',FAILED:'未通过',PENDING:'待评',PENDING_HUMAN:'待人工评审',NOT_RUN:'未验证',DEGRADED:'未通过',NOT_APPLICABLE:'不适用',BLOCKED:'未通过',UNVERIFIED:'未验证'}[String(s)]??'待评');
export function Acceptance({result}:{result:any}) {
 const acceptance=result?.acceptance??result?.report_acceptance??{};
 const values=acceptance.dimensions??acceptance;
 return <div className="acceptance"><p><strong>报告验收：{acceptance.overall==='PASS'&&dimensions.every(([key])=>(values[key]?.status??values[key])==='PASS')?'合格':'尚未合格／待评'}</strong> · 文件生成成功仅代表产生文件。</p><dl>{dimensions.map(([key,label])=>{const item=values[key];let state=item?.status??item;if(key==='model_participation'&&!state)state=result?.narrative?.model_live===true?'PASS':'FAIL';return <div key={key}><dt>{label}</dt><dd title={typeof item?.reason==='string'?item.reason:undefined}>{statusText(state)}</dd></div>})}</dl><p className="muted">人工归因 0–5 分、可读性与版式评审以实际审核记录为准；历史失败记录保留。</p></div>;
}
export function periodLabel(period:any){ if(!Array.isArray(period)) return String(period ?? ''); const p=period.map(String); return p.length>2 ? `${p[0]}–${p[p.length-1]}（${p.length}个月）` : p.join(' 至 '); }
export function MetricDetails({value}:{value:any}) {return <><p className="muted">{value.product} {value.factory} {value.period?.start}{value.period?.end&&value.period?.end!==value.period?.start?` 至 ${value.period.end}`:""}</p>{value.row_keys?.length>0&&<p>数据来源：{[...new Set(value.row_keys.map((key:string)=>key.replace(/:\d+$/,'')))].join("；")} · {value.product} · {value.period?.end??"所选期间"}</p>}<dl className="task-details">{value.value!==undefined&&<><dt>指标数值</dt><dd>{fmt(value.value)} {value.unit}</dd></>}{value.formula&&<><dt>计算口径</dt><dd>{cleanText(value.formula)}</dd></>}{value.comparison_period&&<><dt>比较期间</dt><dd>{periodLabel(value.comparison_period)}</dd></>}{value.numerator!==undefined&&<><dt>分子</dt><dd>{fmt(value.numerator)}</dd></>}{value.denominator!==undefined&&<><dt>分母</dt><dd>{fmt(value.denominator)}</dd></>}</dl></>}
