# -*- coding: utf-8 -*-
"""
视频自动化 Web 控制台 —— 增强功能模块
海纳百川：整合全网竞品精华功能
"""
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 工作流根目录（基于项目目录下的 workspace 文件夹）
_BASE = Path(__file__).resolve().parent.parent
_WORKSPACE = _BASE / "workspace"
WORKFLOW_ROOT = _WORKSPACE
CONFIG_DIR = WORKFLOW_ROOT / "config"
OUTPUTS_DIR = WORKFLOW_ROOT / "01-生成成果"
LOGS_DIR = WORKFLOW_ROOT / "06-运营日志"
ASSETS_DIR = WORKFLOW_ROOT / "03-素材库"
SCRIPTS_DIR = WORKFLOW_ROOT / "04-脚本工具"

# 确保目录存在
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "video").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "image").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "audio").mkdir(parents=True, exist_ok=True)
(ASSETS_DIR / "script").mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
(ASSETS_DIR / "video").mkdir(exist_ok=True)
(ASSETS_DIR / "image").mkdir(exist_ok=True)
(ASSETS_DIR / "audio").mkdir(exist_ok=True)
(ASSETS_DIR / "script").mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. 选题矩阵生成器
# ---------------------------------------------------------------------------

TOPIC_MATRIX_TEMPLATES = {
    "emotional": {
        "targets": ["打工人", "创业者", "学生党", "宝妈", "独居青年", "中年人"],
        "pain_points": ["焦虑", "孤独", "迷茫", "压力", "不被理解", "睡眠不足", "经济紧张"],
        "solutions": ["接纳", "放下", "改变", "坚持", "倾诉", "断舍离", "自我关怀"],
        "hooks": ["你有没有过", "凌晨三点", "没人告诉过你", "成年人的崩溃", "扎心了"],
    },
    "career": {
        "targets": ["应届生", "职场新人", "中层管理", "自由职业者", "技术人", "销售"],
        "pain_points": ["晋升瓶颈", "薪资倒挂", "35岁危机", "能力不足", "沟通障碍", "效率低下"],
        "solutions": ["技能升级", "人脉拓展", "跳槽", "副业", "AI提效", "认知升级"],
        "hooks": ["工作5年没晋升", "工资买的不是你的命", "真正厉害的人", "穷人思维和富人思维"],
    },
    "tech": {
        "targets": ["程序员", "自媒体人", "设计师", "产品经理", "运营", "创业者"],
        "pain_points": ["效率低", "工具不会用", "内容枯竭", "同质化严重", "流量焦虑", "变现困难"],
        "solutions": ["AI自动化", "工具链", "矩阵运营", "爆款复刻", "数据分析", "私域转化"],
        "hooks": ["这条视频是AI做的", "一个人一天50条", "从脚本到成片零人工", "零拍摄零出镜"],
    },
    "life": {
        "targets": ["都市白领", "小城青年", "北漂/沪漂", "宝妈", "退休父母", "大学生"],
        "pain_points": ["生活单调", "社交匮乏", "健康隐患", "亲情疏远", "没有目标", "经济压力"],
        "solutions": ["培养爱好", "陪伴家人", "健康管理", "学习成长", "理财规划", "心态调整"],
        "hooks": ["30岁以后才明白", "父母变老的速度", "原来这才是", "人生最重要的一课"],
    },
}


def generate_topic_matrix(category: str, count: int = 10) -> List[dict]:
    """生成选题矩阵"""
    tpl = TOPIC_MATRIX_TEMPLATES.get(category, TOPIC_MATRIX_TEMPLATES["emotional"])
    results = []
    used = set()
    max_attempts = count * 5
    attempts = 0

    while len(results) < count and attempts < max_attempts:
        attempts += 1
        target = random.choice(tpl["targets"])
        pain = random.choice(tpl["pain_points"])
        solution = random.choice(tpl["solutions"])
        hook = random.choice(tpl["hooks"])

        # 生成标题
        title_patterns = [
            f"{target}的{pain}，只有{solution}能解决",
            f"{hook}：{target}的{pain}真相",
            f"{target}为什么总是{pain}？因为你不懂{solution}",
            f"{hook}，{target}的{solution}指南",
            f"{target}必看：{pain}的本质是缺{solution}",
        ]
        title = random.choice(title_patterns)

        if title in used:
            continue
        used.add(title)

        # 生成钩子
        hook_patterns = [
            f"{hook}，{target}的{pain}有多真实？",
            f"如果你也是{target}，这条视频建议你看到最后",
            f"{hook}，{target}才懂的痛",
        ]

        results.append({
            "title": title,
            "hook": random.choice(hook_patterns),
            "target": target,
            "pain_point": pain,
            "solution": solution,
            "category": category,
            "priority": random.randint(3, 5),
            "tags": [target, pain, solution],
            "id": f"MAT_{category.upper()}_{len(results)+1:03d}",
        })

    return results


def get_matrix_categories() -> List[dict]:
    """获取选题矩阵分类"""
    return [
        {"key": k, "name": v["targets"][0][:2] + "等", "count": len(v["targets"])}
        for k, v in TOPIC_MATRIX_TEMPLATES.items()
    ]


# ---------------------------------------------------------------------------
# 2. AI 脚本批量生成
# ---------------------------------------------------------------------------

SCRIPT_TEMPLATES = {
    "hook_scene_turn_punchline_cta": {
        "name": "黄金五段式",
        "structure": ["hook", "scene", "turn", "punchline", "cta"],
        "desc": "钩子→场景→转折→金句→行动号召，最通用的爆款结构",
    },
    "problem_agitate_solution": {
        "name": "痛点放大式",
        "structure": ["problem", "agitate", "solution", "proof", "cta"],
        "desc": "问题→放大痛点→解决方案→证据→行动号召",
    },
    "story_lesson_action": {
        "name": "故事启发式",
        "structure": ["story", "lesson", "action"],
        "desc": "讲故事→提炼道理→引导行动",
    },
    "data_insight_prediction": {
        "name": "数据洞察式",
        "structure": ["data", "insight", "prediction", "cta"],
        "desc": "数据→洞察→预判→行动",
    },
}


def generate_script_outline(topic: str, template: str = "hook_scene_turn_punchline_cta",
                            duration: int = 30, style: str = "口播") -> dict:
    """生成脚本大纲"""
    tpl = SCRIPT_TEMPLATES.get(template, SCRIPT_TEMPLATES["hook_scene_turn_punchline_cta"])
    segments = []
    segment_duration = duration // len(tpl["structure"])

    for i, seg_type in enumerate(tpl["structure"]):
        segments.append({
            "type": seg_type,
            "duration": segment_duration,
            "start": i * segment_duration,
            "end": (i + 1) * segment_duration,
            "prompt": _get_segment_prompt(seg_type, topic, style),
        })

    return {
        "topic": topic,
        "template": tpl["name"],
        "template_key": template,
        "duration": duration,
        "style": style,
        "segments": segments,
        "notes": [
            "前3秒必须有钩子（提问/痛点/反常识）",
            "口语化表达，避免书面语",
            "结尾带行动引导（点赞/关注/评论）",
            f"建议时长：{duration}秒",
        ],
    }


def _get_segment_prompt(seg_type: str, topic: str, style: str) -> str:
    prompts = {
        "hook": f"用一句话抓住注意力，关于'{topic}'。要求：反常识/提问题/给数据",
        "scene": f"描述一个与'{topic}'相关的具体场景，让观众产生代入感",
        "turn": f"在'{topic}'上制造一个认知转折或情绪反转",
        "punchline": f"给出一个关于'{topic}'的金句或核心观点，让人想截图",
        "cta": f"引导观众行动：关注/评论/私信/点赞，与'{topic}'相关",
        "problem": f"提出与'{topic}'相关的核心问题",
        "agitate": f"放大'{topic}'的痛点，让观众感到共鸣",
        "solution": f"给出'{topic}'的解决方案",
        "proof": f"用一个案例或数据证明'{topic}'的解决方案有效",
        "story": f"讲一个与'{topic}'相关的故事",
        "lesson": f"从'{topic}'的故事中提炼出一个道理",
        "action": f"引导观众因为'{topic}'而采取某个行动",
        "data": f"给出一个与'{topic}'相关的惊人数据",
        "insight": f"从数据中发现关于'{topic}'的洞察",
        "prediction": f"基于'{topic}'的趋势给出一个预判",
    }
    return prompts.get(seg_type, f"围绕'{topic}'展开")


# ---------------------------------------------------------------------------
# 3. 素材库管理
# ---------------------------------------------------------------------------

def list_assets(asset_type: str = None) -> List[dict]:
    """列出素材库内容"""
    results = []
    type_map = {
        "video": ["*.mp4", "*.mov", "*.avi", "*.mkv"],
        "image": ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.gif"],
        "audio": ["*.mp3", "*.wav", "*.m4a", "*.ogg"],
        "script": ["*.json", "*.txt", "*.md"],
    }

    if asset_type and asset_type in type_map:
        dirs = [(asset_type, ASSETS_DIR / asset_type, type_map[asset_type])]
    else:
        dirs = [(t, ASSETS_DIR / t, pats) for t, pats in type_map.items()]

    for type_name, dir_path, patterns in dirs:
        if not dir_path.exists():
            continue
        for pattern in patterns:
            for f in sorted(dir_path.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    stat = f.stat()
                    results.append({
                        "name": f.name,
                        "path": str(f),
                        "type": type_name,
                        "size": stat.st_size,
                        "size_human": _human_size(stat.st_size),
                        "mtime": stat.st_mtime,
                        "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                except Exception:
                    pass

    return results


def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ---------------------------------------------------------------------------
# 4. 视频去重/指纹检测
# ---------------------------------------------------------------------------

def get_video_fingerprint(video_path: str) -> dict:
    """获取视频指纹信息（用于去重检测）"""
    p = Path(video_path)
    if not p.exists():
        return {"error": "文件不存在"}

    try:
        stat = p.stat()
        # 使用 ffprobe 获取视频信息
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration,bit_rate,size:stream=codec_name,width,height,avg_frame_rate",
             "-of", "json", str(p)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        info = json.loads(result.stdout) if result.returncode == 0 else {}

        # 计算文件指纹（前1MB的MD5）
        md5_hash = ""
        try:
            import hashlib
            h = hashlib.md5()
            with open(p, "rb") as f:
                h.update(f.read(1024 * 1024))
            md5_hash = h.hexdigest()[:16]
        except Exception:
            pass

        return {
            "file": str(p),
            "name": p.name,
            "size": stat.st_size,
            "size_human": _human_size(stat.st_size),
            "mtime": stat.st_mtime,
            "md5_preview": md5_hash,
            "format": info.get("format", {}),
            "streams": info.get("streams", []),
        }
    except Exception as e:
        return {"error": str(e)}


def check_duplicate_videos(directory: str = None) -> List[dict]:
    """扫描目录检测重复视频"""
    if directory is None:
        directory = OUTPUTS_DIR

    p = Path(directory)
    if not p.exists():
        return []

    fingerprints = {}
    duplicates = []

    for video in p.rglob("*.mp4"):
        fp = get_video_fingerprint(str(video))
        md5 = fp.get("md5_preview", "")
        if not md5:
            continue

        if md5 in fingerprints:
            duplicates.append({
                "original": fingerprints[md5],
                "duplicate": str(video),
                "confidence": "high",
            })
        else:
            fingerprints[md5] = str(video)

    return duplicates


# ---------------------------------------------------------------------------
# 5. 定时任务队列
# ---------------------------------------------------------------------------

SCHEDULED_TASKS_FILE = CONFIG_DIR / "scheduled_tasks.json"


def load_scheduled_tasks() -> List[dict]:
    if SCHEDULED_TASKS_FILE.exists():
        try:
            with open(SCHEDULED_TASKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_scheduled_tasks(tasks: List[dict]) -> bool:
    try:
        SCHEDULED_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULED_TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def add_scheduled_task(name: str, script_key: str, params: dict,
                       schedule: str, enabled: bool = True) -> dict:
    """添加定时任务
    schedule: cron表达式或特定格式
    """
    tasks = load_scheduled_tasks()
    task = {
        "id": f"sch_{int(time.time())}_{len(tasks)}",
        "name": name,
        "script_key": script_key,
        "params": params,
        "schedule": schedule,
        "enabled": enabled,
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "run_count": 0,
    }
    tasks.append(task)
    save_scheduled_tasks(tasks)
    return task


def delete_scheduled_task(task_id: str) -> bool:
    tasks = load_scheduled_tasks()
    new_tasks = [t for t in tasks if t["id"] != task_id]
    if len(new_tasks) != len(tasks):
        save_scheduled_tasks(new_tasks)
        return True
    return False


# ---------------------------------------------------------------------------
# 6. 数据看板
# ---------------------------------------------------------------------------

def get_dashboard_stats() -> dict:
    """获取综合数据看板统计"""
    stats = {
        "generated_at": datetime.now().isoformat(),
        "outputs": {},
        "costs": {},
        "tasks": {},
        "assets": {},
    }

    # 生成成果统计
    if OUTPUTS_DIR.exists():
        videos = list(OUTPUTS_DIR.rglob("*.mp4"))
        images = list(OUTPUTS_DIR.rglob("*.jpg")) + list(OUTPUTS_DIR.rglob("*.png"))
        total_size = sum(f.stat().st_size for f in videos if f.exists())
        stats["outputs"] = {
            "video_count": len(videos),
            "image_count": len(images),
            "total_size_gb": round(total_size / (1024**3), 2),
            "recent_7d": len([v for v in videos if v.exists() and
                              (datetime.now() - datetime.fromtimestamp(v.stat().st_mtime)).days <= 7]),
        }

    # 成本统计
    cost_file = LOGS_DIR / "cost_log.json"
    if cost_file.exists():
        try:
            with open(cost_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
            total_cost = sum(e.get("cost", 0) for e in logs)
            today = datetime.now().strftime("%Y-%m-%d")
            today_cost = sum(e.get("cost", 0) for e in logs if e.get("date", "").startswith(today))
            stats["costs"] = {
                "total_all_time": round(total_cost, 2),
                "today": round(today_cost, 2),
                "entry_count": len(logs),
                "avg_per_video": round(total_cost / max(len(logs), 1), 2),
            }
        except Exception:
            pass

    # 素材统计
    assets = list_assets()
    stats["assets"] = {
        "total": len(assets),
        "by_type": {},
    }
    for a in assets:
        t = a["type"]
        stats["assets"]["by_type"][t] = stats["assets"]["by_type"].get(t, 0) + 1

    # 任务统计
    tasks = load_scheduled_tasks()
    stats["tasks"] = {
        "scheduled_total": len(tasks),
        "scheduled_enabled": sum(1 for t in tasks if t.get("enabled")),
    }

    return stats


# ---------------------------------------------------------------------------
# 7. 批量混剪配置
# ---------------------------------------------------------------------------

def get_mix_configs() -> List[dict]:
    """获取混剪配置模板"""
    return [
        {
            "id": "mix_standard",
            "name": "标准混剪",
            "desc": "同一文案，多组素材轮换，生成3-5个差异化版本",
            "params": {
                "versions": 5,
                "bgm_rotate": True,
                "subtitle_style_rotate": True,
                "transition_random": True,
            },
        },
        {
            "id": "mix_ab_test",
            "name": "A/B测试混剪",
            "desc": "同一素材，不同开头钩子，测试哪种更吸引点击",
            "params": {
                "versions": 3,
                "hook_variants": ["提问式", "数据式", "反常识式"],
                "same_visual": True,
            },
        },
        {
            "id": "mix_multi_platform",
            "name": "多平台适配",
            "desc": "一条视频，生成抖音/快手/B站/小红书不同尺寸和风格版本",
            "params": {
                "platforms": ["douyin_9_16", "kuaishou_9_16", "bilibili_16_9", "xiaohongshu_3_4"],
                "auto_crop": True,
                "watermark": True,
            },
        },
        {
            "id": "mix_language",
            "name": "多语言版本",
            "desc": "同一视频，生成中文/英文/日文等多语言配音版本",
            "params": {
                "languages": ["zh-CN", "en-US", "ja-JP"],
                "voice_style": "natural",
                "auto_subtitle": True,
            },
        },
    ]


# ---------------------------------------------------------------------------
# 8. DeepSeek API 脚本生成
# ---------------------------------------------------------------------------

def generate_script_with_deepseek(topic: str, style: str = "口播", duration: int = 30,
                                   api_key: str = None) -> dict:
    """使用 DeepSeek API 生成脚本"""
    if not api_key:
        return {"error": "未配置 DeepSeek API Key"}

    try:
        import requests

        prompt = f"""你是短视频爆款脚本专家。请为以下选题创作一条{duration}秒的{style}类视频脚本：

视频主题：{topic}

脚本结构要求：
1. 开头（0-5秒）：钩子，用冲突/反常识/数据抓住注意力
2. 中间（5-{duration-15}秒）：干货内容，2-3个要点，口语化表达
3. 结尾（最后15秒）：行动号召，引导点赞/关注/评论

输出格式：
【画面描述】一句话描述此时画面
【口播文案】主播说的话（纯口语，不要书面语）
【字幕】关键字幕文字

请输出完整脚本。"""

        response = requests.post(
            "https://api.siliconflow.cn/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8,
                "max_tokens": 2000,
            },
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {
                "topic": topic,
                "style": style,
                "duration": duration,
                "script": content,
                "source": "deepseek-v3",
            }
        else:
            return {"error": f"API返回错误: {response.status_code}", "detail": response.text}

    except Exception as e:
        return {"error": f"调用失败: {str(e)}"}


# ---------------------------------------------------------------------------
# 9. 发布记录管理
# ---------------------------------------------------------------------------

def load_publish_log() -> List[dict]:
    """加载发布记录"""
    log_file = LOGS_DIR / "publish_log.csv"
    if not log_file.exists():
        return []

    results = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > 1:
            # 简单CSV解析
            for line in lines[1:]:
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    results.append({
                        "date": parts[0],
                        "platform": parts[1],
                        "video": parts[2],
                        "status": parts[3],
                    })
    except Exception:
        pass
    return results


def get_publish_stats() -> dict:
    """获取发布统计"""
    logs = load_publish_log()
    platforms = {}
    for log in logs:
        p = log.get("platform", "unknown")
        platforms[p] = platforms.get(p, 0) + 1

    return {
        "total_published": len(logs),
        "by_platform": platforms,
        "recent": logs[-10:] if logs else [],
    }
