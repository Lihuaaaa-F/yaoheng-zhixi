import ImportWorkflow from './ImportWorkflow';

/** 数据中心 · 业务数据：五类成本数据导入 → 列表等待 → 一键“解析数据”
 * （预处理→智能字段映射→质检→指标→归因分析→发布，全程进度条）。 */
export default function BusinessData({ onPublished }: { onPublished?: (value: any) => void }) {
  return <ImportWorkflow
    kind="business"
    onPublished={onPublished}
    types={[
      { id: 'cost_summary', label: '成本汇总数据', accept: '.csv,.xlsx', note: '请提供产量、直接材料、直接人工、制造费用，以及产品、工厂和月份。' },
      { id: 'material_detail', label: '原材料消耗明细', accept: '.csv,.xlsx', note: '按原材料名称逐行记录的材料消耗（按要素归集到材料口径）。' },
      { id: 'manufacturing_detail', label: '制造费用明细', accept: '.csv,.xlsx', note: '按费用类别的制造费用明细（按要素归集到制造费用口径）。' },
      { id: 'labor_detail', label: '人工工时明细', accept: '.csv,.xlsx', note: '直接人工与工时记录（人工要素按期间归集）。' },
      { id: 'budget', label: '预算数据', accept: '.csv,.xlsx', note: '预算口径的成本与产量（启用预算差异分析）。' },
    ]}
    parsePath="/data/parse"
    parseLabel="解析数据"
    successPrefix="数据处理成功"
    failPrefix="数据处理失败"
    listTitle="业务数据导入列表"
    hint="上传同一企业的成本汇总、明细或预算表（CSV / XLSX），再统一解析。发布成功后自动进入成本分析。"
    processingNotes="原始文件保留不转码；解析包含预处理、字段映射、质量检查和分析。模型可辅助字段映射与原因假设，未配置模型时使用规则处理。全部已接入文件与本次上传统一校验，重复记录去重，冲突会提示修正；资料不足不补零，汇总与明细不重复计入。"
  />;
}
