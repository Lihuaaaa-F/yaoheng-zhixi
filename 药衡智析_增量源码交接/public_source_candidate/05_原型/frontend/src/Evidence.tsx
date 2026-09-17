import { useState, useEffect, useRef } from 'react';
import { api, contextQuery } from './api';
import { cleanText, sourceLabel, DeveloperDetails, MetricDetails } from './presentation';
import Chart from './Chart';
export default function Evidence({ contextId, product, month, factory, onOpen }: {contextId:string;product:string; month?:string; factory?:string; onOpen:(v:any)=>void}) {
 const searchController=useRef<AbortController|undefined>(undefined);
 const [query,setQuery]=useState('设备停机记录'),[mode,setMode]=useState('hybrid'),[results,setResults]=useState<any>(null),[status,setStatus]=useState<any>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{const c=new AbortController();api(`/kb?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setStatus(x)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[contextId]);
 useEffect(()=>{searchController.current?.abort();setResults(null);setBusy(false);return()=>searchController.current?.abort()},[contextId,product,month,factory]);
 async function search(){searchController.current?.abort();const c=new AbortController();searchController.current=c;setBusy(true);setError('');try{const response=await api('/kb/search',{query,product,month,factory,mode,context_id:contextId},c.signal);if(!c.signal.aborted)setResults(response)}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:String(e))}finally{if(!c.signal.aborted)setBusy(false)}}
 const hits=Array.isArray(results)?results:results?.evidence??results?.results??results?.hits??[];
 return <><section className="panel"><h2>数据与知识来源</h2><p className="muted">按文档名、章节和真实页码核查。文档有记录不等于已证实本期成本原因。</p>{status&&<><p>已登记来源 {Object.keys(status.sources??{}).length} 份；索引{status.status==='PASS'?'可用':'需要复核'}。</p><DeveloperDetails value={status}/></>}</section><section className="panel"><h2>适用证据检索</h2><form className="search-row" onSubmit={e=>{e.preventDefault();void search()}}><input aria-label="知识检索问题" value={query} onChange={e=>setQuery(e.target.value)} placeholder="输入工艺、物料或设备问题"/><select aria-label="检索方式" value={mode} onChange={e=>setMode(e.target.value)}><option value="hybrid">语义与关键词混合</option><option value="bm25">关键词 BM25</option><option value="vector">语义向量</option></select><button className="primary" disabled={busy||!query.trim()}>{busy?'检索中…':'检索证据'}</button></form><p className="muted">核查范围：{product} · {factory} · {month}。通用知识仅解释机制；本期归因还须核对规格、期间和文档版本。</p>{error&&<p role="alert" className="error">{error}</p>}{results&&<p role="status">找到 {hits.length} 条候选依据{results.degraded_reason?'；部分检索能力未通过，请复核证据覆盖。':''}</p>}{results&&!hits.length&&<p className="empty">证据不足：没有适用记录，请补充相关产品和期间的原始资料。</p>}{hits.map((h:any,i:number)=><article className="evidence-result" key={h.evidence_id??i}><strong>{sourceLabel(h)}</strong><p>适用范围：{h.products?.join('、')||h.scope_label||'产品适用性待核对'}。{h.applicability?.reason??'引用前请核对该记录是否支持当前问题。'}</p><button onClick={()=>onOpen(h)}>查看来源与适用性</button></article>)}{results&&<DeveloperDetails value={results}/>}</section><KnowledgeGraphPanel contextId={contextId}/></>
}

// 知识图谱面板（赛题加分项）：产品-药材-工序关系可视化，检索词由此增强。
function KnowledgeGraphPanel({contextId}:{contextId:string}) {
 const [graph,setGraph]=useState<any>(null);
 useEffect(()=>{const c=new AbortController();setGraph(null);api(`/kb/graph?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setGraph(x)}).catch(()=>{if(!c.signal.aborted)setGraph(null)});return()=>c.abort()},[contextId]);
 if(!graph)return null;
 if(graph.status!=='PASS')return <section className="panel"><h2>知识图谱</h2><p className="notice">{graph.reason??'当前知识源未解析出配方或工艺结构，图谱为空。'}</p></section>;
 const categories=[{name:'产品'},{name:'药材'},{name:'工序'}];
 const typeIndex=(t:string)=>({product:0,material:1,process:2})[t]??0;
 const nodes=graph.nodes.map((n:any)=>({id:n.id,name:n.label,category:typeIndex(n.type),symbolSize:n.type==='product'?46:22,value:n.type==='product'?'产品':n.type==='material'?'药材':'工序'}));
 const edges=graph.edges.map((e:any)=>({source:e.source,target:e.target,value:e.relation}));
 return <section className="panel"><div className="panel-heading"><h2>知识图谱 · 配方与工艺</h2><span>{graph.stats?.products??0} 产品 · {graph.stats?.materials??0} 药材 · {graph.stats?.process_steps??0} 工序</span></div>
  <Chart label="知识图谱" option={{tooltip:{show:false},legend:{data:categories.map(c=>c.name),bottom:4},series:[{type:'graph',layout:'force',roam:true,draggable:true,categories,label:{show:true},force:{repulsion:220,edgeLength:[60,120]},data:nodes,links:edges,emphasis:{focus:'adjacency'},lineStyle:{color:'#9eafb9',curveness:0.15},edgeLabel:{show:false}}]}}/>
  <p className="muted">图谱由当前知识库版本确定性抽取（规则 {graph.rules_version}），检索时自动把所选产品的药材与工序补充进关键词检索。图中关系不构成成本归因结论。</p></section>;
}
export function EvidenceDrawer({value,onClose}:{value:any;onClose:()=>void}) {
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()};document.addEventListener('keydown',fn);return()=>document.removeEventListener('keydown',fn)},[onClose]);
 const sources=value.evidence??(value.source||value.source_file?[value]:[]);
 return <div className="drawer-backdrop" onClick={onClose}><aside className="drawer" role="dialog" aria-modal="true" aria-label="证据与计算口径" onClick={e=>e.stopPropagation()}><div className="panel-heading"><h2>证据与计算口径</h2><button onClick={onClose} autoFocus>关闭</button></div>{value.rendered_text&&<p>{cleanText(value.rendered_text)}</p>}<MetricDetails value={value}/>{value.reason&&<p className="notice">{cleanText(value.reason)}</p>}{value.missing_evidence?.length>0&&<p>待补充：{value.missing_evidence.join('；')}</p>}{sources.map((s:any,i:number)=><div className="evidence-result" key={i}><strong>{sourceLabel(s)}</strong><p>适用产品：{s.products?.join('、')||'待核对'}；{s.applicability?.reason??'需按规格、工厂、期间和文档版本进一步核验。'}</p>{s.supporting_excerpt&&<blockquote>{cleanText(s.supporting_excerpt)}</blockquote>}</div>)}<p className="muted">原始文档与完整检索内容留在机器审计详情中。引用位置存在不等于原因已被证实。</p><DeveloperDetails value={value}/></aside></div>
}
