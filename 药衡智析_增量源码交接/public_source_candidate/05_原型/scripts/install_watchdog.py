#!/usr/bin/env python3
"""注册药衡智析服务自愈看门狗（Windows 计划任务，每 5 分钟）。

任务动作 = ASCII 路径的系统 pythonw.exe + 中文路径的 watchdog_start.py
参数：python 的 argv 全程 Unicode，绕开 cmd 批处理/计划任务链路对中文
路径的解析缺陷（2026-09-24 实测：批内容中文被误读、LastTaskResult=1）。
manage.py start 幂等——活进程跳过，只补起死的，服务本就 pythonw 无窗口。

用法：venv 的 python scripts/install_watchdog.py
删除：schtasks /Delete /TN YaohengWatchdog /F
"""
import os
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
TASK = 'YaohengWatchdog'


def main() -> None:
    start = APP / 'scripts' / 'watchdog_start.py'
    if not start.exists():
        raise SystemExit(f'watchdog_start.py missing: {start}')
    # 安装器可能跑在 venv python 里：base_prefix 才是系统解释器（纯 ASCII 路径）
    system_pyw = Path(sys.base_prefix) / 'pythonw.exe'
    if not system_pyw.exists():
        system_pyw = Path(sys.executable)
    tr = f'"{system_pyw}" "{start}"'
    cmd = ('schtasks', '/Create', '/TN', TASK, '/TR', tr,
           '/SC', 'MINUTE', '/MO', '5', '/F')
    # schtasks 输出为 GBK：显式按 GBK 解码，否则 reader 线程 UTF-8 解码崩溃
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding='gbk', errors='replace')
    print(result.stdout.strip() or result.stderr.strip())
    if result.returncode:
        raise SystemExit(result.returncode)
    print(f'看门狗已注册：{TASK}（每 5 分钟，幂等补起死服务；'
          f'删除：schtasks /Delete /TN {TASK} /F）\n/TR = {tr}')


if __name__ == '__main__':
    main()
