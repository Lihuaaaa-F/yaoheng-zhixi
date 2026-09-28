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
        { id: 'product', label: '产品知识', accept: '.pdf,.docx,.txt,.csv', note: '配方、工艺路线。' },
        { id: 'industry', label: '行业知识', accept: '.pdf,.docx,.txt,.csv', note: '药材行情、GMP 规范、行业基准。' },
        { id: 'enterprise', label: '企业内部知识', accept: '.pdf,.docx,.txt,.csv', note: '设备清单、异常记录、对标基线。' },
      ]}
      parsePath="/kb/build"
      parseBody={() => ({ context_id: contextId })}
      parseLabel="解析知识数据"
      successPrefix="知识库构建成功"
      failPrefix="构建知识库失败"
      listTitle="知识文档"
      hint="支持 PDF、Word、TXT 和 CSV。"
      processingNotes="解析后可检索，引用保留来源位置。仅使用当前工作区资料；扫描件需先转为可提取文字的文档。"
      emptyText="暂无待解析文档"
    />
    <Evidence key={`${contextId}:${revision}`} contextId={contextId} product={product} month={month} factory={factory} onOpen={onOpen} />
  </div>;
}
