import { useEffect, useState } from 'react';
import { api } from './api';
import ImportWorkflow from './ImportWorkflow';
import Evidence from './Evidence';

/** 数据中心 · 知识库数据：三类知识（产品/行业/企业内部）导入 → 一键
 * “构建知识索引”（解析→分块→词法→向量→验证，全程进度条）+ 检索验证。 */
export default function KnowledgeData({ contextId, product, month, factory, onOpen }: {
  contextId: string; product: string; month: string; factory: string; onOpen: (v: any) => void;
}) {
  return <div>
    <ImportWorkflow
      kind="knowledge"
      types={[
        { id: 'product', label: '产品知识', accept: '.pdf,.docx,.txt,.csv', note: '配方、工艺路线等产品文档（PDF/Word/TXT；行情/基准表格可传 CSV）。' },
        { id: 'industry', label: '行业知识', accept: '.pdf,.docx,.txt,.csv', note: '药材行情、GMP 规范、行业基准等外部知识。' },
        { id: 'enterprise', label: '企业内部知识', accept: '.pdf,.docx,.txt,.csv', note: '设备清单、历史异常记录、对标基线等内部资料。' },
      ]}
      parsePath="/kb/build"
      parseLabel="构建知识索引"
      successPrefix="知识库构建成功"
      failPrefix="构建知识库失败"
      listTitle="知识库数据导入列表"
      hint="知识文档入库后参与 RAG 检索（jieba+BM25 词法与本地向量双路召回、RRF 融合，检索结果标注来源）。构建由数据提取/数据分析模型辅助解析、本地向量模型完成向量化；扫描件无文本会显式失败，不会冒充构建成功。"
    />
    <Evidence key={contextId} contextId={contextId} product={product} month={month} factory={factory} onOpen={onOpen} />
  </div>;
}
