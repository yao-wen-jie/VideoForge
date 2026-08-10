@echo off
chcp 65001 >nul
echo ==========================================
echo   视频自动化 Web 控制台
echo ==========================================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查并安装依赖
echo [1/3] 检查依赖...
if not exist .venv (
    echo 创建虚拟环境...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

REM 创建工作区目录
echo [2/3] 初始化工作区...
python -c "from pathlib import Path; \
[(p/'01-生成成果').mkdir(parents=True,exist_ok=True), \
 (p/'02-选题策划').mkdir(parents=True,exist_ok=True), \
 (p/'03-素材库'/'video').mkdir(parents=True,exist_ok=True), \
 (p/'03-素材库'/'image').mkdir(parents=True,exist_ok=True), \
 (p/'03-素材库'/'audio').mkdir(parents=True,exist_ok=True), \
 (p/'04-脚本工具').mkdir(parents=True,exist_ok=True), \
 (p/'05-第三方技能').mkdir(parents=True,exist_ok=True), \
 (p/'06-运营日志').mkdir(parents=True,exist_ok=True), \
 (p/'07-文档与配置').mkdir(parents=True,exist_ok=True), \
 (p/'config').mkdir(parents=True,exist_ok=True)] \
" 2>nul

REM 启动应用
echo [3/3] 启动 Web 控制台...
echo.
echo 正在启动，请稍候...
echo 打开浏览器访问: http://localhost:5000
echo.
python app.py
pause
