import {displayNumber,displayFocusRate} from './presentation';
const modelLabels:Record<string,string>={DISABLED:'自动解释未开启，当前为规则分析。',NO_MODEL:'模型未配置，当前为规则分析。',QUEUED:'模型解释排队中…',RUNNING:'正在生成报告与解释。',FAILED:'本次自动解释失败，保留确定性分析；刷新不会重复调用，可手动重试。',DEGRADED:'报告已完成，模型或其他能力存在降级，详见下方分项状态。',SUCCEEDED:'已复用当前数据版本的报告与解释。'};
export default function FocusAnalysis({focus}:{focus:any}){
 if(!focus)return null;
 // 多条重点项的缺证提示逐字相同时只在面板尾部说明一次，避免成片重复稀释信号。
 const seenMissing=new Set<string>();
 const uniqueMissing:string[]=[];
 focus.items?.forEach((item:any)=>{(item.missing_evidence??[]).forEach((m:string)=>{if(!seenMissing.has(m)){seenMissing.add(m);uniqueMissing.push(m)}})});
 // 2026-09-24 反馈：按变动幅度排序并标注等级，首要项一眼可辨；颜色沿用模块方向语义（升=风险橙、降=有利绿）。
 const items=(focus.items??[]).slice().sort((a:any,b:any)=>Math.abs(Number(b.rate))-Math.abs(Number(a.rate)));
 const top=items[0];
 return <section className="panel focus-panel" aria-label="自动重点分析"><h2>自动重点分析</h2><p className="muted">环比绝对值 &gt; 10%，按变动幅度排序。</p>
 {items.length?<>
  <p className="focus-summary">共 <b>{items.length}</b> 项触发重点分析{top?<>，{Number(top.rate)>0?'升幅':'降幅'}最大的是 <b>{top.element} · {top.basis==='unit'?'单位成本':'总成本'}（{Number(top.rate)>0?'+':''}{displayFocusRate(top.rate)}%）</b></>:null}</p>
  <div className="focus-list">{items.map((item:any,i:number)=>{
   const up=Number(item.rate)>0;
   return <article className={`focus-card ${up?'up':'down'}${i===0?' focus-primary':''}`} key={`${item.element_key}:${item.basis}`}>
    <span className="focus-rank">{i===0?'首要关注':`关注 ${String(i+1).padStart(2,'0')}`}</span>
    <div className="focus-body">
     <div className="focus-target">{item.element} · {item.basis==='unit'?'单位成本':'总成本'}</div>
     <div className="focus-compare">{item.current!=null&&item.base!=null?`${displayNumber(item.base)} → ${displayNumber(item.current)} ${item.unit}`:item.text}</div>
    </div>
    <div className={`focus-rate ${up?'up':'down'}`}><span aria-hidden="true">{up?'▲':'▼'} {item.rate>0?'+':''}{displayFocusRate(item.rate)}</span><small>%</small></div>
   </article>})}</div>
 </>:<p>当前可比要素未触发重点分析阈值。</p>}
 {uniqueMissing.length>0&&<p className="muted">待补证据：{uniqueMissing.join('；')}</p>}
 {focus.missing?.length>0&&<details open><summary>缺少比较数据</summary><ul>{focus.missing.map((item:any)=><li key={`${item.element_key}:${item.basis}`}>{item.element} · {item.basis==='unit'?'单位成本':'总成本'}：{item.reason}</li>)}</ul></details>}
 {focus.items?.length>0&&<p role="status" className="notice">{modelLabels[focus.model_status]??'模型解释暂不可用，保留确定性分析。'}</p>}
 </section>
}
