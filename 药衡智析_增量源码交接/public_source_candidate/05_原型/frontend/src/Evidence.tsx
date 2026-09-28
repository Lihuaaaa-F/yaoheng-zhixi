import { Suspense, lazy, useState, useEffect, useRef, useMemo } from 'react';
import { api, contextQuery, openApiFile } from './api';
import { Drawer, Button, Alert, Tooltip } from 'antd';
import { FileTextOutlined, LinkOutlined, QuestionCircleOutlined, ReloadOutlined, FullscreenOutlined, FullscreenExitOutlined } from '@ant-design/icons';
import { cleanText, sourceLabel, MetricDetails } from './presentation';
import { layoutKnowledgeGraph, NODE_TYPES } from './knowledgeGraphLayout';
// 2026-09-23 审查 SSE-2：Chart3D（echarts-gl 栈）改为动态加载——知识图谱仅在
// 证据抽屉渲染时才需要，静态引入会把约 497KB GL 依赖拖进首屏。
const Chart3D = lazy(() => import('./Chart3D'));
export default function Evidence({ contextId, product, month, factory, onOpen }: {contextId:string;product:string; month?:string; factory?:string; onOpen:(v:any)=>void}) {
 const searchController=useRef<AbortController|undefined>(undefined);
 const [graphOpen,setGraphOpen]=useState(()=>new URLSearchParams(window.location.search).get('graph')==='1');
 const [query,setQuery]=useState('设备停机记录'),[mode,setMode]=useState('hybrid'),[results,setResults]=useState<any>(null),[status,setStatus]=useState<any>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{const c=new AbortController();api(`/kb?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setStatus(x)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[contextId]);
 useEffect(()=>{searchController.current?.abort();setResults(null);setBusy(false);return()=>searchController.current?.abort()},[contextId,product,month,factory]);
 async function search(){searchController.current?.abort();const c=new AbortController();searchController.current=c;setBusy(true);setError('');try{const response=await api('/kb/search',{query,product,month,factory,mode,context_id:contextId},c.signal);if(!c.signal.aborted)setResults(response)}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:String(e))}finally{if(!c.signal.aborted)setBusy(false)}}
 const hits=Array.isArray(results)?results:results?.evidence??results?.results??results?.hits??[];
 return <>
  <section className="panel">
   <div className="panel-heading"><h2>知识检索</h2>{status&&<span className="kb-status" role="status">
    {Object.keys(status.sources??{}).length} 份来源 · {status.chunks??0} 个片段
    <span className={status.status==='PASS'||status.status==='READY'?'outline-label':'outline-label increase'}>{status.status==='PASS'||status.status==='READY'?'索引可用':'索引需检查'}</span>
   </span>}</div>
   <form className="search-row" onSubmit={e=>{e.preventDefault();void search()}}>
    <input aria-label="知识检索问题" value={query} onChange={e=>setQuery(e.target.value)} placeholder="搜索工艺、原料或设备"/>
    <select aria-label="检索方式" value={mode} onChange={e=>setMode(e.target.value)}><option value="hybrid">混合检索</option><option value="bm25">关键词</option><option value="vector">语义检索</option></select>
    <button className="primary" disabled={busy||!query.trim()}>{busy?'检索中…':'检索证据'}</button>
   </form>
   <p className="muted">{[product,factory,month].filter(Boolean).join(' · ')}</p>
   {error&&<p role="alert" className="error">{error}</p>}
   {results&&<p role="status">{hits.length} 条结果{results.degraded_reason?' · 检索已降级':''}</p>}
   {results?.degraded_reason&&<p className="notice">{cleanText(results.degraded_reason)}</p>}
   {results&&!hits.length&&<p className="empty">未找到适用记录，请补充相关产品或期间的资料。</p>}
   {hits.map((h:any,i:number)=><article className="evidence-result" key={h.evidence_id??i}>
    <strong>{sourceLabel(h)}</strong><p>{h.products?.join('、')||h.scope_label||'产品适用性待核对'}{h.applicability?.reason?` · ${h.applicability.reason}`:''}</p>
    <button onClick={()=>onOpen(h)}>查看来源与适用性</button>
   </article>)}
   {results&&hits.length>0&&<p className="muted">文档支持原因假设，仍需核对本期生产记录。</p>}
  </section>
  <details className="panel kg-disclosure" open={graphOpen} onToggle={e=>setGraphOpen(e.currentTarget.open)}>
   <summary>配方与工艺图谱</summary>{graphOpen&&<KnowledgeGraphPanel contextId={contextId}/>}
  </details>
 </>
}

// 知识图谱面板（赛题加分项）：产品-药材-工序关系三维可视化。
// 2026-09-22 改版：graphGL（正交相机+2D roam，无真三维旋转）→ scatter3D 节点
// + lines3D 边 + grid3D 轨道相机——左键拖拽真三维旋转、滚轮缩放、右键平移，
// 悬停显示节点/关系说明，支持对 21 节点/27 边结构做视觉分析。
function KnowledgeGraphPanel({contextId}:{contextId:string}) {
 const [graph,setGraph]=useState<any>(null);
 const [fullscreen,setFullscreen]=useState(false);
 const [viewKey,setViewKey]=useState(0);
 const [chartWidth,setChartWidth]=useState(800);
 const [hoverInfo,setHoverInfo]=useState<{text:string;x:number;y:number}|null>(null);
 const chartDomRef=useRef<HTMLDivElement|null>(null);
 const sectionRef=useRef<HTMLElement|null>(null);
 // 真·全屏（Fullscreen API）：双击图谱或右上角按钮进入/退出，Esc 原生可退
 // （2026-09-24 用户要求全屏交互；此前是 CSS 仿全屏，会被页头遮挡且不遮挡
 // 页面其余内容）。fullscreenchange 统一回写状态——按钮、高度都跟随。
 useEffect(()=>{const onFs=()=>setFullscreen(document.fullscreenElement===sectionRef.current);
  document.addEventListener('fullscreenchange',onFs);return()=>document.removeEventListener('fullscreenchange',onFs)},[]);
 const toggleFullscreen=()=>{
  const el=sectionRef.current;if(!el)return;
  if(document.fullscreenElement){document.exitFullscreen().catch(()=>{})}
  else if(el.requestFullscreen){el.requestFullscreen().catch(()=>{})}
 };
 useEffect(()=>{const c=new AbortController();setGraph(null);api(`/kb/graph?${contextQuery(contextId)}`,undefined,c.signal).then(x=>{if(!c.signal.aborted)setGraph(x)}).catch(()=>{if(!c.signal.aborted)setGraph({status:'FAILED',reason:'图谱加载失败，请刷新重试。'})});return()=>c.abort()},[contextId]);
 useEffect(()=>{
  const el=chartDomRef.current;if(!el)return;
  const observer=new ResizeObserver(([entry])=>setChartWidth(entry.contentRect.width));
  observer.observe(el);return()=>observer.disconnect();
 },[graph]);
 const posById=useMemo(()=>layoutKnowledgeGraph(graph?.nodes??[],graph?.edges??[]),[graph]);
 if(!graph)return <p className="muted" role="status">正在加载图谱…</p>;
 if(graph.status!=='PASS')return <section className="panel"><h2>知识图谱</h2><p className="notice">{graph.reason??'当前知识源未解析出配方或工艺结构，图谱为空。'}</p></section>;
 const compact=chartWidth<500;
 const height=fullscreen?Math.max(360,window.innerHeight-160):(compact?440:560);
 // 按画布宽高比留出三类节点及标签的可见空间。
 const cameraDistance=Math.max(350,345*height/Math.max(chartWidth,1));
 const labelById=new Map(graph.nodes.map((n:any)=>[n.id,n.label]));
 const nodeData=graph.nodes.filter((n:any)=>posById.has(n.id)).map((n:any)=>{
   const meta=NODE_TYPES.find(t=>t.type===n.type)??{color:'#64748b',label:n.type};
   const [x,y,z]=posById.get(n.id)!;
   return {name:n.label,value:[x,y,z],
     itemStyle:{color:meta.color,opacity:.95,borderColor:'#fff',borderWidth:1},
     symbolSize:n.type==='product'?25:15,
     label:{show:!compact||n.type==='product'},
     tooltip_kind:meta.label};
 });
 // lines3D 的布局器不支持 cartesian3D（只支持 globe/geo3D/mapbox），改用
 // scatter3D 密集采样点渲染边：所有边的插值点合并进单一系列（减少 drawcall，
 // 27 边×41 点≈1100 符号，单系列渲染开销可控）。
 const SAMPLES=40;
 const edgePoints:any[]=[];
 for(const e of graph.edges){
   if(!posById.has(e.source)||!posById.has(e.target))continue;
   const a=posById.get(e.source)!,b=posById.get(e.target)!;
   const label=`${labelById.get(e.source)??e.source} —${e.relation||e.value||'相关'}→ ${labelById.get(e.target)??e.target}`;
   for(let i=0;i<=SAMPLES;i++){
     const t=i/SAMPLES;
     edgePoints.push({value:[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,a[2]+(b[2]-a[2])*t],
       name:label,tooltip_kind:'边'});
   }
 }
 const edgeSeriesOption={type:'scatter3D',coordinateSystem:'cartesian3D',
   data:edgePoints,symbolSize:1.8,
   itemStyle:{color:'#91a7b5',opacity:.45}};
 return <section ref={sectionRef} className={`panel${fullscreen?' kg-fullscreen':''}`}>
  <div className="panel-heading"><h2>知识图谱</h2>
   <div className="button-row">
    <Tooltip title="左键旋转 · 滚轮缩放 · 按住中键平移 · 双击全屏" trigger={['hover','focus','click']}><Button type="text" aria-label="图谱操作说明" icon={<QuestionCircleOutlined/>}/></Tooltip>
    <Button aria-label="重置图谱视角" icon={<ReloadOutlined/>} onClick={()=>{setHoverInfo(null);setViewKey(k=>k+1)}}>重置</Button>
    <Button aria-label={fullscreen?'退出全屏':'全屏'} icon={fullscreen?<FullscreenExitOutlined/>:<FullscreenOutlined/>} onClick={toggleFullscreen}>{fullscreen?'退出全屏':'全屏'}</Button></div></div>
  <div className="kg-legend" role="list" aria-label="节点类型图例">
    {NODE_TYPES.map(t=><span key={t.type} role="listitem"><i style={{background:t.color}}/>{t.label}<b>{graph.nodes.filter((n:any)=>n.type===t.type).length}</b></span>)}
  </div>
  <div ref={chartDomRef} style={{position:'relative'}} onDoubleClick={toggleFullscreen}>
  <Suspense fallback={<p className="muted" role="status">三维图谱组件加载中…</p>}>
  <Chart3D key={viewKey} label="知识图谱三维视图" height={height}
   onHover={(info:any)=>setHoverInfo(info)} option={{
    tooltip:{renderMode:'richText',formatter:(p:any)=>{
      const label=p.data?.name||p.name||'';
      if(p.data?.tooltip_kind==='边')return label;
      return `${label}（${p.data?.tooltip_kind??''}）`;
    }},
    legend:{show:false},
    series:[
      edgeSeriesOption,
      {type:'scatter3D',coordinateSystem:'cartesian3D',data:nodeData,
       tooltip:{show:true,renderMode:'richText',formatter:(p:any)=>`${p.name}（${p.data?.tooltip_kind??''}）`},
       label:{show:true,formatter:(p:any)=>p.name,position:compact?'bottom':'right',distance:compact?3:1,
         textStyle:{fontSize:compact?10:12,color:'#28414d',fontWeight:400,
           textBorderColor:'#ffffff',textBorderWidth:3,textBorderType:'solid'}},
       emphasis:{label:{show:true,fontSize:15,fontWeight:600,
         textBorderColor:'#ffffff',textBorderWidth:3}}},
    ],
    xAxis3D:{show:false,min:Math.min(-580,...Array.from(posById.values(),p=>p[0]-100)),max:Math.max(580,...Array.from(posById.values(),p=>p[0]+100))},
    yAxis3D:{show:false,min:-420,max:420},zAxis3D:{show:false,min:-420,max:420},
    grid3D:{
      // Keep all three world axes at the same scale: no flattened depth axis.
      show:false,boxWidth:(Math.max(580,...Array.from(posById.values(),p=>p[0]+100))-Math.min(-580,...Array.from(posById.values(),p=>p[0]-100)))/4,boxHeight:210,boxDepth:210,
      viewControl:{alpha:12,beta:-10,distance:cameraDistance,minDistance:100,maxDistance:Math.max(1000,cameraDistance*2),
        // OrbitControl divides dx by height and dy by width. Compensate both
        // so equal pixel drags produce equal angles, including fullscreen.
        rotateSensitivity:[4.2*height/560,4.2*chartWidth/560],
        // The existing perspective camera has a 50-degree vertical field of view.
        // Compensating its projection makes panning track CSS pixels.
        zoomSensitivity:2.2,panSensitivity:[Math.tan(25*Math.PI/180)*chartWidth/height,Math.tan(25*Math.PI/180)],damping:.6,
        rotateMouseButton:'left',panMouseButton:'middle',minAlpha:-89,maxAlpha:89,
        autoRotate:false},
      light:{main:{intensity:1.1,shadow:false},ambient:{intensity:.5}},
      axisLine:{show:false},axisLabel:{show:false},splitLine:{show:false},
      axisPointer:{show:false},
    }}}/>
    </Suspense>
    {hoverInfo && <div className="kg-tooltip" style={{left:hoverInfo.x, top:hoverInfo.y}}>{hoverInfo.text}</div>}
  </div>
  <p className="muted kg-caption">{graph.edges.length} 条配方与工艺关系 · 不代表成本变化的已证实原因</p></section>;
}
export function EvidenceDrawer({value,onClose}:{value:any;onClose:()=>void}) {
 const [error,setError]=useState('');
 const sources=Array.isArray(value.evidence)?value.evidence:Array.isArray(value.sources)?value.sources:value.evidence?.evidence??(value.source||value.source_file||value.title||value.text?[value]:[]);
 const quotes=value.evidence_quotes??{};
 const openSource=async(source:any)=>{setError('');try{await openApiFile(`/api/kb/sources/${encodeURIComponent(source.source_id)}?context_id=${encodeURIComponent(value.context_id??source.context_id??'')}`,undefined,source.page)}catch(e:any){setError(e.message)}};
 return <Drawer className="evidence-drawer" title={<><FileTextOutlined /> 证据与计算口径</>} open onClose={onClose} size={560}>
  {value.rendered_text&&<p className="evidence-heading">{cleanText(value.rendered_text)}</p>}
  <MetricDetails value={value}/>
  {value.reason&&<Alert type="info" showIcon title={cleanText(value.reason)}/>}
  {value.missing_evidence?.length>0&&<Alert type="warning" showIcon title="仍需补充的证据" description={Array.isArray(value.missing_evidence)?value.missing_evidence.join('；'):value.missing_evidence}/>}
  {error&&<Alert type="error" showIcon title={error}/>}
  {!sources.length&&value.value===undefined&&<div className="evidence-none">
    <p>{value.claim_type==='numeric_fact'
      ?'本项由业务数据计算，口径与来源见上方。'
      :'当前结论没有可展示的文档证据，请补充资料后核查。'}</p>
    {value.claim_type==='recommendation'&&<p className="muted">规则建议，进展可在“问题整改”查看。</p>}
  </div>}
  {sources.map((source:any,index:number)=>{
   const quote=quotes[source.evidence_id]??source.supporting_excerpt;
   const excerpt=source.text??source.excerpt??source.content;
   return <article className="evidence-result" key={source.evidence_id??source.source_id??index}>
    <strong>{sourceLabel(source)}</strong>
    <p className="evidence-location">适用范围：{source.products?.join('、')||source.product||source.scope_label||'需结合当前产品核对'}{source.factory?` · ${source.factory}`:''}{source.document_version?` · 版本 ${source.document_version}`:''}</p>
    {quote&&<><span className="muted">结论引用</span><blockquote>{cleanText(quote)}</blockquote></>}
    {excerpt&&(!quote||cleanText(quote)!==cleanText(excerpt))&&<><span className="muted">来源摘录</span><blockquote>{cleanText(excerpt)}</blockquote></>}
    {!quote&&!excerpt&&<p className="notice">本条记录缺少可读摘录，请打开原件核查。</p>}
    {source.applicability?.reason&&<p className="muted">{source.applicability.reason}</p>}
    {source.source_id&&<Button size="small" icon={<LinkOutlined/>} className="source-actions" onClick={()=>openSource(source)}>打开原始文档{source.page?`（第 ${source.page} 页）`:''}</Button>}
   </article>;
  })}
  <p className="muted">引用前请核对产品、工厂、期间与生产记录。</p>
 </Drawer>;
}
