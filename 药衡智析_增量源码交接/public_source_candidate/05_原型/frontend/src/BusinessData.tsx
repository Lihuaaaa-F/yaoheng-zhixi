import ImportWorkflow from './ImportWorkflow';

/** 数据中心 · 业务数据：五类成本数据导入 → 列表等待 → 一键“解析数据”
 * （预处理→智能字段映射→质检→指标→归因分析→发布，全程进度条）。 */
export default function BusinessData() {
  return <ImportWorkflow
    kind="business"
    types={[
      { id: 'cost_summary', label: '成本汇总数据', accept: '.csv,.xlsx', note: '含 产量/直接材料/直接人工/制造费用 的成本宽表（题包《成本汇总》同构）。' },
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
    hint="上传业务成本数据：原始文件保留不转码；解析将从数据预处理到归因分析全流程执行（数据提取模型建议字段映射、数据分析模型生成归因推测，未配置模型时确定性回退）。同一企业的多份文件（汇总/明细/预算）一次解析合并为一个数据集，汇总口径优先、防止双计。"
  />;
}
