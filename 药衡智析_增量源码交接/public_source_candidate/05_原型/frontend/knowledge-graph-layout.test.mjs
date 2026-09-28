import test from 'node:test';
import assert from 'node:assert/strict';
import { layoutKnowledgeGraph } from './src/knowledgeGraphLayout.ts';

const nodes = [
  {id:'a',type:'product',label:'产品甲'}, {id:'b',type:'product',label:'产品乙'},
  {id:'shared',type:'material',label:'共用原料'}, {id:'isolated',type:'material',label:'独立原料'},
  {id:'first',type:'process',label:'提取'}, {id:'second',type:'process',label:'浓缩'},
];
const edges = [
  {source:'a',target:'shared'}, {source:'b',target:'shared'},
  {source:'a',target:'first',props:{order:0}}, {source:'a',target:'second',props:{order:1}},
  {source:'first',target:'second',relation:'工序顺序'},
];
test('types occupy separate regions without dropping shared or disconnected nodes',()=>{
  const positions=layoutKnowledgeGraph(nodes,edges);
  assert.equal(positions.size,nodes.length);
  const x=type=>nodes.filter(n=>n.type===type).map(n=>positions.get(n.id)[0]);
  assert.ok(Math.max(...x('material'))<Math.min(...x('product')));
  assert.ok(Math.max(...x('product'))<Math.min(...x('process')));
  assert.equal(new Set([...positions.values()].map(p=>p.join(','))).size,nodes.length);
  assert.ok(positions.get('first')[2]>positions.get('second')[2]);
});
test('API order does not change positions or mutate source nodes and edges',()=>{
  const before=JSON.stringify({nodes,edges});
  const a=layoutKnowledgeGraph(nodes,edges),b=layoutKnowledgeGraph([...nodes].reverse(),[...edges].reverse());
  for(const node of nodes)assert.deepEqual(a.get(node.id),b.get(node.id));
  assert.equal(JSON.stringify({nodes,edges}),before);
});
test('empty graphs and additional node types retain finite coordinates',()=>{
  assert.equal(layoutKnowledgeGraph([],[]).size,0);
  const all=[...nodes,{id:'device',type:'equipment',label:'设备'}];
  const positions=layoutKnowledgeGraph(all,edges);
  assert.equal(positions.size,all.length);
  assert.ok([...positions.values()].flat().every(Number.isFinite));
  assert.ok(positions.get('device')[0]>positions.get('first')[0]);
});
test('each populated type is a volumetric cluster rather than a column or plane',()=>{
  const cloudNodes=['material','product','process'].flatMap(type=>Array.from({length:12},(_,i)=>({id:`${type}-${i}`,type,label:`${type}${i}`})));
  const positions=layoutKnowledgeGraph(cloudNodes,[]);
  for(const type of ['material','product','process']){
    const points=cloudNodes.filter(n=>n.type===type).map(n=>positions.get(n.id));
    const spans=[0,1,2].map(axis=>Math.max(...points.map(p=>p[axis]))-Math.min(...points.map(p=>p[axis])));
    assert.ok(Math.min(...spans)/Math.max(...spans)>.5,`${type} must extend in all three dimensions`);
    const [a,b,c,d]=points;
    const u=b.map((v,i)=>v-a[i]),v=c.map((v,i)=>v-a[i]),w=d.map((v,i)=>v-a[i]);
    const volume=Math.abs(u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0]));
    assert.ok(volume>1000,`${type} must not be coplanar`);
  }
  for(const [left,right]of [['material','product'],['product','process']]){
    const xs=type=>cloudNodes.filter(n=>n.type===type).map(n=>positions.get(n.id)[0]);
    assert.ok(Math.max(...xs(left))<Math.min(...xs(right)),'type volumes must remain disjoint');
  }
});
