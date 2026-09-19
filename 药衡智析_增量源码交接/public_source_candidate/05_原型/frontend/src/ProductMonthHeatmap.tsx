import {useEffect,useState} from 'react';
import Chart from './Chart';
import {api,Selection} from './api';
import {displayNumber} from './presentation';

type Cell={product:string;month:string;status:string;reason?:string;values:Record<string,{value:string|null;unit:string;reason?:string}>};
export default function ProductMonthHeatmap({selection,onSelect}:{selection:Selection;onSelect:(product:string,month:string)=>void}){
 const [expanded,setExpanded]=useState(false);
 const [grid,setGrid]=useState<any>(null),[element,setElement]=useState('all'),[error,setError]=useState('');
 useEffect(()=>{const c=new AbortController();setGrid(null);setError('');const p=new URLSearchParams({context_id:selection.context_id,factory:selection.factory,month:selection.month,basis:selection.basis});api(`/dashboard/heatmap?${p}`,undefined,c.signal).then(x=>{if(!Array.isArray(x.cells)||!Array.isArray(x.elements))throw new Error('产品月份数据不完整');if(!c.signal.aborted)setGrid(x)}).catch(e=>{if(!c.signal.aborted)setError(e.message)});return()=>c.abort()},[selection.context_id,selection.factory,selection.month,selection.basis]);
 const selectedElement=grid?.elements.some((e:any)=>e.key===element)?element:'all';
 const cells:Cell[]=grid?.cells??[],products:string[]=grid?.products??[],months:string[]=grid?.months??[];
 const available=(c:Cell)=>c.status==='AVAILABLE'&&c.values[selectedElement]?.value!=null&&Number.isFinite(Number(c.values[selectedElement].value));
 const text=(c:Cell)=>available(c)?`${c.values[selectedElement].value} ${c.values[selectedElement].unit}`:`缺失：${c.reason??c.values[selectedElement]?.reason??'该要素未提供'}`;
 const units=[...new Set(cells.filter(available).map(c=>c.values[selectedElement].unit))];
 // Different physical units never share one color scale.
 const comparableUnits=units.length<=1;
 const data=cells.filter(available).map(c=>({value:[months.indexOf(c.month),products.indexOf(c.product),Number(c.values[selectedElement].value)],cell:c}));
 const values=data.map(d=>d.value[2]);
 const pick=(c:Cell)=>{if(available(c))onSelect(c.product,c.month)};
 return <section className="panel"><div className="panel-heading"><h2>产品 × 月份成本热力图</h2><label>成本要素<select aria-label="热力图成本要素" value={selectedElement} onChange={e=>setElement(e.target.value)}>{(grid?.elements??[{key:'all',name:'全部成本'}]).map((e:any)=><option key={e.key} value={e.key}>{e.name}</option>)}</select></label></div><p className="muted">{selection.factory} · {selection.basis==='unit'?'单位成本':'总成本'}口径（上方可切换） · 近六个自然月。点击网格或精确值切换产品与月度分析；缺失保持空格。图内最多显示四位小数，悬浮提示和下表保留精确值。</p>{error&&<p className="error" role="alert">热力图读取失败：{error}</p>}{!grid&&!error&&<p role="status">正在读取产品月度成本…</p>}{grid&&<>{comparableUnits?<Chart label="产品月份成本热力图" onClick={(event:any)=>{if(event.data?.cell)pick(event.data.cell)}} option={{tooltip:{renderMode:'richText',formatter:(p:any)=>`${p.data.cell.product} · ${p.data.cell.month}\n${text(p.data.cell)}`},grid:{left:125,right:35,top:20,bottom:90},xAxis:{type:'category',data:months,splitArea:{show:true}},yAxis:{type:'category',data:products,splitArea:{show:true}},visualMap:{min:Math.min(...values,0),max:Math.max(...values,1),orient:'horizontal',left:'center',bottom:5,inRange:{color:['#eaf2f2','#729bc2','#227c81']}},series:[{type:'heatmap',data,label:{show:true,formatter:(p:any)=>displayNumber(p.data.cell.values[selectedElement].value)}}]}}/>:<p className="notice">各产品单位不一致，不能共用颜色刻度，请用下方精确值逐项比较。</p>}<details open={expanded} onToggle={event=>setExpanded(event.currentTarget.open)}><summary>查看产品月份精确值与缺失状态</summary><div className="table-scroll"><table><thead><tr><th>产品</th>{months.map(month=><th key={month}>{month}</th>)}</tr></thead><tbody>{products.map(product=><tr key={product}><th>{product}</th>{months.map(month=>{const cell=cells.find(c=>c.product===product&&c.month===month);return <td key={month}>{cell&&available(cell)?<button aria-label={`${product} ${month} ${text(cell)}`} onClick={()=>pick(cell)}>{text(cell)}</button>:<span>{cell?text(cell):'缺失'}</span>}</td>})}</tr>)}</tbody></table></div></details></>}</section>
}
