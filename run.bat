@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set "PY=python"
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    set "PY=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
)

echo [Mindy] 处理 file\ 目录下的订单 xlsx ...
echo.

"%PY%" -m src.main %*
set "RC=%ERRORLEVEL%"

if %RC% neq 0 (
    echo.
    echo [失败] 退出码 %RC%
    echo 若提示缺少模块，请先执行: "%PY%" -m pip install -r requirements.txt
    pause
    exit /b %RC%
)

echo.
echo [完成] 输出目录: production\
pause
exit /b 0
