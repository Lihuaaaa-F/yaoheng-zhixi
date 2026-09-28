export type GraphNode = { id: string; type: string; label: string };
export type GraphEdge = { source: string; target: string; relation?: string; props?: { order?: number } };
export type GraphPosition = [number, number, number];

export const NODE_TYPES = [
  { type: 'material', label: '原料', color: '#b87931' },
  { type: 'product', label: '产品', color: '#087f88' },
  { type: 'process', label: '工序', color: '#8f5b7a' },
];

/** Display coordinates only: disjoint type regions, stable across API ordering.
 * Shared and disconnected nodes each retain their own identity. Nothing is
 * inferred about cost causality or added to the source relationships.
 */
export function layoutKnowledgeGraph(nodes: GraphNode[], edges: GraphEdge[]) {
  const types = [...NODE_TYPES.map(n => n.type), ...Array.from(new Set(nodes.map(n => n.type)))
    .filter(type => !NODE_TYPES.some(n => n.type === type)).sort()];
  const products = new Set(nodes.filter(n => n.type === 'product').map(n => n.id));
  const owners = new Map<string, string[]>();
  const order = new Map<string, number>();
  for (const edge of edges) {
    const owner = products.has(edge.source) ? edge.source : products.has(edge.target) ? edge.target : null;
    if (!owner) continue;
    const child = edge.source === owner ? edge.target : edge.source;
    owners.set(child, [...(owners.get(child) ?? []), owner]);
    if (Number.isFinite(edge.props?.order)) order.set(child, Math.min(order.get(child) ?? Infinity, edge.props!.order!));
  }
  const ownerKey = (id: string) => (owners.get(id) ?? []).slice().sort().join('|');
  const positions = new Map<string, GraphPosition>();
  types.forEach((type, groupIndex) => {
    const members = nodes.filter(node => node.type === type).slice().sort((a, b) =>
      ownerKey(a.id).localeCompare(ownerKey(b.id), 'zh-CN') ||
      (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0) || a.id.localeCompare(b.id, 'zh-CN'));
    // Separate cloud centres in all axes. Each cloud stays within its own
    // x region, while a spherical distribution supplies real depth within it.
    const center: GraphPosition = [
      (groupIndex - (types.length - 1) / 2) * 360,
      groupIndex % 2 === 0 ? -140 : 180,
      [90, 220, -170][groupIndex % 3],
    ];
    const radius = type === 'product' ? 130 : 190;
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));
    members.forEach((node, index) => {
      if (members.length === 1) { positions.set(node.id, [...center]); return; }
      const vertical = 1 - 2 * (index + .5) / members.length;
      const ring = Math.sqrt(1 - vertical * vertical);
      const angle = index * goldenAngle + groupIndex * .8;
      // Alternating inner/outer shells avoid putting every node on a surface.
      const shell = .78 + (index % 3) * .11;
      positions.set(node.id, [
        center[0] + radius * ring * Math.cos(angle) * shell,
        center[1] + radius * ring * Math.sin(angle) * shell,
        center[2] + radius * vertical,
      ]);
    });
  });
  return positions;
}
