# 每日自动运行脚本 (Windows PowerShell)
# 用于定时执行 AnyRouter, OpenI, ShareYourCC 自动化任务

# 设置项目路径
$PROJECT_DIR = Split-Path -Parent $PSScriptRoot
Set-Location $PROJECT_DIR

# 设置日志目录
$LOG_DIR = Join-Path $PROJECT_DIR "data\logs"
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR | Out-Null
}

# 设置日期
$DATE = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

# 激活虚拟环境（如果使用）
# & "$PROJECT_DIR\venv\Scripts\Activate.ps1"

Write-Host "========================================"
Write-Host "开始每日自动化任务: $DATE"
Write-Host "========================================"

# 任务结果
$results = @{
    AnyRouter = $false
    OpenI = $false
    ShareYourCC = $false
}

# 1. 运行 AnyRouter
Write-Host ""
Write-Host ">>> 运行 AnyRouter..."
$logFile = Join-Path $LOG_DIR "anyrouter_$DATE.log"
python -m src anyrouter --headless *>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ AnyRouter 完成" -ForegroundColor Green
    $results.AnyRouter = $true
} else {
    Write-Host "❌ AnyRouter 失败 (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# 2. 运行 OpenI
Write-Host ""
Write-Host ">>> 运行 OpenI..."
$logFile = Join-Path $LOG_DIR "openi_$DATE.log"
python -m src openi --headless *>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ OpenI 完成" -ForegroundColor Green
    $results.OpenI = $true
} else {
    Write-Host "❌ OpenI 失败 (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# 3. 运行 ShareYourCC
Write-Host ""
Write-Host ">>> 运行 ShareYourCC..."
$logFile = Join-Path $LOG_DIR "shareyourcc_$DATE.log"
python -m src shareyourcc --headless *>&1 | Tee-Object -FilePath $logFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ ShareYourCC 完成" -ForegroundColor Green
    $results.ShareYourCC = $true
} else {
    Write-Host "❌ ShareYourCC 失败 (exit code: $LASTEXITCODE)" -ForegroundColor Red
}

# 汇总结果
Write-Host ""
Write-Host "========================================"
Write-Host "任务完成: $DATE"
Write-Host "AnyRouter: $(if ($results.AnyRouter) { '✅' } else { '❌' })"
Write-Host "OpenI: $(if ($results.OpenI) { '✅' } else { '❌' })"
Write-Host "ShareYourCC: $(if ($results.ShareYourCC) { '✅' } else { '❌' })"
Write-Host "========================================"

# 清理旧日志（保留最近 30 天）
Get-ChildItem -Path $LOG_DIR -Filter "*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) } | Remove-Item

# 退出码：任何一个失败就返回 1
if (-not ($results.AnyRouter -and $results.OpenI -and $results.ShareYourCC)) {
    exit 1
}

exit 0
