# 实施进度（续跑先读）

## 唯一工作目录与基线
用户授权迁入本WSL同名目录，D盘只读保留。docs/baseline.json记录129文件复制哈希；原无Git仓，不强制创建/提交。当前42项测试通过，最终机器状态见06_评测/verification.json。

## 已完成
- 原赛题/CSV/PDF/Word/RPA合同核验；16组810算术观测、51连续组零失败；44受保护基线文件当前哈希无变化。
- Python3.12项目venv、React/Vite锁、CPU ONNX、Chroma+FTS5中文分词RRF、LlamaIndex真实适配、DeepSeek及OpenAI/Anthropic接口。
- 指标快照与季度加权、对标方向、三要素unit/total告警、原料/费用、缺值与单位转换。
- 原Word工作副本101唯一/108位置，金额比例拆分，84数值绑定复核；4DOCX+4PDF实际产物、15表/2图、零占位符。
- SQLite报告worker与outbox、用户确认、原mock实际发送、超时/重复/重启边界、幂等与中断快照保持。
- 浏览器25项全链、7项季度/重启、11项归因界面；Windows Chrome/Edge实际DOM截图；最终内容更新后仅新增必要定向检查。
- 六个Matt技能在~/.codex/skills共享，固定SHA+许可证；已有React/浏览器/Data技能复用。原生发现待下次会话验证。
- README/旧方案MD/ADR/原HTML和artifact原位维护；无需外部发布。

## 当前冻结与剩余
FINAL_STATUS=PARTIAL：S1/S3/Q2真实模型通过；S2最终JSON含未绑定文档数字，严格降级规则版，DOCX/PDF合格。先前跨产品胶囊事件误引已作废并补回归。不要将阶段性4报告PASS或旧artifact当最终状态。
模型30条计账未清零；默认上限40留最多10次用户演示，费用UNKNOWN。本轮停止扩大测试/模型调用。
最终混合Recall@5=0.7857，保留集0.75，低于自选0.85；不以降低引用标准换通过。人工0—5评分待填human_scoring.json；Docker无daemon/CLI；比赛视频/PPT/发布/提交未执行。

## 复现命令
```bash
bash 05_原型/scripts/bootstrap.sh
bash 05_原型/scripts/start.sh
bash 05_原型/scripts/verify.sh
```
浏览器http://localhost:8765；报告索引06_评测/scenario_reports.json，文件07_交付/业务报告/<job_id>/report.docx与report.pdf。
沙箱中PID不可见/网络禁用时，运行服务与浏览器须在正常WSL终端或批准的沙箱外执行；stop仅按本项目PID和启动时间处理，不杀其他服务。
下一步仅处理S2文档数字插槽/引用合同稳定性，再一次限次验证；不得重造原数据或把未验证归因当事实。当前已授权任务无外部发送待办。

最终补充：八个实际下载+作废artifact404+降级UI共10项PASS（browser_final_artifacts.json）；旧HTML实际7项PASS且内嵌artifact一致。最终服务已按默认累计40次上限启动，本轮已记30次，不再调用。
