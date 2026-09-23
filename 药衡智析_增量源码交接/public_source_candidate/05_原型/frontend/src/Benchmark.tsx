import { useState } from 'react';
import Chart from './Chart';
import JobProgress from './JobProgress';
import {AnalysisStatus,DeveloperDetails,sourceLabel} from './presentation';
import {findingLabel} from './NarrativePanel';
import { Details } from './Analysis';
import { fmt, pct } from './api';

// 模型解释异步补全（2026-09-23 审计 AUD-BENCH-01 修复）：后端 async 模式冷请求
// 即时返回确定性解释 + 报告任务 job_id；此处轮询任务进度条，完成后用任务
// narrative 中的对标章节解释替换"模型解释生成中"占位。首次运行需等待，
// 数值与证据部分立即可见。
function AsyncExplanation({ jobId, onEvidence, fallback, evidence }: { jobId: string; onEvidence: (x: any) => void; fallback: any; evidence: any[] }) {
  const [completed, setCompleted] = useState(false), [narrative, setNarrative] = useState<any>(null), [sources, setSources] = useState<any[]>(evidence), [error, setError] = useState('');
  const findings = (narrative?.findings ?? []).filter((f: any) => f.section === 'benchmark' && ['hypothesis', 'insufficient_evidence', 'recommendation'].includes(f.claim_type));
  return <>
    {!completed && <p className="notice" role="status">数值差异已就绪；模型解释正在后台处理，完成后会在此更新。</p>}
    <JobProgress jobId={jobId} label="对标解释进度" onDone={job=>{setCompleted(true);if(job.status==='FAILED'){setError(job.error??'模型解释未完成');return}setNarrative(job.result?.narrative??null);setSources(job.result?.evidence?.evidence??evidence)}} />
    {error && <p className="error" role="alert">{error}。下方保留确定性差异与规则假设。</p>}
    {completed && !narrative && !error && <p className="notice">任务已结束，但没有适用于当前对标的解释；请核查任务记录。</p>}
    {narrative && <AnalysisStatus narrative={narrative} />}
    {findings.map((f:any,i:number)=><div className="finding" key={i}><div className="finding-head"><strong>{findingLabel(f.claim_type)}</strong><button className="finding-evidence-btn" onClick={()=>onEvidence({...f,evidence:sources.filter((source:any)=>f.evidence_refs?.includes(source.evidence_id))})}>查看证据依据</button></div><p>{f.rendered_text}</p>{f.missing_evidence?.length>0&&<p className="muted">仍需补充：{f.missing_evidence.join('；')}</p>}{f.suggestion&&<p>{f.suggestion}</p>}</div>)}
    {completed && !findings.length && !error && <p className="muted">当前未形成额外的可用模型归因。规则假设与证据仍可逐条核查。</p>}
  </>;
}

export default function Benchmark({ data, analysisType, onSwap, onEvidence }: {
    data: any;
    analysisType?: string;
    onSwap: () => void;
    onEvidence: (x: any) => void;
}) { const unit = data?.elements?.[0]?.unit ?? data?.unit ?? data?.unit_cost_unit ?? data?.summary?.find((r:any)=>r.name==='单位成本')?.unit ?? (data?.quantity_unit ? `${data.currency??'元'}/${data.quantity_unit}` : '未提供单位'); const period = data?.period?.label ?? (analysisType==='quarterly' && data?.month ? `${data.month.slice(0,4)} 年第 ${Math.ceil(Number(data.month.slice(-2))/3)} 季度` : data?.month); const syntheticLabel = [data?.details?.left, data?.details?.right].find((d: any) => d?.data_label)?.data_label; const queued = data?.narrative?.model_status === 'QUEUED' && data?.narrative?.job_id; return <><div className="section-title"><div><h2>三步跨厂对标</h2><p>{data?.direction ?? (data ? `${data.left} 与 ${data.right} · ${period}` : '载入同规格、同期间成本对比')}{data ? `；成本要素按 ${unit} 比较，总成本与产量按表内单位。` : ''}</p></div><button onClick={onSwap}>交换工厂方向</button></div>{syntheticLabel && <p className="notice">{syntheticLabel}。差异方向与汇总数值来自题包真实数据；结构分解结论仅用于演示。</p>}{data && <><section className="panel"><h2><b className="step">1</b>差异总览</h2><div className="table-scroll"><table><thead><tr><th>指标</th><th>{data.left}</th><th>{data.right}（基准）</th><th>差异额</th><th>差异率</th></tr></thead><tbody>{data.summary.map((r: any, i: number) => <tr key={i}><td>{r.name}（{r.unit}）</td><td>{fmt(r.left)}</td><td>{fmt(r.right)}</td><td>{fmt(r.delta)}</td><td>{pct(r.rate)}</td></tr>)}</tbody></table></div></section><section className="panel"><h2><b className="step">2</b>{data.product} · {period} 成本要素结构</h2><Chart label="跨厂成本要素对比图" option={{color:['#bd673f','#227c81'],tooltip:{trigger:'axis'},legend:{bottom:0},grid:{left:65,right:25,top:35,bottom:65},xAxis:{type:'category',data:data.elements.map((e:any)=>e.name)},yAxis:{type:'value',min:0,name:unit},series:[{name:data.left,type:'bar',data:data.elements.map((e:any)=>Number(e.left)),label:{show:true,position:'top',formatter:(p:any)=>fmt(p.value)}},{name:data.right,type:'bar',data:data.elements.map((e:any)=>Number(e.right)),label:{show:true,position:'top',formatter:(p:any)=>fmt(p.value)}}]}}/><div className="table-scroll"><table><thead><tr><th>要素</th><th>{data.left}</th><th>{data.right}</th><th>差异额（{unit}）</th><th>占跨厂总差额</th><th>差异率</th></tr></thead><tbody>{data.elements.map((r: any) => <tr key={r.key}><td>{r.name}</td><td>{fmt(r.left)}</td><td>{fmt(r.right)}</td><td>{fmt(r.delta)}</td><td>{pct(r.contribution)}</td><td>{pct(r.rate)}</td></tr>)}</tbody></table></div></section><div className="chart-grid"><div><h3>{data.left}</h3><Details details={data.details.left}/></div><div><h3>{data.right}</h3><Details details={data.details.right}/></div></div><section className="panel"><h2><b className="step">3</b>原因假设与建议</h2>{!queued&&<AnalysisStatus narrative={data.narrative}/>} {queued && <AsyncExplanation key={data.narrative.job_id} jobId={data.narrative.job_id} onEvidence={onEvidence} fallback={data.narrative} evidence={data.evidence?.evidence??[]}/>}{data.hypotheses?.map((h: any, i: number) => <div className="finding" key={i}><div className="finding-head"><strong>{findingLabel(h.claim_type??'hypothesis')}</strong><button className="finding-evidence-btn" aria-label={`查看第${i+1}条${findingLabel(h.claim_type??'hypothesis')}的证据依据`} onClick={() => onEvidence(h)}>查看证据依据</button></div><p>{h.hypothesis}</p>{h.missing_evidence?.length>0&&<p className="muted">缺少证据：{Array.isArray(h.missing_evidence) ? h.missing_evidence.join('；') : h.missing_evidence}</p>}{h.suggestion&&h.suggestion!==h.hypothesis&&<p className="finding-suggestion">建议：{h.suggestion}</p>}</div>)}<h3>相关文档证据</h3><p className="muted">候选依据仅供核查，不表示已证实跨厂因果。采购与工艺原因需要双方明细支持。</p>{data.evidence?.evidence?.map((e: any) => <div className="evidence-result" key={e.evidence_id}><strong>{sourceLabel(e)}</strong><p>适用产品：{e.products?.join("、")||"待核对"}；引用前核对工厂与期间。</p><button onClick={() => onEvidence(e)}>查看来源位置</button></div>)}<p className="notice">跨厂汇总只能证明差异。采购、工艺、设备原因需进一步取证；生产变更须按本企业政策人工批准。</p><DeveloperDetails value={{narrative:data.narrative,evidence:data.evidence}}/></section></>}</>; }
