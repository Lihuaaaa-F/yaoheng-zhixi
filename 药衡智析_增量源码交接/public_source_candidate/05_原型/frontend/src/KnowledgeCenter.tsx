import { useState } from 'react';
import { api } from './api';
import Evidence from './Evidence';

/** 知识中心：知识库状态与构建 + 现有证据浏览（检索/适用范围核对）。 */
export default function KnowledgeCenter({ contextId, product, month, factory, onOpen }: {
  contextId: string; product: string; month: string; factory: string; onOpen: (v: any) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState('');
  const build = async () => {
    setBusy(true); setError('');
    try { setStatus(await api('/kb/build')); } catch (e: any) { setError(e.message); }
    finally { setBusy(false); }
  };
  return <div>
    <section className="panel">
      <h2>知识库</h2>
      <p className="muted">知识资料经数据中心上传并解析登记后，在此重建索引。解析失败的文件不会计入“已构建成功”；扫描件请先 OCR。</p>
      <div className="button-row">
        <button className="primary" disabled={busy} onClick={build}>{busy ? '提交中…' : '重建知识索引'}</button>
      </div>
      {status?.job_id && <p className="badge" style={{ marginTop: 10 }}>已提交构建任务 {status.job_id.slice(0, 8)}；进度见「报告与整改」任务列表。</p>}
      {error && <div className="error" style={{ marginTop: 10 }}>{error}</div>}
    </section>
    <Evidence key={contextId} contextId={contextId} product={product} month={month} factory={factory} onOpen={onOpen} />
  </div>;
}
