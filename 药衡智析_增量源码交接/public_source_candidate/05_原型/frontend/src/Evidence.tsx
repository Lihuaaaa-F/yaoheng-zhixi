import { Suspense, lazy, useState, useEffect, useRef } from 'react';
import { api, contextQuery } from './api';
import { cleanText, sourceLabel, DeveloperDetails, MetricDetails } from './presentation';
// 2026-09-23 审查 SSE-2：Chart3D（echarts-gl 栈）改为动态加载——知识图谱仅在
// 证据抽屉渲染时才需要，静态引入会把约 497KB GL 依赖拖进首屏。
const Chart3D = lazy(() => import('./Chart3D'));
export default function Evidence({ contextId, product, month, factory, onOpen }: {contextId:string;product:string; month?:string; factory?:string; onOpen:(v:any)=>void}) {
 const searchController=useRef<AbortController|undefined>(undefined);
 const [query,setQuery]=useState('设备停机记录'),[mode,setMode]=useState('hybrid'),[results,setResults]=useState<any>(null),[status,setStatus]=useState<any>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{const c=new AbortController();api(`/kb?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setStatus(x)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[contextId]);
 useEffect(()=>{searchController.current?.abort();setResults(null);setBusy(false);return()=>searchController.current?.abort()},[contextId,product,month,factory]);
 async function search(){searchController.current?.abort();const c=new AbortController();searchController.current=c;setBusy(true);setError('');try{const response=await api('/kb/search',{query,product,month,factory,mode,context_id:contextId},c.signal);if(!c.signal.aborted)setResults(response)}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:String(e))}finally{if(!c.signal.aborted)setBusy(false)}}
 const hits=Array.isArray(results)?results:results?.evidence??results?.results??results?.hits??[];
 return <><section className="panel"><h2>数据与知识来源</h2><p className="muted">按文档名、章节和真实页码核查。文档有记录不等于已证实本期成本原因。</p>{status&&<><p>已登记来源 {Object.keys(status.sources??{}).length} 份；索引{status.status==='PASS'?'可用':'需要复核'}。</p><DeveloperDetails value={status}/></>}</section><section className="panel"><h2>适用证据检索</h2><form className="search-row" onSubmit={e=>{e.preventDefault();void search()}}><input aria-label="知识检索问题" value={query} onChange={e=>setQuery(e.target.value)} placeholder="输入工艺、物料或设备问题"/><select aria-label="检索方式" value={mode} onChange={e=>setMode(e.target.value)}><option value="hybrid">语义与关键词混合</option><option value="bm25">关键词 BM25</option><option value="vector">语义向量</option></select><button className="primary" disabled={busy||!query.trim()}>{busy?'检索中…':'检索证据'}</button></form><p className="muted">核查范围：{product} · {factory} · {month}。通用知识仅解释机制；本期归因还须核对规格、期间和文档版本。</p>{error&&<p role="alert" className="error">{error}</p>}{results&&<p role="status">找到 {hits.length} 条候选依据{results.degraded_reason?'；部分检索能力未通过，请复核证据覆盖。':''}</p>}{results&&!hits.length&&<p className="empty">证据不足：没有适用记录，请补充相关产品和期间的原始资料。</p>}{hits.map((h:any,i:number)=><article className="evidence-result" key={h.evidence_id??i}><strong>{sourceLabel(h)}</strong><p>适用范围：{h.products?.join('、')||h.scope_label||'产品适用性待核对'}。{h.applicability?.reason??'引用前请核对该记录是否支持当前问题。'}</p><button onClick={()=>onOpen(h)}>查看来源与适用性</button></article>)}{results&&<DeveloperDetails value={results}/>}</section><KnowledgeGraphPanel contextId={contextId}/></>
}

// 知识图谱面板（赛题加分项）：产品-药材-工序关系三维可视化。
// 2026-09-22 改版：graphGL（正交相机+2D roam，无真三维旋转）→ scatter3D 节点
// + lines3D 边 + grid3D 轨道相机——左键拖拽真三维旋转、滚轮缩放、右键平移，
// 悬停显示节点/关系说明，支持对 21 节点/27 边结构做视觉分析。
function KnowledgeGraphPanel({contextId}:{contextId:string}) {
 const [graph,setGraph]=useState<any>(null);
 const [fullscreen,setFullscreen]=useState(false);
 const [hoverInfo,setHoverInfo]=useState<{text:string;x:number;y:number}|null>(null);
 const chartDomRef=useRef<HTMLDivElement|null>(null);
 useEffect(()=>{const c=new AbortController();setGraph(null);api(`/kb/graph?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setGraph(x)}).catch(()=>{if(!c.signal.aborted)setGraph(null)});return()=>c.abort()},[contextId]);
 if(!graph)return null;
 if(graph.status!=='PASS')return <section className="panel"><h2>知识图谱</h2><p className="notice">{graph.reason??'当前知识源未解析出配方或工艺结构，图谱为空。'}</p></section>;
 const colors=['#227c81','#c08a3e','#8f5b7a'];
 const typeIndex=(t:string)=>({product:0,material:1,process:2})[t]??0;
 const typeLabel=(t:string)=>({product:'产品',material:'药材',process:'工序'})[t]??t;
 const height=fullscreen?Math.round(window.innerHeight*0.88):720;
 // 确定性三维布局：产品按等边三角分布，各产品的药材与工序绕本产品在
 // 倾斜环上按索引均匀转角；关系完全来自后端确定性抽取，坐标只影响展示。
 const productNodes=graph.nodes.filter((n:any)=>n.type==='product');
 const R=380, H=200;
 const posById=new Map<string,[number,number,number]>();
 const nodeMeta=new Map<string,{color:string;size:number;kind:string}>();
 productNodes.forEach((p:any,pi:number)=>{
   const angle=-Math.PI/2+pi*2*Math.PI/Math.max(productNodes.length,1);
   posById.set(p.id,[Math.cos(angle)*R,0,Math.sin(angle)*R]);
   nodeMeta.set(p.id,{color:colors[0],size:16,kind:'产品'});
 });
 const neighborOf=new Map<string,string[]>();
 for(const e of graph.edges){
   for(const [s,t] of [[e.source,e.target],[e.target,e.source]]){
     const list=neighborOf.get(s)??[];list.push(t);neighborOf.set(s,list);
   }
 }
 for(const p of graph.nodes.filter((n:any)=>n.type==='product')){
   const [cx,,cz]=posById.get(p.id)!;
   const neighbors=(neighborOf.get(p.id)??[]).filter((id:string)=>!posById.has(id));
   neighbors.forEach((id:string,idx:number)=>{
     if(posById.has(id))return;
     const a=idx*2*Math.PI/Math.max(neighbors.length,1)+ (posById.keys().next().value===p.id?0:.7);
     const y=H*(idx%2===0?1:-.6);
     posById.set(id,[cx+Math.cos(a)*190,y,cz+Math.sin(a)*190]);
   });
 }
 const nodeData=graph.nodes.filter((n:any)=>posById.has(n.id)).map((n:any)=>{
   const meta=nodeMeta.get(n.id)??{color:typeIndex(n.type)===1?colors[1]:colors[2],size:typeIndex(n.type)===1?9:8,kind:typeLabel(n.type)};
   const [x,y,z]=posById.get(n.id)!;
   return {name:n.label,value:[x,y,z],
     itemStyle:{color:meta.color,opacity:.95,borderColor:'#fff',borderWidth:1},
     symbolSize:n.type==='product'?20:meta.size,
     tooltip_kind:meta.kind};
 });
 // lines3D 的布局器不支持 cartesian3D（只支持 globe/geo3D/mapbox），改用
 // scatter3D 密集采样点渲染边：所有边的插值点合并进单一系列（减少 drawcall，
 // 27 边×41 点≈1100 符号，单系列渲染开销可控）。
 const SAMPLES=40;
 const edgePoints:any[]=[];
 for(const e of graph.edges){
   if(!posById.has(e.source)||!posById.has(e.target))continue;
   const a=posById.get(e.source)!,b=posById.get(e.target)!;
   const label=`${e.source} —${e.value||'相关'}→ ${e.target}`;
   for(let i=0;i<=SAMPLES;i++){
     const t=i/SAMPLES;
     edgePoints.push({value:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t],
       name:i===0||i===SAMPLES?label:'',tooltip_kind:'边'});
   }
 }
 const edgeSeriesOption={type:'scatter3D',coordinateSystem:'cartesian3D',
   data:edgePoints,symbolSize:1.8,
   itemStyle:{color:'#7d97a6',opacity:.45}};
 return <section className={`panel${fullscreen?' kg-fullscreen':''}`}>
  <div className="panel-heading"><h2>知识图谱 · 配方与工艺（三维）</h2>
   <div className="button-row"><span>{graph.stats?.products??0} 产品 · {graph.stats?.materials??0} 药材 · {graph.stats?.process_steps??0} 工序</span>
    <button onClick={()=>setFullscreen(f=>!f)}>{fullscreen?'退出全屏':'放大视图'}</button></div></div>
  <div className="kg-legend" role="list" aria-label="节点类型图例">
    {[['产品','#227c81'],['药材','#c08a3e'],['工序','#8f5b7a']].map(([t,c])=><span key={t} role="listitem"><i style={{background:c}}/>{t}</span>)}
    <span className="muted">连线为配方/工艺关系</span>
  </div>
  <div ref={chartDomRef} style={{position:'relative'}}>
  <Suspense fallback={<p className="muted" role="status">三维图谱组件加载中…</p>}>
  <Chart3D label="知识图谱三维视图" height={height}
   onHover={(info:any)=>setHoverInfo(info)} option={{
    tooltip:{formatter:(p:any)=>{
      const label=p.data?.name||p.name||'';
      if(p.data?.tooltip_kind==='边')return label;
      return `${label}（${p.data?.tooltip_kind??''}）`;
    }},
    legend:{show:false},
    series:[
      edgeSeriesOption,
      {type:'scatter3D',coordinateSystem:'cartesian3D',data:nodeData,
       tooltip:{show:true,formatter:(p:any)=>`${p.name}（${p.data?.tooltip_kind??''}）`},
       label:{show:true,formatter:(p:any)=>p.name,position:'right',distance:1,
         textStyle:{fontSize:12,color:'#28414d',fontWeight:400,
           textBorderColor:'#ffffff',textBorderWidth:3,textBorderType:'solid'}},
       emphasis:{label:{show:true,fontSize:15,fontWeight:600,
         textBorderColor:'#ffffff',textBorderWidth:3}}},
    ],
    xAxis3D:{show:false},yAxis3D:{show:false},zAxis3D:{show:false},
    grid3D:{
      width:900,height:520,depth:900,
      show:false,boxWidth:200,
      viewControl:{alpha:22,beta:20,distance:260,minDistance:60,maxDistance:620,
        rotateSensitivity:1,zoomSensitivity:1,panSensitivity:1,damping:.85,
        autoRotate:false,autoRotateAfterStill:4,autoRotateSpeed:8},
      light:{main:{intensity:1.1,shadow:false},ambient:{intensity:.5}},
      axisLine:{show:false},axisLabel:{show:false},splitLine:{show:false},
      axisPointer:{show:false},
    }}}/>
    </Suspense>
    {hoverInfo && <div className="kg-tooltip" style={{left:hoverInfo.x, top:hoverInfo.y}}>{hoverInfo.text}</div>}
  </div>
  <p className="muted">三维操作：左键拖拽<b>旋转</b> · 滚轮<b>缩放</b> · 右键拖拽<b>平移</b> · 静止 4 秒后<b>自动缓旋</b> · 悬停节点/连线<b>查看说明</b>。图谱由当前知识库版本确定性抽取（规则 {graph.rules_version}），检索时自动把所选产品的药材与工序补充进关键词检索。图中关系不构成成本归因结论。</p></section>;
}
export function EvidenceDrawer({value,onClose}:{value:any;onClose:()=>void}) {
 useEffect(()=>{const fn=(e:KeyboardEvent)=>{if(e.key==='Escape')onClose()};document.addEventListener('keydown',fn);return()=>document.removeEventListener('keydown',fn)},[onClose]);
 const sources=value.evidence??(value.source||value.source_file?[value]:[]);
 return <div className="drawer-backdrop" onClick={onClose}><aside className="drawer" role="dialog" aria-modal="true" aria-label="证据与计算口径" onClick={e=>e.stopPropagation()}><div className="panel-heading"><h2>证据与计算口径</h2><button onClick={onClose} autoFocus>关闭</button></div>{value.rendered_text&&<p>{cleanText(value.rendered_text)}</p>}<MetricDetails value={value}/>{value.reason&&<p className="notice">{cleanText(value.reason)}</p>}{value.missing_evidence?.length>0&&<p>待补充：{value.missing_evidence.join('；')}</p>}{sources.map((s:any,i:number)=><div className="evidence-result" key={i}><strong>{sourceLabel(s)}</strong><p>适用产品：{s.products?.join('、')||'待核对'}；{s.applicability?.reason??'需按规格、工厂、期间和文档版本进一步核验。'}</p>{s.supporting_excerpt&&<blockquote>{cleanText(s.supporting_excerpt)}</blockquote>}</div>)}<p className="muted">原始文档与完整检索内容留在机器审计详情中。引用位置存在不等于原因已被证实。</p><DeveloperDetails value={value}/></aside></div>
}