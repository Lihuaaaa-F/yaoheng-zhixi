# ADR 0003：最小主流框架适配与受约束外部模型

状态：Accepted；原决定2026-08-26，按实现更新2026-09-15。

在本地检索结果上真实执行LlamaIndex Core BaseRetriever/TextNode/NodeWithScore，业务数值和RRF仍由项目明确实现。显式CPU embedding避免框架隐式调用默认OpenAI模型；不同时引入LangChain或云解析服务。

模型网关默认DeepSeek `deepseek-flash`，OpenAI chat/completions与Anthropic messages保留不同协议编码。密钥从外部本地文件或环境读取，不写入源码。用户已明确允许项目必要上下文由商业模型处理；这项会话授权覆盖本地联调，不授权公开原始比赛资料、报告或远端发布。

Pydantic约束Finding、指标引用、证据摘录和缺证项。程序注入业务数值，文档事实逐字引用真实位置；原因假设需同时提供指标与文档。网络错误有限超时，结构最多两次修复，调用次数持久化限制，未知费用记UNKNOWN。版本和缓存包含数据、知识、模型、提示及模板；worker检查入队版本，变化要求重新提交。

规则版是可见降级，不等于真实模型PASS。Anthropic协议已用HTTP夹具验证，其他真实供应商未联调。最终S1/S3/Q2全新真实调用通过（非缓存），S2因未绑定文档数字降级，以四场景报告和 `06_评测/verification.json` 为证；比赛准备仍待人工评分与后续视频/PPT。


## 2026-09-16增量决定
应用默认迁移至glm-5.3-flash，通用中国站端点；上文DeepSeek为历史实现记录，不是当前默认。已加入项目配置、受控密钥读取、Coding端点拒绝、版本缓存、日期/规格/证据数字类型化、章节局部修复。GLM真实调用因凭据缺失未执行，probe_glm.json为BLOCKED；不得将历史成功重命名。
