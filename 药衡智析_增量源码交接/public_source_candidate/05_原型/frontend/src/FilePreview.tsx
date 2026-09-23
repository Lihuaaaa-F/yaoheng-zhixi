import { useEffect, useRef, useState } from 'react';
import { api } from './api';

/** 原始文件预览弹窗：实时预览上传的原始文件；一次只预览一份（打开新文件
 * 自动替换当前内容）。表格显示前 200 行，PDF 走浏览器内嵌原始文件。 */
export default function FilePreview({ importId, onClose }: { importId: string; onClose: () => void }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  // onClose 用 ref 转接、不进 effect 依赖：父组件每次重渲染传入的都是新的
  // 函数引用，此前会让本 effect 反复重跑（清空→重新拉取→闪烁，表现为预览
  // 框周期性闪动）。只有切换 importId 才应重新读取。
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError('');
    api(`/imports/${encodeURIComponent(importId)}/preview`, undefined, controller.signal)
      .then(x => { if (!controller.signal.aborted) setData(x); })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : String(e)); });
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') onCloseRef.current(); };
    window.addEventListener('keydown', onKey);
    return () => { controller.abort(); window.removeEventListener('keydown', onKey); };
  }, [importId]);
  return <div className="drawer-backdrop preview-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label="原始文件预览">
    <div className="drawer preview-panel" onClick={e => e.stopPropagation()}>
      <div className="panel-heading">
        <div><h2>原始文件预览</h2><p className="muted">{data?.filename ?? '…'}{data ? ` · ${(Number(data.size ?? 0) / 1024).toFixed(1)} KB · ${data.suffix ?? ''}` : ''}</p></div>
        <button onClick={onClose}>关闭（Esc）</button>
      </div>
      {error && <div className="error" role="alert">预览失败：{error}</div>}
      {!data && !error && <p role="status">正在读取原始文件…</p>}
      {data?.format === 'table' && <div className="table-scroll"><table>
        <thead><tr>{data.headers?.map((h: string, i: number) => <th key={i}>{h || `列${i + 1}`}</th>)}</tr></thead>
        <tbody>{(data.rows ?? []).map((row: any[], i: number) => <tr key={i}>{row.map((c: any, j: number) => <td key={j}>{String(c)}</td>)}</tr>)}</tbody>
      </table><p className="muted">显示前 {data.rows?.length ?? 0} 行 / 共 {data.row_count} 行</p></div>}
      {data?.format === 'pdf' && <iframe className="preview-pdf" title="PDF 原始文件" src={data.url} />}
      {data?.format === 'docx-text' && <div className="preview-text">{data.paragraphs?.map((p: string, i: number) => <p key={i}>{p}</p>)}
        {(data.tables ?? []).map((t: any, i: number) => <details key={i}><summary>表格 {i + 1}</summary><div className="table-scroll"><table><tbody>{t.rows?.map((r: any[], j: number) => <tr key={j}>{r.map((c: any, k: number) => <td key={k}>{c}</td>)}</tr>)}</tbody></table></div></details>)}
        <p className="muted">共 {data.paragraph_count} 个非空段落（文本抽取预览）</p></div>}
      {(data?.format === 'text') && <pre className="preview-text">{data.text}</pre>}
    </div>
  </div>;
}
