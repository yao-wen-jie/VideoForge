# 视频自动化 VideoForge

> **一句话出片**：选题 → AI脚本 → 镜头卡分镜 → 视频生成 → 多平台发布，全流程自动化。
> 整合 video-shotcraft 104张镜头配方卡 + 161条样片素材，海纳百川，好用为王。

---

## 快速开始（3分钟跑通）

### 方式一：全自动安装（推荐）

```bash
# 1. 克隆或解压项目到任意目录
cd 视频自动化

# 2. 双击启动
start.bat
```

启动后会自动：
- ✅ 检测 Python 环境
- ✅ 创建虚拟环境 `.venv`
- ✅ 安装依赖（Flask + requests）
- ✅ 初始化 `workspace/` 工作目录
- ✅ 启动 Web 控制台 `http://localhost:5000`

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
python -m venv .venv

# 2. 激活（Windows）
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化工作区
python -c "from pathlib import Path; p=Path('workspace'); [(p/d).mkdir(parents=True,exist_ok=True) for d in ['01-生成成果','02-选题策划','03-素材库/video','03-素材库/image','03-素材库/audio','04-脚本工具','05-第三方技能','06-运营日志','07-文档与配置','config']]"

# 5. 启动
python app.py
```

浏览器访问：**http://localhost:5000**

---

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

> ✅ = 开箱即用 | ⚠️ = 需要配置API Key或依赖外部工具

---

## 配置API Key（解锁AI功能）

打开浏览器访问 `http://localhost:5000`，进入「系统设置」页面：

| Key | 用途 | 获取方式 |
|-----|------|----------|
| `deepseek` | AI脚本生成 | [硅基流动](https://www.siliconflow.cn) 注册免费领额度 |
| `dashscope` | 阿里云视频生成 | [DashScope](https://dashscope.aliyun.com) |
| `seedance` | 视频生成 | [Seedance](https://seedance.io) |
| `pixabay` | 免费素材 | [Pixabay API](https://pixabay.com/api/docs/) |
| `pexels` | 免费素材 | [Pexels API](https://www.pexels.com/api/) |

**最低配置**：只需 `deepseek` Key，即可使用AI脚本生成功能（硅基流动注册送免费额度，足够个人使用）。

---

## 项目结构

```
视频自动化/
├── app.py                  # Flask 主应用（52个API端点）
├── requirements.txt        # Python 依赖
├── start.bat               # 一键启动脚本（Windows）
├── check_env.bat           # 环境诊断脚本
├── SKILL.md                # 本文档
│
├── modules/                # 后端模块
│   ├── workflow_engine.py  # 工作流引擎（任务管理、脚本执行）
│   └── enhanced_features.py # 增强功能（选题矩阵、AI脚本、素材库、看板）
│
├── templates/
│   └── index.html          # Web 控制台（单页应用，5大页面）
├── static/
│   ├── css/                # 样式
│   └── js/
│       └── app.js          # 前端逻辑（API调用 + 状态管理）
│
├── video-shotcraft/        # 104张镜头卡 + 161条样片
│   └── api/
│       └── library.json      # 镜头卡数据库
│
└── workspace/              # 工作区（运行后自动创建）
    ├── 01-生成成果/        # 生成的视频/图片
    ├── 02-选题策划/        # 选题记录
    ├── 03-素材库/          # 视频/图片/音频/脚本
    ├── 04-脚本工具/        # Python脚本（需从1.1复制或自建）
    ├── 05-第三方技能/      # 外部Skill
    ├── 06-运营日志/        # 成本/发布/日报
    ├── 07-文档与配置/      # 文档
    └── config/
        ├── topics_pool.json    # 选题池（运行后自动生成）
        └── scheduled_tasks.json # 定时任务
```

---

## 核心API一览

### 系统状态
- `GET /api/system/status` — 环境检测（Python/FFmpeg/GPU/API Keys）
- `GET/POST /api/system/config` — 读取/保存配置
- `GET /api/system/history` — 操作历史

### 选题策划
- `GET /api/topics/daily` — 每日选题推荐
- `GET /api/topics/list` — 列出所有选题
- `POST /api/matrix/generate` — 生成选题矩阵（情感/职场/科技/生活）
- `GET /api/matrix/categories` — 获取矩阵分类

### AI脚本生成
- `POST /api/script/generate` — AI生成完整脚本（DeepSeek驱动）
- `POST /api/script/outline` — 生成脚本大纲
- `GET /api/script/templates` — 获取脚本模板

### Video ShotCraft 镜头卡
- `GET /api/shotcraft/library` — 获取完整镜头卡库（104张）
- `GET /api/shotcraft/search?q=...` — 搜索镜头卡
- `GET /api/shotcraft/categories` — 获取分类列表
- `GET /api/shotcraft/card/<name>` — 单张镜头卡详情
- `POST /api/shotcraft/generate-plan` — 基于镜头卡生成分镜方案

### 素材库
- `GET /api/assets/list` — 素材库列表
- `GET /api/assets/stats` — 素材统计
- `POST /api/video/fingerprint` — 视频指纹检测
- `POST /api/video/duplicates` — 重复视频检测

### 成本追踪
- `GET /api/cost/summary` — 每日API调用成本汇总
- `POST /api/cost/add` — 记录API调用成本

### 智能导演
- `POST /api/director/plan` — 生成导演方案（dry-run）
- `POST /api/director/run` — 执行导演方案

### 工作流与工具集成
- `GET /api/workflow/scripts` — 列出可用脚本
- `POST /api/workflow/run` — 运行脚本
- `GET /api/workflow/task/<id>` — 任务详情
- `POST /api/workflow/task/<id>/kill` — 终止任务
- `GET /api/workflow/env-check` — 环境检查
- `POST /api/openmontage/run` — OpenMontage视频生成
- `POST /api/replicate/analyze` — 分析抖音爆款
- `POST /api/replicate/run` — 复刻爆款视频
- `POST /api/skill/parse` — 解析Kimi Skill
- `POST /api/skill/transcribe` — 语音转文字

### 任务管理
- `GET /api/tasks` — 所有任务状态
- `GET /api/task/<id>` — 单个任务状态
- `POST /api/task/<id>/kill` — 终止任务

### 定时任务
- `GET /api/schedule/list` — 定时任务列表
- `POST /api/schedule/add` — 添加定时任务
- `DELETE /api/schedule/delete/<task_id>` — 删除定时任务

### 数据看板
- `GET /api/dashboard/stats` — 数据看板统计
- `GET /api/mix/configs` — 混剪配置模板
- `GET /api/publish/stats` — 发布统计

### 文件与成果
- `GET /api/files/browse` — 浏览目录
- `GET /api/outputs` — 生成成果列表
- `GET /api/outputs/list` — 生成成果列表（V2）

---

## 使用流程示例

### 场景：从零生成一条30秒口播视频

1. **选题**：打开「选题矩阵」→ 选择"情感"分类 → 点击生成 → 获得10条选题
2. **脚本**：选择一条选题 → 进入「AI脚本」→ 点击"生成脚本" → DeepSeek返回完整口播稿
3. **分镜**：进入「镜头卡库」→ 搜索"开场" → 选择 brand-ink-open → 点击"生成分镜方案"
4. **素材**：进入「素材库」→ 上传视频/图片素材 → 系统提示可用素材
5. **生成**：配置API Key后 → 使用导演/生成工具 → 系统自动合成视频
6. **发布**：进入「数据看板」→ 查看生成成果 → 下载视频 → 上传各平台

> 配好 DeepSeek Key 后，步骤1-3可以全自动完成，真正实现"一句话出片"。

---

## 环境要求

| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| Python | 3.8+ | 必需 |
| Flask | 2.3+ | 必需，Web框架 |
| requests | 2.31+ | 必需，API调用 |
| FFmpeg | 任意 | 可选，视频处理 |
| GPU | NVIDIA | 可选，加速视频生成 |

---

## 故障排查

### 问题1：双击 start.bat 闪退
**解决**：先运行 `check_env.bat` 看诊断报告，通常是Python未安装或不在PATH中。

### 问题2：API返回"找不到脚本"
**解决**：脚本已内置为存根版本，位于 `workspace/04-脚本工具/` 目录。需要完整功能请自行接入 OpenMontage 等外部工具。

### 问题3：AI脚本生成失败
**解决**：未配置 DeepSeek API Key。去 [硅基流动](https://www.siliconflow.cn) 注册，获取 Key 后在系统设置中填入。

### 问题4：镜头卡库为空
**解决**：内置了104张镜头卡数据，无需额外配置。如果仍为空，检查 `video-shotcraft/api/library.json` 是否存在。

### 问题5：workspace目录未创建
**解决**：手动运行 `python -c "from pathlib import Path; p=Path('workspace'); [(p/d).mkdir(parents=True,exist_ok=True) for d in ['01-生成成果','02-选题策划','03-素材库/video','03-素材库/image','03-素材库/audio','04-脚本工具','05-第三方技能','06-运营日志','07-文档与配置','config']]"`

---

## 商业变现路线

1. **个人创作者**：免费自用，每天节省2小时
2. **MCN机构**：¥99/月，批量生成100条视频
3. **企业定制**：按需定价，私有化部署
4. **Skill市场**：将此Skill上传Kimi Skill市场，按调用量分成

---

## 开源与致谢

- **video-shotcraft**: [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) — 镜头配方卡系统
- **DeepSeek**: [硅基流动](https://www.siliconflow.cn) — AI脚本生成
- **Flask**: [palletsprojects.com](https://flask.palletsprojects.com) — Web框架

---

*最后更新：2026-08-08 | 版本：2.0-整合版*
