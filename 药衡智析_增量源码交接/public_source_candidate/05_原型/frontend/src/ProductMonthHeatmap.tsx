import {useEffect,useState} from 'react';
import Chart from './Chart';
import {api,Selection} from './api';
import {displayNumber} from './presentation';

type Cell={product:string;month:string;status:string;reason?:string;values:Record<string,{value:string|null;unit:string;reason?:string}>};
type Row={elementKey:string;elementName:string;product:string;label:string};

// 产品 × 月份 × 成本要素三维交叉热力图（2026-09-23 审计 AUD-M2-10 修复）：
// y 轴 = 要素×产品组合行，单图同时呈现三维交叉（此前为要素下拉切换的二维实现）。
// 色阶跨要素全局统一，数量级差异读格内数值；缺失保持空格；点击格切换分析对象。
export default function ProductMonthHeatmap({selection,onSelect}:{selection:Selection;onSelect:(product:string,month:string)=>void}){
 const [expanded,setExpanded]=useState(false);
 const [grid,setGrid]=useState<any>(null),[error,setError]=useState('');
 useEffect(()=>{const c=new AbortController();setGrid(null);setError('');const p=new URLSearchParams({context_id:selection.context_id,factory:selection.factory,month:selection.month,basis:selection.basis});api(`/dashboard/heatmap?${p}`,undefined,c.signal).then(x=>{if(!Array.isArray(x.cells)||!Array.isArray(x.elements))throw new Error('产品月份数据不完整');if(!c.signal.aborted)setGrid(x)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[selection.context_id,selection.factory,selection.month,selection.basis]);
 const cells:Cell[]=grid?.cells??[],products:string[]=grid?.products??[],months:string[]=grid?.months??[];
 const elements:{key:string;name:string}[]=grid?.elements?.length?grid?.elements:[{key:'all',name:'全部成本'}];
 const cellOf=(product:string,month:string)=>cells.find(c=>c.product===product&&c.month===month);
 const valueOf=(cell:Cell|undefined,key:string)=>cell&&cell.status==='AVAILABLE'&&cell.values[key]?.value!=null&&Number.isFinite(Number(cell.values[key].value))?Number(cell.values[key].value):null;
 const unitOf=(key:string)=>{for(const c of cells){const v=c.values[key];if(v?.unit)return v.unit}return ''};
 const rows:Row[]=elements.flatMap(el=>products.map(p=>({elementKey:el.key,elementName:el.name,product:p,label:`${el.name}·${p}`})));
 const points=rows.flatMap((row,y)=>months.map((month,x)=>{const cell=cellOf(row.product,month);const v=valueOf(cell,row.elementKey);return v===null?null:{value:[x,y,v] as [number,number,number],row,cell}})).filter((d):d is {value:[number,number,number];row:Row;cell:Cell|undefined}=>d!==null);
 const values=points.map(d=>d.value[2]);
 const pick=(product:string,month:string)=>{const cell=cellOf(product,month);if(cell&&cell.status==='AVAILABLE')onSelect(product,month)};
 const unit=unitOf(elements[0]?.key??'all');
 const chartHeight=Math.max(240,rows.length*34+150);
 const textOf=(cell:Cell|undefined,key:string)=>{const v=cell?.values[key];return v?.value!=null?`${v.value} ${v.unit}`:`缺失：${cell?.reason??v?.reason??'该要素未提供'}`};
 return <section className="panel"><div className="panel-heading"><h2>产品 × 月份 × 成本要素 热力图</h2></div><p className="muted">{selection.factory} · {selection.basis==='unit'?'单位成本':'总成本'}口径（上方可切换） · 近六个自然月 · 每要素每产品一行：三维交叉单图。色阶全局统一，跨要素数量级差异请读格内数值（最多四位小数）；缺失保持空格；点击任意数值格切换该产品与月度分析。</p>{error&&<p className="error" role="alert">热力图读取失败：{error}</p>}{!grid&&!error&&<p role="status">正在读取产品月度成本…</p>}{grid&&<>{points.length?<>
 {unit&&<p className="muted">数值单位：{unit}。</p>}
 <div className="heatmap-3d"><Chart label="产品月份成本要素三维交叉热力图" onClick={(event:any)=>{if(event.data?.row&&event.value)pick(event.data.row.product,months[event.value[0]]??selection.month)}} option={{tooltip:{renderMode:'richText',formatter:(p:any)=>`${p.data.row.label} · ${months[p.value[0]]}\n${textOf(p.data.cell,p.data.row.elementKey)}`},grid:{left:150,right:35,top:20,bottom:90},xAxis:{type:'category',data:months,splitArea:{show:true}},yAxis:{type:'category',data:rows.map(r=>r.label),splitArea:{show:true}},visualMap:{min:Math.min(...values,0),max:Math.max(...values,1),orient:'horizontal',left:'center',bottom:5,text:[displayNumber(Math.max(...values,1)),displayNumber(Math.min(...values,0))],inRange:{color:['#eaf2f2','#729bc2','#227c81']}},series:[{type:'heatmap',data:points,label:{show:true,fontSize:10,formatter:(p:any)=>displayNumber(p.data.value[2])}}]}}/></div>
 <style>{`.heatmap-3d .chart{height:${chartHeight}px}`}</style>
 </>:<p className="empty">当前口径没有可交叉展示的产品×月份×要素数值。</p>}
 <details open={expanded} onToggle={event=>setExpanded(event.currentTarget.open)}><summary>查看产品月份各要素精确值与缺失状态</summary><div className="table-scroll"><table><thead><tr><th>产品</th><th>要素</th>{months.map(month=><th key={month}>{month}</th>)}</tr></thead><tbody>{products.flatMap(product=>elements.map(el=>{const hasAny=months.some(m=>{const c=cellOf(product,m);return c?.status==='AVAILABLE'&&c.values[el.key]});if(!hasAny)return null;return <tr key={`${product}:${el.key}`}><th>{product}</th><th>{el.name}</th>{months.map(month=>{const cell=cellOf(product,month);const v=cell?.values[el.key];const active=cell&&cell.status==='AVAILABLE'&&v?.value!=null;return <td key={month}>{active?<button aria-label={`${product} ${el.name} ${month} ${textOf(cell,el.key)}`} onClick={()=>pick(product,month)}>{textOf(cell,el.key)}</button>:<span>{cell?textOf(cell,el.key):'缺失'}</span>}</td>})}</tr>}))}</tbody></table></div></details></>}</section>;
}
