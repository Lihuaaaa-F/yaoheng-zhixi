// 展示层统一中文映射：后端枚举/字段键在界面上呈现为中文；未知键保留原值兜底（不隐藏数据）。
// 收录范围以当前后端实际输出为准，新枚举出现英文直出时在此补录。

export const ELEMENT_LABELS: Record<string, string> = {
  material: '直接材料', materials: '直接材料', labor: '直接人工', overhead: '制造费用',
  energy: '能源', depreciation: '折旧', other: '其他',
  unit_cost: '单位成本', total_cost: '总成本', quantity: '产量',
};
export const elementLabel = (key: unknown) => {
  const value = String(key ?? '').trim();
  return ELEMENT_LABELS[value] ?? value;
};

export const DIRECTION_LABELS: Record<string, string> = {
  increase: '上升', decrease: '下降', up: '上升', down: '下降',
  flat: '持平', unchanged: '持平', neutral: '持平',
};
export const directionLabel = (value: unknown) => {
  const key = String(value ?? '').trim();
  return DIRECTION_LABELS[key] ?? key;
};

export const boolLabel = (value: unknown) =>
  value === true ? '是' : value === false ? '否' : String(value ?? '');

// 任务阶段（jobs.history[].stage / jobs.stage）
export const STAGE_LABELS: Record<string, string> = {
  PENDING: '排队等待', MAPPING: '字段映射', VALIDATE: '质量校验', COMPUTE: '指标计算',
  ATTRIBUTION: '归因分析', PUBLISH: '发布注册', PARSING: '解析中', PARSE: '解析',
  KB_BUILD: '知识库构建', RENDER: '报告渲染', UPLOAD: '验收上传', EXPLAIN: '解释生成',
  SUCCEEDED: '已完成', DEGRADED: '已完成（降级）', FAILED: '失败',
  VECTOR_SWITCH: '向量模型切换', RPA: '模拟下发',
};
export const stageLabel = (value: unknown) => {
  const key = String(value ?? '').trim();
  return STAGE_LABELS[key] ?? key;
};
