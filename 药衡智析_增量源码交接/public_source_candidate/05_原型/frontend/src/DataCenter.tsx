import { useState } from 'react';
import { api } from './api';

type ImportRecord = any;
const KIND_LABELS: Record<string, string> = { business: '业务数据', knowledge: '知识资料', template: '报告模板' };
const ROLE_OPTIONS = [
  ['', '（不使用）'],
  ['factory_id', '维度：工厂'], ['product_id', '维度：产品'], ['period', '维度：核算期间'],
  ['quantity', '独立产量（每期间一条）'], ['total_cost', '成本合计（总额）'],
  ['element:material', '成本要素：材料'], ['element:labor', '成本要素：人工'], ['element:overhead', '成本要素：制造费用'],
];

async function uploadFile(kind: string, file: File): Promise<ImportRecord> {
  const form = new FormData();
  form.append('kind', kind);
  form.append('file', file);
  const response = await fetch('/api/imports/uploads', { method: 'POST', body: form });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message ?? data?.detail ?? `上传失败（HTTP ${response.status}）`);
  return data;
}

export default function DataCenter() {
  const [kind, setKind] = useState('business');
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [record, setRecord] = useState<ImportRecord | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [mappingName, setMappingName] = useState('');
  const [amountScale, setAmountScale] = useState('1');
  const [validation, setValidation] = useState<any>(null);
  const [publishResult, setPublishResult] = useState<any>(null);
  const [enterpriseName, setEnterpriseName] = useState('');
  const [packId, setPackId] = useState('');
  const [quantityUnit, setQuantityUnit] = useState('件');
  const [packs, setPacks] = useState<any[]>([]);
  const [imports, setImports] = useState<ImportRecord[]>([]);

  const refreshImports = () => api('/imports').then(setImports).catch(() => setImports([]));
  useState(() => { void refreshImports(); api('/industry/catalog').then((x: any) => { setPacks(x.industries ?? x.packs ?? []); const first = (x.industries ?? x.packs ?? [])[0]; if (first) setPackId(first.industry_id ?? first.id ?? ''); }).catch(() => {}); });

  const doUpload = async () => {
    if (!file) { setError('请先选择文件'); return; }
    setBusy(true); setError(''); setValidation(null); setPublishResult(null);
    try {
      const rec = await uploadFile(kind, file);
      setRecord(rec);
      const suggested = rec.meta?.preview?.suggested_mapping ?? {};
      setMapping(suggested);
      if (rec.meta?.preview?.headers?.length) setMappingName('');
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); void refreshImports(); }
  };

  const doValidate = async () => {
    if (!record) return;
    setBusy(true); setError('');
    try {
      const result = await api(`/imports/${record.id}/validate`, { mapping, options: { amount_scale: amountScale } });
      setValidation(result?.meta?.last_validation ?? null);
      if (mappingName) await api(`/imports/${record.id}/mapping`, { mapping, save_as: mappingName });
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };

  const doPublish = async () => {
    if (!record) return;
    setBusy(true); setError('');
    try {
      const result = await api(`/imports/${record.id}/publish`, {
        mapping, options: { amount_scale: amountScale }, enterprise_name: enterpriseName, pack_id: packId, quantity_unit: quantityUnit,
      });
      setPublishResult(result?.meta?.published ?? null);
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); void refreshImports(); }
  };

  const doTemplateCheck = async () => {
    if (!record) return;
    setBusy(true); setError('');
    try {
      const result = await api(`/imports/${record.id}/template-check`);
      setValidation({ template_check: result });
    } catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };

  const headers: string[] = record?.meta?.preview?.headers ?? [];
  const preview = record?.meta?.preview;

  return <div>
    <section className="panel">
      <h2>接入新数据</h2>
      <p className="muted">上传 → 预览与字段映射 → 质量检查 → 能力预览 → 发布。原始文件保留不转码；发布成功后即可在页面上方切换到新企业。</p>
      <div className="filters" style={{ marginBottom: 12 }}>
        <label>数据类型<select value={kind} onChange={e => { setKind(e.target.value); setRecord(null); setValidation(null); }}>
          <option value="business">业务数据（CSV / XLSX）</option>
          <option value="knowledge">知识资料（PDF / DOCX / TXT）</option>
          <option value="template">报告模板（DOCX，仅兼容性检查）</option>
        </select></label>
        <label>选择文件<input type="file" accept=".csv,.xlsx,.pdf,.docx,.txt" onChange={e => setFile(e.target.files?.[0] ?? null)} /></label>
        <button className="primary" disabled={busy || !file} onClick={doUpload}>{busy ? '处理中…' : '上传并预览'}</button>
      </div>
      {error && <div className="error" role="alert">{error}</div>}
    </section>

    {record && kind === 'business' && <section className="panel">
      <h2>字段与口径映射</h2>
      <p className="muted">系统已按常见成本宽表给出建议映射（如「核算期间→期间」「完工数量→产量」）。确认或调整后执行质量检查；映射方案可命名保存，下个月同样表头直接复用。</p>
      <div className="form-grid">
        {headers.map(h => <label key={h}>{h}
          <select value={mapping[h] ?? ''} onChange={e => setMapping(m => ({ ...m, [h]: e.target.value }))}>
            {ROLE_OPTIONS.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
        </label>)}
        <label>金额单位
          <select value={amountScale} onChange={e => setAmountScale(e.target.value)}>
            <option value="1">元</option><option value="10000">万元</option>
          </select>
        </label>
        <label>保存映射方案名（可选）<input value={mappingName} onChange={e => setMappingName(e.target.value)} placeholder="如：标准成本宽表" /></label>
      </div>
      <div className="button-row">
        <button className="primary" disabled={busy} onClick={doValidate}>执行质量检查与能力预览</button>
      </div>
      {preview && <div className="table-scroll" style={{ marginTop: 16 }}>
        <table><thead><tr><th>预览（前 8 行 / 共 {preview.row_count} 行）</th>{preview.sample_rows?.[0]?.map((_: any, i: number) => <th key={i}>列{i + 1}</th>)}</tr></thead>
          <tbody>{(preview.sample_rows ?? []).slice(0, 8).map((row: any, i: number) => <tr key={i}>{headers[i] && <td>{headers[i]}</td>}{row.map((c: any, j: number) => <td key={j}>{c}</td>)}</tr>)}</tbody></table>
      </div>}
    </section>}

    {record && kind === 'business' && validation && <section className="panel">
      <h2>质量检查结果</h2>
      {validation.status === 'VALID'
        ? <p className="badge">检查通过：{validation.statistics?.factories?.length ?? 0} 个工厂 · {validation.statistics?.products?.length ?? 0} 个产品 · {validation.statistics?.periods?.length ?? 0} 个期间</p>
        : <div className="error" role="alert">发现 {validation.error_count} 个错误，请修正文件后重新上传</div>}
      {validation.errors?.length > 0 && <ul>{validation.errors.slice(0, 12).map((e: any, i: number) => <li key={i} style={{ fontSize: 12 }}>{e.file}{e.sheet ? `/${e.sheet}` : ''}{e.row ? ` 第${e.row}行` : ''}：{e.reason}</li>)}</ul>}
      {validation.warnings?.length > 0 && <details><summary>{validation.warnings.length} 条提示</summary><ul>{validation.warnings.slice(0, 10).map((w: string, i: number) => <li key={i} style={{ fontSize: 12 }}>{w}</li>)}</ul></details>}
      {validation.capabilities && <>
        <h3 style={{ margin: '14px 0 8px' }}>能力预览（由数据决定，缺项不乱算）</h3>
        <div className="table-scroll"><table><thead><tr><th>分析能力</th><th>状态</th><th>说明</th></tr></thead><tbody>
          {validation.capabilities.map((c: any) => <tr key={c.capability}><td>{capabilityName(c.capability)}</td><td>{c.available ? <span className="badge">可用</span> : <span className="muted">不可用</span>}</td><td className="muted" style={{ whiteSpace: 'normal' }}>{c.reason}</td></tr>)}
        </tbody></table></div>
      </>}
    </section>}

    {record && kind === 'business' && validation?.status === 'VALID' && <section className="panel">
      <h2>发布为新企业</h2>
      <p className="muted">发布将写入独立数据目录并完成合同校验；现有企业与分析不受影响。发布失败不会破坏现有可用数据。</p>
      <div className="form-grid">
        <label>企业名称<input value={enterpriseName} onChange={e => setEnterpriseName(e.target.value)} placeholder="如：示范工厂C" /></label>
        <label>行业包<select value={packId} onChange={e => setPackId(e.target.value)}>
          {packs.map((p: any) => <option key={p.industry_id ?? p.id} value={p.industry_id ?? p.id}>{p.industry_name ?? p.name ?? p.industry_id ?? p.id}</option>)}
        </select></label>
        <label>产量单位<input value={quantityUnit} onChange={e => setQuantityUnit(e.target.value)} /></label>
      </div>
      <div className="button-row"><button className="primary" disabled={busy || !enterpriseName || !packId} onClick={doPublish}>确认发布</button></div>
      {publishResult && <div className="notice" style={{ marginTop: 12 }}>发布成功：新企业上下文 <strong>{publishResult.context_id}</strong>（{publishResult.dataset_facts} 条事实）。在左上角企业选择器中切换即可分析。</div>}
    </section>}

    {record && kind === 'knowledge' && <KnowledgePanel record={record} />}
    {record && kind === 'template' && <section className="panel">
      <h2>模板兼容性检查</h2>
      <div className="button-row"><button className="primary" disabled={busy} onClick={doTemplateCheck}>检查章节与占位符</button></div>
      {validation?.template_check && <div style={{ marginTop: 12 }}>
        {validation.template_check.compatible ? <p className="badge">兼容：六个固定章节齐全，{validation.template_check.placeholder_count} 个占位符</p> : <div className="error">缺少章节：{(validation.template_check.missing_sections ?? []).join('、') || '章节数不符'}</div>}
        <p className="muted" style={{ whiteSpace: 'normal' }}>{validation.template_check.note}</p>
      </div>}
    </section>}

    <section className="panel">
      <h2>导入历史</h2>
      {imports.length === 0 ? <div className="empty">还没有导入记录</div> : <div className="table-scroll"><table>
        <thead><tr><th>类型</th><th>文件</th><th>大小</th><th>编码</th><th>状态</th><th>时间</th></tr></thead>
        <tbody>{imports.map((r, i) => <tr key={r.id ?? i}><td>{KIND_LABELS[r.kind] ?? r.kind}</td><td>{r.filename}</td><td>{((r.size ?? 0) / 1024).toFixed(1)} KB</td><td>{r.encoding || '—'}</td><td>{r.status}{r.meta?.published ? '（已发布）' : ''}</td><td className="muted">{(r.created ?? '').slice(0, 19).replace('T', ' ')}</td></tr>)}</tbody>
      </table></div>}
    </section>
  </div>;
}

function KnowledgePanel({ record }: { record: ImportRecord }) {
  const [title, setTitle] = useState('');
  const [products, setProducts] = useState('');
  const [factories, setFactories] = useState('');
  const [period, setPeriod] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const publish = async () => {
    setBusy(true); setError('');
    try { setResult(await api(`/imports/${record.id}/publish`, { options: { title, products: products ? products.split(/[,，、\s]+/).filter(Boolean) : [], factories: factories ? factories.split(/[,，、\s]+/).filter(Boolean) : [], period } })); }
    catch (e: any) { setError(e.message ?? String(e)); }
    finally { setBusy(false); }
  };
  return <section className="panel">
    <h2>解析与登记知识资料</h2>
    <p className="muted">直接提取文字建库；扫描件解析后无文本会明确失败（需先 OCR），不会悄悄标记为构建成功。可声明适用产品、工厂与生效期间，检索时据此过滤。</p>
    <div className="form-grid">
      <label>资料标题（可选）<input value={title} onChange={e => setTitle(e.target.value)} placeholder={record.filename} /></label>
      <label>适用产品（逗号分隔，可选）<input value={products} onChange={e => setProducts(e.target.value)} /></label>
      <label>适用工厂（逗号分隔，可选）<input value={factories} onChange={e => setFactories(e.target.value)} /></label>
      <label>生效期间（如 2026-01，可选）<input value={period} onChange={e => setPeriod(e.target.value)} /></label>
    </div>
    <div className="button-row"><button className="primary" disabled={busy} onClick={publish}>解析并登记</button></div>
    {error && <div className="error" style={{ marginTop: 12 }}>{error}</div>}
    {result && <div className="notice" style={{ marginTop: 12 }}>已登记 {result.evidence_id}：{result.pages} 页 / {result.characters} 字（解析成功；进入知识库构建后参与检索）。</div>}
  </section>;
}

const capabilityName = (key: string) => ({
  total_cost_analysis: '总成本分析', unit_cost_analysis: '单位成本分析', mom_comparison: '环比',
  yoy_comparison: '同比', budget_comparison: '预算差异', price_volume_decomposition: '量价分解',
} as Record<string, string>)[key] ?? key;
