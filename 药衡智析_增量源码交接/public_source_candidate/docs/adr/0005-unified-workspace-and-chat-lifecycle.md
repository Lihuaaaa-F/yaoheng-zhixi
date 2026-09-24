# ADR 0005：统一上传工作区与持久化聊天标签

状态：实施。日期：2026-09-23。接续工作台升级，保持模块化单体，不引入新服务或运行依赖。

## 页面和数据的一致性

界面取消“数据范围”选择。`GET /api/workspace` 返回本机单企业工作区、当前数据版本、全部已接入来源、待处理来源和问题。没有用户业务上传时可展示原有比赛资料；存在上传但尚未就绪时不能悄悄回到比赛演示。

业务文件在用户点击解析后，连同此前全部已接入文件统一校验。相同业务事实去重；金额、产量、单位或企业冲突不擅自裁决。实际与预算分开，相同字节的不同资料类型也不能被错误去重。工作区 ID 稳定，完整数据版本目录不可变；注册指针只在校验成功后原子切换。分析取得数据后复核版本，防止更新过程中出现版本标签与数字不一致。

`READY` 才允许生成新的工作区分析、报告和助手答案；`PENDING/BLOCKED` 给出处理入口，上一有效版本及历史产物仍保留。报告和助手共用同一分析引擎与快照。数据库中的内部上下文 ID 继续用于证据隔离，不再作为用户必须选择的业务选项。

修正旧表时，可在“更新已接入文件”中明确指定替代关系；`POST /api/data/parse` 的 `replacements` 为新导入 ID 到旧导入 ID 的映射。发布接口也接受 `options.replace_import_id`。旧原件和历史版本保留，新组合完整校验后切换，失败仍保留旧版本。不能通过未声明的覆盖来改变已接受数据。

旧版同企业导入自动迁移；仅继承迁移清单中核验过的知识来源，保留来源 ID、原文件、页码和原上下文。显式访问旧范围不会获得兄弟范围权限；比赛或其他企业文档不会混入。

当前接入合同：单企业、人民币、统一产量单位、完整业务粒度。没有交易级主键的重叠明细分片不自动相加；不同单位不猜测换算。含多张非空工作表的 XLSX 提示拆分后重新上传，避免只读首表却声称全部接入。行业扩展仍通过已有行业包完成。

浏览器上传联调复现了 API 与 worker 冷启动时的 SQLite WAL 初始化锁冲突。共用的连接初始化增加有界重试，只重试尚未开始事务的 WAL 初始化，不重放业务写入。真实 SQLite 独占锁与八个并发任务/整改存储初始化测试覆盖此问题。

## 聊天状态

借鉴 Codex 将持久线程、当前打开状态与每轮执行状态分开的思路，用已有 SQLite 实现本产品的会话，不引入 Codex 运行服务。

| 操作 | 行为 |
|---|---|
| ＋ | 总是创建全新聊天，空数据工作区也可创建 |
| 标题标签 | 最多显示三个；当前聊天始终可见，仅一个消息区 |
| 下箭头 | 列出所有已打开标题，按视口高度滚动，无人为数量截断 |
| 固定 | 服务端持久化；优先显示，关闭后仍保留固定标记 |
| 关闭 | 收起标签，保留历史；不阻断已经开始的回答 |
| … → 历史记录 | 搜索、恢复旧聊天的唯一用户入口 |
| 归档 | 从打开列表移除，停止接收进行中的回答；可恢复 |
| 删除 | 用户确认后删除该聊天、轮次及消息；已生成报告、整改任务不删除 |
| 对话导航 | 列出每轮用户问题并跳转到对应真实消息；不展示模型隐藏推理 |

接口：`GET /api/assistant/conversations?state=open|history|archived`；`POST` 新建；`PATCH /api/assistant/conversations/{id}` 接受 `open/close/pin/unpin/archive/unarchive`；`DELETE` 删除。恢复归档先 `unarchive`，再显式 `open`。旧数据库使用增量列迁移，不删除历史。归档或删除后的迟到回答不能恢复已移除的聊天。关闭聊天不等于取消生成。

## 视觉与可访问性

三个固定外框：172px 可折叠左栏、弹性中间工作区、可调整宽度的右栏。运行状态放在左下角。中央筛选与分区导航固定，正文独立滚动；桌面不使用根页面滚动。移动端通过导航和对话抽屉保持阅读空间。

系统字体、柔和背景、22px 外框圆角、克制阴影、深青绿选中态与淡青绿悬停态。190ms 内容切换可中断；跟随系统减少动态，用户也可主动减少。设置中的密度、默认口径和任务通知实际生效。上下文圆环和模型参数保留真实接口及未知状态，不为截图伪造联网、模型或用量。

## 参考与借鉴范围

- [Codex App Server 官方文档](https://developers.openai.com/codex/app-server/)：线程新建/恢复、持久元数据、归档/删除、分轮读取。
- [openai/codex App Server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md) 与 [thread_state.rs](https://github.com/openai/codex/blob/main/codex-rs/app-server/src/thread_state.rs)：实际读取了公开的线程状态、活动轮次与连接订阅分离实现。借鉴状态划分，没有复制 Rust 源码，也不声称获得了 Codex 桌面完整 UI 源码。
- [Apple HIG Layout](https://developer.apple.com/design/human-interface-guidelines/layout)、[Motion](https://developer.apple.com/design/human-interface-guidelines/motion)、[Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)：层级、阅读空间、轻量反馈及减少动态。awesome-design-systems 是索引，不是 Apple 官方编程 skill。

测试与版本以 `../current_run.json` 为准。自动测试通过不代替真人视觉审美、比赛三场景评分、真实模型与目标机器部署验收。
