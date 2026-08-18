@echo off
chcp 65001 >nul
title VideoForge Web控制台
color 0A

echo ==========================================
echo   VideoForge 视频自动化 Web控制台
echo ==========================================
echo.

REM 设置项目目录
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

REM 检查虚拟环境Python
set "VENV_PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" (
    echo [错误] 未找到虚拟环境 Python
    echo 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo [致命错误] 无法创建虚拟环境，请确认已安装 Python 3.8+
        pause
        exit /b 1
    )
)

REM 安装依赖
echo [1/3] 检查依赖...
"%VENV_PYTHON%" -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo [警告] 依赖安装可能有问题，继续尝试启动...
)

REM 创建工作区目录
echo [2/3] 初始化工作区...
"%VENV_PYTHON%" -c "from pathlib import Path; p=Path('workspace'); [(p/'01-生成成果').mkdir(parents=True,exist_ok=True), (p/'02-选题策划').mkdir(parents=True,exist_ok=True), (p/'03-素材库'/'video').mkdir(parents=True,exist_ok=True), (p/'03-素材库'/'image').mkdir(parents=True,exist_ok=True), (p/'03-素材库'/'audio').mkdir(parents=True,exist_ok=True), (p/'04-脚本工具').mkdir(parents=True,exist_ok=True), (p/'05-第三方技能').mkdir(parents=True,exist_ok=True), (p/'06-运营日志').mkdir(parents=True,exist_ok=True), (p/'07-文档与配置').mkdir(parents=True,exist_ok=True), (p/'config').mkdir(parents=True,exist_ok=True), (p/'voice_outputs').mkdir(parents=True,exist_ok=True), (p/'voice_clones').mkdir(parents=True,exist_ok=True)]" 2>nul

REM 启动应用
echo [3/3] 启动 Web 控制台...
echo.
echo 正在启动，请稍候...
echo.

echo ==========================================
echo  服务启动后，将自动打开浏览器
echo  手动访问: http://localhost:5000
echo ==========================================
echo.
echo [提示] 不要关闭此窗口！关了服务就停了
echo [提示] 按 Ctrl+C 可以停止服务
echo.

REM 启动浏览器（延迟3秒等服务起来）
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

REM 启动Flask服务
"%VENV_PYTHON%" app.py

REM 如果上面的命令异常退出，暂停显示错误
echo.
echo [服务已停止]
pause
