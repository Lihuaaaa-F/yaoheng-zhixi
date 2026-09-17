# 演示与答辩材料 / Demo & Defense Materials（2026-09-18）

> 运行绑定：`release_20260918_bc854cc`（代码提交 bc854cc，验收 verify=PASS）。
> **English** — Narrated end-to-end demo video and refreshed defense deck, bound to verified run release_20260918_bc854cc.

## 内容 / Contents

| 文件 | 说明 |
|---|---|
| yaoheng_demo_narrated.webm | 讲解字幕版端到端演示，2分52秒（赛题要求≤5分钟）：选择条件→看板（含预测/Agent决策卡）→对标三步法→生成报告→任务与模拟RPA送达→证据与知识图谱 |
| 药衡智析_演示与答辩稿.pptx | 10页答辩稿（python-pptx 1.0.2 生成，含加分项两页：图谱与多模型/自主决策与预测） |
| 药衡智析_演示与答辩稿_阅读版.pdf | 同内容阅读版 PDF 伴读 |
| pptx_render/ | PPTX 经 LibreOffice 实渲染的 PDF 与逐页 PNG（实渲染验证证据） |
| demo_receipt.json | 录制回执（11幕字幕清单、提交的报告任务号） |

生成方式：`05_原型/frontend/record_demo_20260918.mjs`（Playwright 真实浏览器录制，字幕为页内注入）；
`05_原型/scripts/build_demo_deck.py --output-dir 07_交付/demo_20260918`。

## 文件 SHA256

- `yaoheng_demo_narrated.webm`：`4bf171dc16270627e721904629ab58a2fed001c98fd09ae278b2848d96d3e10e`
- `药衡智析_演示与答辩稿.pptx`：`0d0c39ff83a417cb7dd41d964909b492e4e3bdbd560d0ddb61c39108b0f20ce7`
- `药衡智析_演示与答辩稿_阅读版.pdf`：`e6407306b813b52a973184846b00995cc4361646f92d49509059ddbb27e55bf5`
- `demo_receipt.json`：`7d565f0a0985b7b070a10985b2f8d917bf7683e8e04bc099b421c80028fa0bc5`

边界：视频为合成/赛题数据下的本地演示录制；任务送达为模拟 RPA；真人评审（0–5 归因、可读性、版式）仍须本人填写，本目录不替代。
