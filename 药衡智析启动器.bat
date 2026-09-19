@echo off
chcp 65001 >nul
rem 药衡智析桌面启动入口：双击打开菜单（启动/停止/状态/日志）。
rem 逻辑全部在 deploy\launcher.ps1；本文件只是免策略限制的跳板。
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0药衡智析_增量源码交接\public_source_candidate\05_原型\deploy\launcher.ps1" %*
