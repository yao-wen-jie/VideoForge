# 视频自动化 VideoForge

> **一句话出片**：选题 → AI脚本 → 镜头卡分镜 → 视频生成 → 多平台发布，全流程自动化。

## 功能全景

| 模块 | 功能 | 状态 |
|------|------|------|
| 📋 **选题矩阵** | 情感/职场/科技/生活 四大矩阵，一键生成10条爆款选题 | ✅ |
| ✍️ **AI脚本** | DeepSeek V3 驱动，30秒口播脚本，黄金五段式结构 | ⚠️ 需配置API Key |
| 🎬 **镜头卡库** | 104张ShotCraft配方卡，10大分类，智能分镜排期 | ✅ |
| 📁 **素材库** | 视频/图片/音频/脚本 统一管理，支持去重检测 | ✅ |
| 🎬 **智能导演** | 输入主题，自动生成导演方案（dry-run/执行） | ⚠️ 依赖旧工作流 |
| 🔥 **爆款复刻** | 分析抖音爆款，自动复刻同款视频 | ⚠️ 依赖旧工作流 |
| 💰 **成本追踪** | 每日API调用成本汇总，超预算自动告警 | ✅ |
| ⏰ **定时任务** | 定时选题、定时生成、定时发布，全自动托管 | ✅ |
| 📊 **数据看板** | 生成量、成本、素材、任务状态 一目了然 | ✅ |
| 🔀 **混剪配置** | 标准混剪/A-B测试/多平台适配/多语言版本 | ✅ |

## 界面预览

### 首页控制台
![首页控制台](screenshots/01-首页控制台.png)

### 选题矩阵 — 一键生成爆款选题
![选题矩阵](screenshots/02-选题矩阵.png)

### ShotCraft 镜头卡库 — 104张配方卡
![镜头卡库](screenshots/03-镜头卡库.png)

### AI脚本生成 — DeepSeek驱动
![AI脚本生成](screenshots/04-AI脚本生成.png)

### 成本追踪 — API调用明细
![成本追踪](screenshots/05-成本追踪.png)

## 快速开始

```bash
# 1. 解压项目到任意目录
cd 视频自动化

# 2. 双击启动
start.bat
```

浏览器访问：**http://localhost:5000**

## 配置API Key

打开浏览器访问 `http://localhost:5000`，进入「系统设置」页面：

| Key | 用途 | 获取方式 |
|-----|------|----------|
| `deepseek` | AI脚本生成 | [硅基流动](https://www.siliconflow.cn) 注册免费领额度 |
| `dashscope` | 阿里云视频生成 | [DashScope](https://dashscope.aliyun.com) |
| `pixabay` | 免费素材 | [Pixabay API](https://pixabay.com/api/docs/) |
| `pexels` | 免费素材 | [Pexels API](https://www.pexels.com/api/) |

## 项目结构

```
视频自动化/
├── app.py                    # Flask 主应用（52个API端点）
├── requirements.txt          # Python 依赖
├── start.bat                 # 一键启动脚本（Windows）
├── check_env.bat             # 环境诊断脚本
├── README.md                 # 本文件
├── SKILL.md                  # 功能文档
├── .gitignore                # Git 忽略规则
│
├── modules/                  # 后端模块
│   ├── workflow_engine.py    # 工作流引擎
│   └── enhanced_features.py  # 增强功能
│
├── templates/
│   └── index.html            # Web 控制台（单页应用）
├── static/
│   ├── css/                  # 样式
│   └── js/
│       └── app.js            # 前端逻辑
│
├── video-shotcraft/          # 104张镜头卡 + 161条样片
│   └── api/
│       └── library.json
│
└── workspace/                # 工作区（运行后自动创建）
    ├── 01-生成成果/
    ├── 02-选题策划/
    ├── 03-素材库/
    ├── 04-脚本工具/
    ├── 05-第三方技能/
    ├── 06-运营日志/
    ├── 07-文档与配置/
    └── config/
```

## 核心API一览

### 系统状态
- `GET /api/system/status` — 环境检测
- `GET/POST /api/system/config` — 读取/保存配置
- `GET /api/system/history` — 操作历史

### 选题策划
- `GET /api/topics/daily` — 每日选题推荐
- `GET /api/topics/list` — 列出所有选题
- `POST /api/matrix/generate` — 生成选题矩阵
- `GET /api/matrix/categories` — 获取矩阵分类

### AI脚本生成
- `POST /api/script/generate` — AI生成完整脚本
- `POST /api/script/outline` — 生成脚本大纲
- `GET /api/script/templates` — 获取脚本模板

### Video ShotCraft 镜头卡
- `GET /api/shotcraft/library` — 获取完整镜头卡库（104张）
- `GET /api/shotcraft/search?q=...` — 搜索镜头卡
- `GET /api/shotcraft/categories` — 获取分类列表
- `POST /api/shotcraft/generate-plan` — 基于镜头卡生成分镜方案

### 素材库
- `GET /api/assets/list` — 素材库列表
- `POST /api/video/fingerprint` — 视频指纹检测
- `POST /api/video/duplicates` — 重复视频检测

### 成本追踪
- `GET /api/cost/summary` — 每日API调用成本汇总
- `POST /api/cost/add` — 记录API调用成本

### 数据看板
- `GET /api/dashboard/stats` — 数据看板统计
- `GET /api/mix/configs` — 混剪配置模板

## 商业变现路线

1. **个人创作者**：免费自用，每天节省2小时
2. **MCN机构**：¥99/月，批量生成100条视频
3. **企业定制**：按需定价，私有化部署
4. **Skill市场**：上传Kimi Skill市场，按调用量分成

## 开源与致谢

- **video-shotcraft**: [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
- **DeepSeek**: [硅基流动](https://www.siliconflow.cn)
- **Flask**: [palletsprojects.com](https://flask.palletsprojects.com)

---
*版本：2.0-整合版 | 2026-08-08*
