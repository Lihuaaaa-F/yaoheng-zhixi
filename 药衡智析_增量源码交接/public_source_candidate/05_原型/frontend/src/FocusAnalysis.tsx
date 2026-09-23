import {displayNumber,displayFocusRate} from './presentation';
const modelLabels:Record<string,string>={DISABLED:'自动模型解释未开启；当前为确定性分析。',NO_MODEL:'未配置模型，已保留确定性变化与缺证说明。',QUEUED:'已进入报告队列，模型解释完成后自动显示在下方。',RUNNING:'正在生成报告与解释。',FAILED:'本次自动解释失败，保留确定性分析；刷新不会重复调用，可手动重试。',DEGRADED:'报告已完成，模型或其他能力存在降级，详见下方分项状态。',SUCCEEDED:'已复用当前数据版本的报告与解释。'};
export default function FocusAnalysis({focus}:{focus:any}){
 if(!focus)return null;
 // 多条重点项的缺证提示逐字相同时只在面板尾部说明一次，避免成片重复稀释信号。
 const seenMissing=new Set<string>();
 const uniqueMissing:string[]=[];
 focus.items?.forEach((item:any)=>{(item.missing_evidence??[]).forEach((m:string)=>{if(!seenMissing.has(m)){seenMissing.add(m);uniqueMissing.push(m)}})});
 return <section className="panel" aria-label="自动重点分析"><h2>自动重点分析</h2><p className="muted">各要素环比严格超过 ±10% 即显示；单位与总额分别判断，恰好 ±10% 不触发。以下通常显示至四位小数，临界值保留必要精度。</p>{focus.items?.length?focus.items.map((item:any,i:number)=><article className="finding" key={`${item.element_key}:${item.basis}`}><div className="finding-head"><strong>{item.element} · {item.basis==='unit'?'单位成本':'总成本'} · {Number(item.rate)>0?'+':''}{displayFocusRate(item.rate)}%</strong></div><p>{item.current!=null&&item.base!=null?<>{item.element}{item.basis==='unit'?'单位成本':'总成本'}由 {displayNumber(item.base)} {item.unit}变为 {displayNumber(item.current)} {item.unit}，环比{Number(item.rate)>0?'上升':'下降'} {displayFocusRate(String(item.rate).replace(/^-/,''))}%，严格超过 ±10%，列为重点分析。</>:item.text}</p></article>):<p>当前可比要素未触发重点分析阈值。</p>}{uniqueMissing.length>0&&<p className="muted">缺少证据（各重点项共用）：{uniqueMissing.join('；')}</p>}{focus.missing?.length>0&&<details open><summary>不可比较的要素（不按零值处理）</summary><ul>{focus.missing.map((item:any)=><li key={`${item.element_key}:${item.basis}`}>{item.element} · {item.basis==='unit'?'单位成本':'总成本'}：{item.reason}</li>)}</ul></details>}{focus.items?.length>0&&<p role="status">{modelLabels[focus.model_status]??'模型解释暂不可用，保留确定性分析。'}</p>}</section>
}
