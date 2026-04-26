# ============================================================
#  WenForge Launcher (PowerShell)
#  右键 -> 使用 PowerShell 运行
#  或者:   powershell -ExecutionPolicy Bypass -File Start.ps1
# ============================================================

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ROOT
$ErrorActionPreference = "Stop"

Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor DarkCyan
Write-Host "║       WenForge - 锻造文学               ║" -ForegroundColor Cyan
Write-Host "║       AI 网文创作助手                    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor DarkCyan
Write-Host ""

# ── 1. Check dependencies ──────────────────────────────
$errors = @()

if (-not (Test-Path "$ROOT\package.json")) {
    $errors += "找不到 package.json"
}
if (-not (Test-Path "$ROOT\node_modules\electron\dist\electron.exe")) {
    $errors += "找不到 Electron，请执行: npm install"
}
else {
    Write-Host "[OK] Electron 就绪" -ForegroundColor Green
}
if (-not (Test-Path "$ROOT\dist\index.html")) {
    Write-Host "[WARN] 前端未编译，正在编译..." -ForegroundColor Yellow
    try {
        & npx.cmd vite build
        Write-Host "[OK] 前端编译完成" -ForegroundColor Green
    }
    catch {
        $errors += "前端编译失败，请执行: npx vite build"
    }
}
else {
    Write-Host "[OK] 前端就绪" -ForegroundColor Green
}
if (Test-Path "$ROOT\python\main.py") {
    Write-Host "[OK] Python 引擎就绪" -ForegroundColor Green
}
else {
    $errors += "找不到 Python 引擎"
}

if ($errors.Count -gt 0) {
    Write-Host "`n[ERROR] 发现以下问题:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host "  ❌ $_" -ForegroundColor Red }
    Write-Host "`n请修复后重试" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}

# ── 2. Find Python ─────────────────────────────────────
$python = $null
try { $python = (Get-Command python -ErrorAction Stop).Source } catch {}
if (-not $python) { try { $python = (Get-Command python3 -ErrorAction Stop).Source } catch {} }
if (-not $python) { try { $python = (Get-Command py -ErrorAction Stop).Source } catch {} }
# Common install paths
$paths = @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    "C:\Python311\python.exe"
)
if (-not $python) {
    foreach ($p in $paths) {
        if (Test-Path $p) { $python = $p; break }
    }
}
if (-not $python) {
    Write-Host "[ERROR] 未找到 Python，请安装 Python 3.11+" -ForegroundColor Red
    Write-Host "    下载: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按 Enter 退出"
    exit 1
}
Write-Host "[OK] Python: $python" -ForegroundColor Green

# ── 3. Start Python Engine ──────────────────────────────
Write-Host "`n[1/2] 启动 AI 引擎..." -ForegroundColor Cyan
$pythonLog = "$ROOT\python.log"
try {
    $pythonArgs = @("-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8765")
    $pythonProcess = Start-Process -FilePath $python -ArgumentList $pythonArgs `
        -WorkingDirectory "$ROOT\python" `
        -WindowStyle Minimized `
        -RedirectStandardOutput $pythonLog `
        -RedirectStandardError "$pythonLog.err" `
        -PassThru -NoNewWindow
    Write-Host "  → PID: $($pythonProcess.Id)" -ForegroundColor Gray
    Write-Host "  → 日志: python.log" -ForegroundColor Gray
}
catch {
    Write-Host "  ⚠ Python 启动状态请查看 python.log" -ForegroundColor Yellow
}

# ── 4. Launch Electron ──────────────────────────────────
Write-Host "[2/2] 启动桌面应用..." -ForegroundColor Cyan
try {
    $electron = "$ROOT\node_modules\electron\dist\electron.exe"
    Start-Process -FilePath $electron -ArgumentList "$ROOT." -WorkingDirectory $ROOT
    Write-Host ""

    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor DarkCyan
    Write-Host "║        WenForge 已启动！                  ║" -ForegroundColor Cyan
    Write-Host "║        请稍等 AI 引擎就绪...              ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor DarkCyan
    Write-Host ""
    Write-Host "故障排查:" -ForegroundColor Yellow
    Write-Host "  - 查看 python.log 检查 Python 引擎状态" -ForegroundColor Gray
    Write-Host "  - 在终端运行此脚本可看到完整错误信息" -ForegroundColor Gray
}
catch {
    Write-Host "[ERROR] 桌面应用启动失败: $_" -ForegroundColor Red
    Read-Host "按 Enter 退出"
    exit 1
}
