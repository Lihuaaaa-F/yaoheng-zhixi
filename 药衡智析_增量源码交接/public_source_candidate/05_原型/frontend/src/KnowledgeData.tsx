import { useState } from 'react';
import ImportWorkflow from './ImportWorkflow';
import Evidence from './Evidence';

/** 数据中心 · 知识库数据：三类知识（产品/行业/企业内部）导入 → 一键
 * “构建知识索引”（解析→分块→词法→向量→验证，全程进度条）+ 检索验证。 */
export default function KnowledgeData({ contextId, product, month, factory, onOpen }: {
  contextId: string; product: string; month: string; factory: string; onOpen: (v: any) => void;
}) {
  const [revision,setRevision]=useState(0);
  return <div>
    <ImportWorkflow
      kind="knowledge"
      onPublished={()=>setRevision(value=>value+1)}
      types={[
        { id: 'product', label: '产品知识', accept: '.pdf,.docx,.txt,.csv', note: '配方、工艺路线等产品文档（PDF/Word/TXT；行情/基准表格可传 CSV）。' },
        { id: 'industry', label: '行业知识', accept: '.pdf,.docx,.txt,.csv', note: '药材行情、GMP 规范、行业基准等外部知识。' },
        { id: 'enterprise', label: '企业内部知识', accept: '.pdf,.docx,.txt,.csv', note: '设备清单、历史异常记录、对标基线等内部资料。' },
      ]}
      parsePath="/kb/build"
      parseBody={() => ({ context_id: contextId })}
      parseLabel="解析知识数据"
      successPrefix="知识库构建成功"
      failPrefix="构建知识库失败"
      listTitle="知识库数据导入列表"
      hint="上传当前数据范围的产品、工艺、规范或内部资料，解析后可在下方检索，并用于分析中的证据引用。"
      processingNotes="系统通过关键词与语义混合检索查找资料（BM25 与向量召回、RRF 融合），并保留来源、页码和位置。文件解析与索引仅绑定当前数据范围。扫描件若无法提取文字会提示失败，请补充带文本的文档后重试。"
      emptyText="暂无待构建的知识文档，请先在上方上传。"
    />
    <Evidence key={`${contextId}:${revision}`} contextId={contextId} product={product} month={month} factory={factory} onOpen={onOpen} />
  </div>;
}
