# 药衡智析桌面启动器（PowerShell 逻辑；由 药衡智析启动器.bat 双击调用）
# 职责：定位 Docker（Windows CLI 优先，WSL 集成回退）→ 启动/停止/状态/日志。
# 只管理本项目的 compose 服务（项目名 yaoheng），不终止任何未知进程。
param(
    [Parameter(Position = 0)][ValidateSet('menu', 'start', 'update', 'stop', 'status', 'logs', 'open')]
    [string]$Action = 'menu',
    [switch]$NoBrowser
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$DeployDir = $PSScriptRoot
$ComposeFile = Join-Path $DeployDir 'docker-compose.yml'
$Url = 'http://127.0.0.1:8765'

function Write-Info($msg)  { Write-Host "[药衡智析] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "[药衡智析] $msg" -ForegroundColor Green }
function Write-Warn2($msg) { Write-Host "[药衡智析] $msg" -ForegroundColor Yellow }
function Write-Err2($msg)  { Write-Host "[药衡智析] $msg" -ForegroundColor Red }
function Pause-Exit($code = 1) { if ($Host.Name -eq 'ConsoleHost') { Read-Host '按回车键关闭窗口' | Out-Null }; exit $code }

# ---------- Docker 定位：Windows CLI → 常见安装路径 → WSL 集成 ----------
# 返回 @{ Docker=参数数组前缀; Compose=完整 compose 参数前缀 }
function Resolve-Docker {
    $dockerExe = $null
    $cmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($cmd) { $dockerExe = 'docker' }
    if (-not $dockerExe) {
        $fallback = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
        if (Test-Path $fallback) { $dockerExe = $fallback }
    }
    if ($dockerExe) {
        return @{ Docker = @($dockerExe); Compose = @($dockerExe, 'compose', '-f', $ComposeFile) }
    }
    # WSL 集成回退：发行版内的 docker（与 Docker Desktop 同一引擎）。
    # compose 文件路径需换算为发行版内可见的 /mnt/<盘>/… 形式。
    # 2026-09-24 修复（审计 AUD-DEP-06）：不再硬编码 Ubuntu-20.04——按序探测
    # 每个发行版内是否有 docker，适配任意发行版名。
    $distros = @()
    try { $distros = (wsl -l -q 2>$null | ForEach-Object { $_.Trim([char]0) }) | Where-Object { $_ } } catch {}
    foreach ($distro in $distros) {
        wsl -d $distro -e sh -c 'command -v docker >/dev/null 2>&1' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $wslFile = $ComposeFile -replace '\\', '/'
            if ($wslFile -match '^//wsl(?:\.localhost|\$)/([^/]+)/(.*)$') {
                if ($Matches[1] -ne $distro) { continue }
                $wslFile = '/' + $Matches[2]
            } elseif ($wslFile -match '^([A-Za-z]):/(.*)$') {
                $wslFile = '/mnt/' + $Matches[1].ToLower() + '/' + $Matches[2]
            } else {
                $converted = & wsl -d $distro -- wslpath -u $ComposeFile 2>$null
                if ($LASTEXITCODE -ne 0 -or -not $converted) { continue }
                $wslFile = $converted.Trim()
            }
            return @{ Docker = @('wsl', '-d', $distro, 'docker')
                      Compose = @('wsl', '-d', $distro, 'docker', 'compose', '-f', $wslFile) }
        }
    }
    if ($distros.Count -gt 0) { throw 'DOCKER_WSL_INTEGRATION_OFF' }
    throw 'DOCKER_NOT_INSTALLED'
}

function Invoke-Compose($Resolved, [string[]]$Arguments) {
    # Compose 参数数组 = 前缀 + 具体子命令参数；退出码经 $LASTEXITCODE 传递。
    # compose 把进度写到 stderr，需临时放宽偏好避免误判为脚本错误。
    $rest = if ($Resolved.Compose.Count -gt 1) { $Resolved.Compose[1..($Resolved.Compose.Count - 1)] } else { @() }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Resolved.Compose[0] $rest @Arguments } finally { $ErrorActionPreference = $prev }
}

function Invoke-DockerRaw($Resolved, [string[]]$Arguments) {
    # 仅探测用途：吞掉全部输出，靠 $LASTEXITCODE 判断（引擎探测时 stderr 是常态）。
    $rest = if ($Resolved.Docker.Count -gt 1) { $Resolved.Docker[1..($Resolved.Docker.Count - 1)] } else { @() }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $Resolved.Docker[0] $rest @Arguments 2>&1 | Out-Null } finally { $ErrorActionPreference = $prev }
}

function Ensure-Engine($Resolved) {
    $null = Invoke-DockerRaw $Resolved @('info')
    if ($LASTEXITCODE -eq 0) { return }
    Write-Warn2 'Docker 引擎未运行，正在尝试启动 Docker Desktop（最长等待 120 秒）…'
    $dd = 'C:\Program Files\Docker\Docker\Docker Desktop.exe'
    if (-not (Test-Path $dd)) { Write-Err2 '未找到 Docker Desktop，请先安装：https://www.docker.com/products/docker-desktop/'; Pause-Exit }
    Start-Process $dd | Out-Null
    $deadline = (Get-Date).AddSeconds(120)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 5
        $null = Invoke-DockerRaw $Resolved @('info')
        if ($LASTEXITCODE -eq 0) { Write-Ok 'Docker 引擎已就绪'; return }
    }
    Write-Err2 'Docker 引擎 120 秒内未就绪。请打开 Docker Desktop 查看具体报错（常见：WSL2 未启用、虚拟化未开启），就绪后重试本启动器。'
    Pause-Exit
}

function Resolve-OrAdvise {
    try { Resolve-Docker } catch {
        switch ($_) {
            'DOCKER_NOT_INSTALLED' { Write-Err2 '未检测到 Docker。请先安装 Docker Desktop（WSL2 后端），安装说明见仓库 README「部署」一节。' }
            'DOCKER_WSL_INTEGRATION_OFF' { Write-Err2 '检测到 WSL 发行版，但未找到可用的 Docker 集成。请打开 Docker Desktop → Settings → Resources → WSL Integration，启用项目所在的发行版（例如 Ubuntu-24.04）后重试。' }
        }
        Pause-Exit
    }
}

# ---------- 动作 ----------
function Action-Start([switch]$Rebuild) {
    $resolved = Resolve-OrAdvise
    Ensure-Engine $resolved

    Write-Info '启动本项目服务（已运行则直接复用，不会重复启动一套）…'
    # 已有镜像直接复用；缺失时 compose 自动构建（首次准备与日常启动同一入口）
    $composeArgs = @('up', '-d')
    if ($Rebuild) { $composeArgs += '--build'; Write-Info '按当前源码更新镜像，复用构建缓存并保留数据卷。' }
    $null = Invoke-Compose $resolved $composeArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Err2 '服务启动失败。正在查看最近日志以定位原因：'
        $null = Invoke-Compose $resolved @('logs', '--tail', '40', 'web', 'worker', 'rpa') | Select-Object -Last 40 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
        Write-Err2 '常见原因：① 首次构建网络受限（需为 Docker Desktop 配置可用网络/代理）② 端口 8765/8090 被占用 ③ 磁盘空间不足。'
        Pause-Exit
    }

    Write-Info '等待核心服务就绪（Web + 后台任务处理）…'
    $deadline = (Get-Date).AddSeconds(180)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $health = Invoke-RestMethod -Uri "$Url/health" -TimeoutSec 3
            if ($health.worker.alive) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 3 }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        Write-Err2 '容器已启动但核心服务未在 180 秒内就绪。执行「日志」查看 worker 日志；常见原因：首次启动在下载向量模型（可稍等后在浏览器直接访问）。'
        Pause-Exit
    }
    Write-Ok "核心服务已就绪：$Url"

    # 区分“核心就绪”与“完整比赛能力就绪”：无密钥时明确降级提示
    try {
        $routes = Invoke-RestMethod -Uri "$Url/api/model/routes" -TimeoutSec 3
        if ($routes.routes.analysis.available) { Write-Ok '分析模型已配置；请在模型连接中测试实际服务可用性。' }
        else { Write-Warn2 '分析模型尚未配置——确定性分析与基础报告可用；请在网页“模型与设置 → 模型连接”配置。助手密钥单独配置。' }
    } catch { Write-Warn2 '未能读取模型配置状态（不影响核心分析）' }

    if (-not $NoBrowser) { Start-Process $Url }
}

function Action-Stop {
    $resolved = Resolve-OrAdvise
    Write-Info '停止本项目服务（业务数据保留在持久卷，不会丢失）…'
    $null = Invoke-Compose $resolved @('stop')
    if ($LASTEXITCODE -eq 0) { Write-Ok '已停止。数据与历史报告均已保留；再次双击启动器即可恢复。' }
    else { Write-Err2 '停止失败，请用「日志」查看原因。' }
}

function Action-Status {
    $resolved = Resolve-OrAdvise
    $null = Invoke-Compose $resolved @('ps') | ForEach-Object { Write-Host "  $_" }
    try {
        $health = Invoke-RestMethod -Uri "$Url/health" -TimeoutSec 3
        Write-Info ("Web: {0}  Worker 心跳: {1} 秒前  RPA: {2}" -f $health.status, [int]$health.worker.heartbeat_age_seconds, $health.rpa_mode)
    } catch { Write-Warn2 'Web 暂不可达（服务可能未启动）' }
}

function Action-Logs {
    $resolved = Resolve-OrAdvise
    $null = Invoke-Compose $resolved @('logs', '--tail', '80')
}

function Show-Menu {
    Write-Host ''
    Write-Host '======== 药衡智析 · 桌面启动器 ========' -ForegroundColor White
    Write-Host '  1. 启动（首次自动构建，日常秒级启动）'
    Write-Host '  2. 停止（保留全部业务数据）'
    Write-Host '  3. 查看状态'
    Write-Host '  4. 查看日志'
    Write-Host '  5. 打开页面（服务已启动时）'
    Write-Host '  6. 更新源码后的镜像并启动（保留数据）'
    Write-Host '  0. 退出'
    $choice = Read-Host '请选择'
    switch ($choice) {
        '1' { Action-Start }
        '2' { Action-Stop }
        '3' { Action-Status }
        '4' { Action-Logs }
        '5' { Start-Process $Url }
        '6' { Action-Start -Rebuild }
        default { exit 0 }
    }
}

switch ($Action) {
    'start'  { Action-Start }
    'update' { Action-Start -Rebuild }
    'stop'   { Action-Stop }
    'status' { Action-Status }
    'logs'   { Action-Logs }
    'open'   { Start-Process $Url }
    default  { Show-Menu }
}
if ($Host.Name -eq 'ConsoleHost') { Read-Host '按回车键关闭窗口' | Out-Null }
