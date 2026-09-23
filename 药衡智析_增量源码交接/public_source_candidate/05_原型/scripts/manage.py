#!/usr/bin/env python3
"""Only manage process IDs belonging to this project's recorded start time."""
from pathlib import Path
import json,os,signal,socket,subprocess,sys,time,urllib.request
APP=Path(__file__).resolve().parents[1];ROOT=APP.parent;RUN=APP/'.runtime';RUN.mkdir(exist_ok=True)
sys.path.insert(0,str(APP/'backend'))
from pharma.config import PACKAGE,RUNTIME
RUN=RUNTIME
def _default_python():
    for candidate in (APP/'.venv/bin/python',APP/'.venv/Scripts/python.exe'):
        if candidate.exists():return str(candidate)
    return sys.executable
PYTHON=Path(os.environ.get('PHARMA_PYTHON') or _default_python());STATE=RUN/'processes.json'
def _windowless_python():
    # Windows 的 venv python.exe 只是启动器：它重新派生真正的控制台解释器时
    # 不继承 DETACHED/CREATE_NO_WINDOW 标志（2026-09-23 探针实测两者均穿透
    # 失败，GetConsoleWindow()!=0），于是每个服务分配到新控制台，被系统默认
    # 终端（Windows Terminal）宿主为常驻窗口——"每次运行完终端不自动关闭"，
    # 且手关窗口会连带杀死服务。pythonw.exe 全链路 GUI 子系统，无控制台；
    # 服务的 stdout/stderr 本就重定向进 .runtime/*.log，不依赖控制台。
    if os.name=='nt' and PYTHON.name.lower().endswith('.exe'):
        pw=PYTHON.with_name('pythonw.exe')
        if pw.exists():return pw
    return PYTHON
SERVICE_PYTHON=_windowless_python()

def token(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().split()
        return fields[21] if fields[2]!='Z' else None
    except (OSError,IndexError):return None

def alive(info):
    # POSIX: /proc start-time token. Windows: /proc absent; verify the pid
    # still names a live process (Start Time via WMI-free ctypes check).
    if Path('/proc').is_dir():
        return token(info['pid'])==info['token']
    import ctypes
    PROCESS_QUERY_LIMITED_INFORMATION=0x1000; STILL_ACTIVE=259
    kernel32=ctypes.windll.kernel32
    handle=kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,int(info['pid']))
    if not handle:return False
    try:
        code=ctypes.c_ulong()
        if not kernel32.GetExitCodeProcess(handle,ctypes.byref(code)):return False
        return code.value==STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)
def ready(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as r:return r.status==200
    except Exception:return False

def worker_ready(api_port):
    """Web 端口可开不等于后台能力可用：以 /health 的 worker 心跳为准（fix8）。"""
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{api_port}/health',timeout=2) as r:
            return json.loads(r.read()).get('worker',{}).get('alive') is True
    except Exception:return False

def occupied(port):
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',port));return False
        except OSError:return True

def main():
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    if sys.argv[1]=='stop':
        for name,info in state.items():
            if not alive(info):continue
            if os.name=='nt':
                # Windows 记录的是启动器 PID，真实解释器（占端口/干活的那
                # 个）是其子进程；TerminateProcess 不回收子树，只杀启动器
                # 会孤儿化真身——上一轮"6 个游离 python、监听 PID 与记录
                # 不一致"即源于此。树杀一并回收。
                subprocess.run(['taskkill','/F','/T','/PID',str(info['pid'])],capture_output=True)
            else:os.kill(info['pid'],signal.SIGTERM)
        for _ in range(100):
            if not any(alive(info) for info in state.values()):break
            time.sleep(.1)
        if any(alive(info) for info in state.values()):raise SystemExit('本项目进程仍在退出，请稍后重试')
        print('已停止本项目记录的进程');return
    env={**os.environ,'PYTHONPATH':str(APP/'backend'),'TMPDIR':'/tmp','MPLCONFIGDIR':str(RUN/'matplotlib'),'ANONYMIZED_TELEMETRY':'False','OTEL_SDK_DISABLED':'true'}
    mock=PACKAGE/'05_RPA接口文档'
    rpa_module='mock_rpa_server:app' if (mock/'mock_rpa_server.py').is_file() else 'pharma.synthetic_rpa:app'
    rpa_dir=str(mock) if (mock/'mock_rpa_server.py').is_file() else str(APP/'backend')
    api_port=int(os.getenv('PHARMA_API_PORT','8765'));rpa_port=int(os.getenv('PHARMA_RPA_PORT','8090'))
    env['RPA_BASE_URL']=f'http://127.0.0.1:{rpa_port}'
    env['PHARMA_RPA_SIMULATION']='1'
    # 冷启动顺序：rpa → api → worker。worker 的就绪判据是 api /health 的
    # 心跳，api 必须先于 worker 启动（此前 rpa→worker→api 的顺序在冷启动时
    # 必然"心跳超时"中断——历史上被手工预起的 api 掩盖，2026-09-22 暴露）。
    commands={'rpa':([str(SERVICE_PYTHON),'-m','uvicorn',rpa_module,'--app-dir',rpa_dir,'--host','127.0.0.1','--port',str(rpa_port)],rpa_port),
              'api':([str(SERVICE_PYTHON),'-m','uvicorn','pharma.api:app','--host','127.0.0.1','--port',str(api_port)],api_port),
              'worker':([str(SERVICE_PYTHON),'-m','pharma.worker'],None)}
    for name,(cmd,port) in commands.items():
        if name in state and alive(state[name]):continue
        if port and occupied(port):raise SystemExit(f'端口{port}被非本项目受管进程占用；未终止其他服务')
        with (RUN/(name+'.log')).open('ab') as log:
            # start_new_session is POSIX-only; on Windows the children must
            # detach from the caller's console/job or they die with the shell.
            flags=0
            if os.name=='nt':
                flags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.DETACHED_PROCESS
                try:flags|=subprocess.CREATE_BREAKAWAY_FROM_JOB
                except AttributeError:pass
            p=subprocess.Popen(cmd,cwd=APP,env=env,stdout=log,stderr=log,start_new_session=(os.name!='nt'),creationflags=flags)
        state[name]={'pid':p.pid,'token':token(p.pid),'command':cmd};STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2))
        if port:
            for _ in range(60):
                if ready(port):break
                if p.poll() is not None:raise SystemExit(f'{name}退出，见{RUN/name}.log')
                time.sleep(.5)
            else:raise SystemExit(f'{name}健康检查超时')
        elif name=='worker':
            # 后台任务进程退出或心跳不刷新时不得宣称启动成功（fix8）。
            for _ in range(90):
                if p.poll() is not None:raise SystemExit(f'后台任务进程启动后即退出（退出码 {p.poll()}）；详见 {RUN/(name+".log")}')
                if ready(api_port) and worker_ready(api_port):break
                time.sleep(1)
            else:raise SystemExit(f'后台任务处理未就绪（Web 已响应但 worker 心跳超时）；详见 {RUN/(name+".log")}，常见原因：依赖缺失、数据库被占用、已有本项目 worker 在运行')
    print(f'药衡智析：http://127.0.0.1:{api_port}  原mock：http://127.0.0.1:{rpa_port}')
if __name__=='__main__':main()
