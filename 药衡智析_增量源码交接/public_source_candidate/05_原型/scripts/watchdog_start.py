#!/usr/bin/env python3
"""看门狗动作体（被计划任务以 pythonw 调用）：幂等补起死掉的服务。

为什么存在：计划任务/批处理链路对中文路径的解析在本机不可靠
（2026-09-24 实测 LastTaskResult=1 或路径乱码），而 python 的 argv 全程
Unicode。计划任务引用 ASCII 路径的系统 pythonw.exe（安装器解析
base_prefix 得到），把本脚本的中文路径当参数传入，由本脚本再以仓库
venv 的 pythonw 跑 manage.py start——manage.py 自身幂等：活着的进程
跳过，只补起死的；服务进程本就 DETACHED+pythonw 无窗口。"""
import subprocess
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
LOG = APP / '.runtime' / 'watchdog.log'


def main() -> None:
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open('ab') as log:
        log.write(f'[watchdog {time.strftime("%Y-%m-%d %H:%M:%S")}] tick\n'.encode('utf-8'))
        pyw = APP / '.venv' / 'Scripts' / 'pythonw.exe'
        subprocess.run([str(pyw), str(APP / 'scripts' / 'manage.py'), 'start'],
                       cwd=APP, stdout=log, stderr=log)


if __name__ == '__main__':
    main()
