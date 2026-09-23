import { useEffect, useState } from 'react';
import { api } from './api';
import ImportWorkflow from './ImportWorkflow';

/** 数据中心 · 报告模板：三类模板（月度/季度/专题）导入 → 一键“解析报告模板”
 * （结构检查→占位符语义绑定分析→安装，全程进度条）+ 已安装模板状态。 */
export default function TemplateCenter() {
  const [templates, setTemplates] = useState<any[]>([]);
  const [error, setError] = useState('');
  const load = () => api('/templates').then((x: any) => { setTemplates(x.templates ?? []); setError(''); })
    .catch(e => setError(e instanceof Error ? e.message : String(e)));
  useEffect(() => { void load(); }, []);
  return <div>
    <ImportWorkflow
      kind="template"
      types={[
        { id: 'monthly', label: '月度成本分析', accept: '.docx', note: 'Word 模板：需含六个固定章节（封面/总成本概览/要素明细/重点产品/对标/总结建议）与 {{占位符}}。' },
        { id: 'quarterly', label: '季度成本分析', accept: '.docx', note: '季度报告模板；未安装时沿用月度模板并按季度口径改写。' },
        { id: 'special', label: '专题分析', accept: '.docx', note: '专题分析模板；未安装时沿用月度模板。' },
      ]}
      parsePath="/templates/parse"
      parseLabel="解析报告模板"
      successPrefix="报告模板解析成功"
      failPrefix="报告模板解析失败"
      listTitle="报告模板导入列表"
      hint="报告模板决定 Word/PDF 报告的章节结构与数据占位符。解析将执行模板结构检查（六章节契约）、占位符语义绑定分析（数据分析模型辅助）并安装为对应类型的当前模板。"
      emptyText="暂无待解析的报告模板，请先在上方上传 Word 模板文件。"
      extra={() => <section className="panel" style={{ marginTop: 16 }}>
        <h2>已安装模板</h2>
        {error && <div className="error" role="alert">读取失败：{error}</div>}
        <div className="table-scroll"><table>
          <thead><tr><th>报告类型</th><th>状态</th><th>占位符</th><th>模板文件</th></tr></thead>
          <tbody>{templates.map(t => <tr key={t.analysis_type}>
            <td>{t.label}</td>
            <td>{t.installed ? <span className="badge">已安装</span> : <span className="muted">未安装（回退题包月度模板）</span>}</td>
            <td>{t.installed ? t.placeholder_count : '—'}</td>
            <td className="muted">{t.installed ? t.path : '题包 04_报告模板'}</td>
          </tr>)}</tbody>
        </table></div>
      </section>}
    />
  </div>;
}
