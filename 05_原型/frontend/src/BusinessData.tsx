import ImportWorkflow from './ImportWorkflow';

/** 数据中心 · 业务数据：五类成本数据导入 → 列表等待 → 一键“解析数据”
 * （预处理→智能字段映射→质检→指标→归因分析→发布，全程进度条）。 */
export default function BusinessData({ onPublished }: { onPublished?: (value: any) => void }) {
  return <ImportWorkflow
    kind="business"
    onPublished={onPublished}
    types={[
      { id: 'cost_summary', label: '成本汇总数据', accept: '.csv,.xlsx', note: '必需：产品、工厂、月份、产量及材料、人工、制造费用。' },
      { id: 'material_detail', label: '原材料消耗明细', accept: '.csv,.xlsx', note: '按原料逐行记录消耗与成本。' },
      { id: 'manufacturing_detail', label: '制造费用明细', accept: '.csv,.xlsx', note: '按费用类别记录金额。' },
      { id: 'labor_detail', label: '人工工时明细', accept: '.csv,.xlsx', note: '人工成本与工时记录。' },
      { id: 'budget', label: '预算数据', accept: '.csv,.xlsx', note: '预算成本与产量。' },
      { id: 'industry_reference', label: '行业参考数据', accept: '.csv,.xlsx', note: '上传标注“测试数据”的行业基准表，仅作参考，不计入成本。' },
    ]}
    parsePath="/data/parse"
    parseLabel="解析数据"
    successPrefix="数据处理成功"
    failPrefix="数据处理失败"
    listTitle="导入记录"
    hint="上传 CSV / XLSX，再点击“解析数据”。"
    processingNotes="原件保留。新文件与已接入数据合并校验，重复去重、冲突提示修正；缺失不补零，汇总和明细不重复计入。未配置模型时使用规则映射。"
  />;
}
