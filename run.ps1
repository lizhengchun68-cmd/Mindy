# Mindy 快速运行脚本（PowerShell）
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = if (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") {
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
} else {
    "python"
}

Write-Host "[Mindy] 处理 file\ 目录下的订单 xlsx ..." -ForegroundColor Cyan
& $py -m src.main @args
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[失败] 退出码 $LASTEXITCODE" -ForegroundColor Red
    Write-Host "若缺少模块: $py -m pip install -r requirements.txt"
    exit $LASTEXITCODE
}
Write-Host "`n[完成] 输出目录: production\" -ForegroundColor Green
