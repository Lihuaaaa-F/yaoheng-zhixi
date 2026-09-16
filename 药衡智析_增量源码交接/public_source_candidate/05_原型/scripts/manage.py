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

def occupied(port):
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',port));return False
        except OSError:return True

def main():
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    if sys.argv[1]=='stop':
        for name,info in state.items():
            if alive(info):os.kill(info['pid'],signal.SIGTERM)
        for _ in range(100):
            if not any(alive(info) for info in state.values()):break
            time.sleep(.1)
        if any(alive(info) for info in state.values()):raise SystemExit('本项目进程仍在退出，请稍后重试')
        print('已停止本项目记录的进程');return
    env={**os.environ,'PYTHONPATH':str(APP/'backend'),'TMPDIR':'/tmp','MPLCONFIGDIR':str(RUN/'matplotlib'),'ANONYMIZED_TELEMETRY':'False','OTEL_SDK_DISABLED':'true'}
    mock=PACKAGE/'05_RPA接口文档'
    api_port=int(os.getenv('PHARMA_API_PORT','8765'));rpa_port=int(os.getenv('PHARMA_RPA_PORT','8090'))
    env['RPA_BASE_URL']=f'http://127.0.0.1:{rpa_port}'
    commands={'rpa':([str(PYTHON),'-m','uvicorn','mock_rpa_server:app','--app-dir',str(mock),'--host','127.0.0.1','--port',str(rpa_port)],rpa_port),'worker':([str(PYTHON),'-m','pharma.worker'],None),'api':([str(PYTHON),'-m','uvicorn','pharma.api:app','--host','127.0.0.1','--port',str(api_port)],api_port)}
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
    print(f'药衡智析：http://127.0.0.1:{api_port}  原mock：http://127.0.0.1:{rpa_port}')
if __name__=='__main__':main()
