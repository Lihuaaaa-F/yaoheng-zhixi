# 药衡智析增量源码交接

1. public_source_candidate 是公开源码**候选**；未发布，不含题包/报告/知识原文。公开前还需队内审查授权。
2. team_internal 仅供参赛队内部，含原题包、知识、工作模板、当前样例和真实证据；不得公开。
3. 在包根目录运行 `python3 prepare_team_workspace.py`，然后进入public_source_candidate。合并后的工作副本含内部资料。
4. 读 `docs/ZCODE_HANDOFF.md`，运行 `bash 05_原型/scripts/bootstrap.sh` 与 `bash 05_原型/scripts/start.sh`。
5. 包不含密钥、个人配置、venv、node_modules、缓存与旧版生成产物。检索模型按固定manifest下载或显式外置复用。
6. GLM应用实调缺凭据，真人归因/可读性/版式待评。文件生成成功不代表报告验收成功。
7. 当前验证证据位于team_internal/06_评测/incremental_20260916；历史失败证据在04_baseline及本轮history日志，不可覆盖。
