# ADR 0004：模块化单体中的成本核心、行业包与企业配置

状态：实施。日期：2026-09-17。基于acc4693，不复制ERP实现，无新增运行依赖。

选择Pydantic不可变合同、显式可信策略注册、SQLite任务/outbox、现有DuckDB/FTS/Chroma/LlamaIndex检索与React/ECharts。行业切换绑定不可变AnalysisContext，绝不使用进程级active_industry。成本金额和独立产量关系分别聚合，Σ金额/Σ可比产量；基础导入成本与驱动重建来源互斥。企业配置独立于行业和制造模式。受信策略代码新增允许受控重启，配置包不需重编前端。

比较过：逐行业复制后台（修复难同步，拒绝）；完整ERP/插件平台（首轮收益低且引入存量/许可复杂度，拒绝）；保留轻量单体并提取真实变化接口（选择）。内置注册表足够，未引入pluggy。制药旧报告编译器为严格赛题适配；合成报告走同render_docx入口、包章节配置、共享字体/PDF/审核。迁移不能声称零核心改动：本轮新增industry/context_services/reference_report接口后才接通参考包。

## 一手研究与许可

- [ERPNext BOM](https://docs.frappe.io/erpnext/bill-of-materials)、[当前BOM代码](https://github.com/frappe/erpnext/blob/develop/erpnext/manufacturing/doctype/bom/bom.py)：BOM输入、工序、计量和成本来源分开；ERPNext GPL-3与Frappe MIT不同。本轮未复制。
- [Odoo mrp manifest](https://github.com/odoo/odoo/blob/19.0/addons/mrp/__manifest__.py)、[mrp_account manifest](https://github.com/odoo/odoo/blob/19.0/addons/mrp_account/__manifest__.py)、[成本实现](https://github.com/odoo/odoo/blob/19.0/addons/mrp_account/models/mrp_production.py)：核对19.0两个模块LGPL-3，借鉴生产订单/工作中心和成本来源；未使用Enterprise或复制代码。
- [Tryton production](https://docs.tryton.org/latest/modules-production/)、[production-work](https://docs.tryton.org/latest/modules-production-work/)：输入输出与工序成本扩展。GPL-3.0-or-later，未复制。代码直链本轮访问失败，不能宣称审阅了该文件实现。
- [微软成本组](https://learn.microsoft.com/en-us/dynamics365/supply-chain/cost-management/cost-groups)、[生产订单成本分析](https://learn.microsoft.com/en-us/dynamics365/supply-chain/cost-management/production-order-cost-analysis)、[配方版本](https://learn.microsoft.com/en-us/dynamics365/supply-chain/production-control/formulas-versions)：成本分类、估算/实际、配方与联副产品是不同维度。产品文档不作为普适会计准则。
- [pluggy](https://pluggy.readthedocs.io/en/stable/)仅接口参考，未新增依赖。

## 不可声称

合成迁移验证不等于真实行业落地；未做全量ERP、自动WIP/联副产品引擎或真实微信。规则生成与模型生成有独立来源标签。公开样例数字为独立假设，不来自题包，阈值不是行业基准。
