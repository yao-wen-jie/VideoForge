---
name: videoforge
description: >
  VideoForge 视频自动化 Web 控制台。
  提供选题矩阵、AI脚本生成、镜头卡分镜、AI配音、素材库管理、
  成本追踪、数据看板等视频创作全流程工具。
  启动本地服务后通过浏览器 http://localhost:5000 使用。
  当用户提到视频创作、选题、脚本、配音、镜头卡、素材管理时触发。
---

# 视频自动化 VideoForge

> **一句话出片**：选题 → AI脚本 → 镜头卡分镜 → AI配音 → 素材管理，全流程自动化。
> 整合 video-shotcraft 104张镜头配方卡 + 161条样片素材 + 11种AI配音音色。

---

## 如何启动服务

### 方式一：一键启动（Windows）
```bash
start.bat
```
服务启动后自动打开浏览器访问 `http://localhost:5000`。
**不要关闭黑窗口**，关了服务就停了。

### 方式二：手动启动
```bash
# 进入项目目录
cd 视频自动化

# 用虚拟环境Python启动
.venv\Scripts\python.exe app.py
```

浏览器访问：**http://localhost:5000**

---

## Agent 应调用的核心 API

### 1. 系统状态检测
```
GET /api/system/status
```
返回：Python环境、FFmpeg、GPU、API Keys 配置状态。

### 2. 选题矩阵生成
```
POST /api/matrix/generate
Body: {"category": "情感"}  // 情感|职场|科技|生活
```
返回：10条爆款选题。

### 3. AI脚本生成
```
POST /api/script/generate
Body: {"topic": "选题标题", "style": "口播", "duration": 30}
```
返回：完整口播脚本（需配置 DeepSeek API Key）。

### 4. 镜头卡库
```
GET /api/shotcraft/library          # 全部104张镜头卡
GET /api/shotcraft/search?q=开场    # 搜索镜头卡
GET /api/shotcraft/categories       # 获取分类列表
```

### 5. AI配音（新增）
```
POST /api/voice/synthesize
Body: {
  "text": "要合成的文案",
  "engine": "edge-tts",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+0%"
}
```
返回：音频文件路径，可直接播放下载。

可用音色：`zh-CN-XiaoxiaoNeural` (晓晓)、`zh-CN-YunxiNeural` (云希)、
`zh-CN-YunjianNeural` (云健)、`zh-CN-XiaoyiNeural` (晓伊)、
`zh-CN-YunyangNeural` (云扬)、`zh-CN-XiaochenNeural` (晓晨)。

### 6. 素材库
```
GET /api/assets/list     # 素材列表
GET /api/assets/stats    # 素材统计
```

### 7. 数据看板
```
GET /api/dashboard/stats
```

---

## 配置API Key（解锁AI功能）

打开 `http://localhost:5000` → 「系统设置」：

| Key | 用途 | 获取方式 |
|-----|------|----------|
| `deepseek` | AI脚本生成 | [硅基流动](https://www.siliconflow.cn) 注册免费领额度 |
| `pixabay` | 免费素材 | [Pixabay API](https://pixabay.com/api/docs/) |
| `pexels` | 免费素材 | [Pexels API](https://www.pexels.com/api/) |

**最低配置**：只需 `deepseek` Key 即可使用 AI 脚本生成。

---

## 项目结构

```
视频自动化/
├── app.py                  # Flask 主应用
├── requirements.txt        # Python 依赖
├── start.bat               # 一键启动脚本（Windows）
├── SKILL.md                # 本文档（Agent操作手册）
│
├── modules/
│   ├── workflow_engine.py  # 工作流引擎
│   ├── enhanced_features.py # 增强功能
│   └── voiceforge_tts.py   # AI配音模块
│
├── templates/index.html    # Web 控制台
├── static/js/app.js        # 前端逻辑
├── video-shotcraft/        # 104张镜头卡数据
└── workspace/              # 工作区（运行后自动创建）
```

---

## 故障排查

| 问题 | 解决 |
|------|------|
| 双击 start.bat 闪退 | 先运行 `check_env.bat` 看诊断报告 |
| 智能导演/爆款复刻提示依赖缺失 | 此为存根版本，完整功能需安装 [OpenMontage](https://github.com/OpenMontage) |
| AI脚本生成失败 | 未配置 DeepSeek API Key |
| 镜头卡库为空 | 检查 `video-shotcraft/api/library.json` 是否存在 |
| AI配音无声 | 确认网络连接（Edge-TTS 需联网） |
|------|------|
| 双击 start.bat 闪退 | 先运行 `check_env.bat` 看诊断报告 |
| AI脚本生成失败 | 未配置 DeepSeek API Key |
| 镜头卡库为空 | 检查 `video-shotcraft/api/library.json` 是否存在 |
| AI配音无声 | 确认网络连接（Edge-TTS 需联网） |

---

*版本：2.1 | 更新：2026-08-18*
