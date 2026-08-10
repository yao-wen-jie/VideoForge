@echo off
chcp 65001 >nul
echo ==========================================
echo   视频自动化 — 环境诊断
echo ==========================================
echo.

echo [检查] Python 版本:
python --version 2>nul || echo   X 未安装
echo.

echo [检查] FFmpeg:
ffmpeg -version 2>nul | findstr "version" || echo   X 未安装 (视频处理功能受限)
echo.

echo [检查] 工作区目录:
if exist "01-生成成果" (echo   √ 01-生成成果) else (echo   X 01-生成成果)
if exist "03-素材库" (echo   √ 03-素材库) else (echo   X 03-素材库)
if exist "config" (echo   √ config) else (echo   X config)
echo.

echo [检查] 配置状态:
if exist config.json (
    echo   √ config.json 已创建
    python -c "import json; c=json.load(open('config.json','r',encoding='utf-8')); \
    keys=c.get('api_keys',{}); \
    print('   API Keys配置:'); \
    [print(f'     - {k}: {\"已配置\" if v else \"未配置\"}') for k,v in keys.items()]"
) else (
    echo   X config.json 不存在
)
echo.

echo ==========================================
echo 诊断完成。按任意键退出。
pause >nul
