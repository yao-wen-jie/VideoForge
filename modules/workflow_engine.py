# -*- coding: utf-8 -*-
"""
视频自动化工作流引擎
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 工作流根目录（基于项目目录下的 workspace 文件夹）
_BASE = Path(__file__).resolve().parent.parent
_WORKSPACE = _BASE / "workspace"
WORKFLOW_ROOT = _WORKSPACE
SCRIPTS_DIR = WORKFLOW_ROOT / "04-脚本工具"
OUTPUTS_DIR = WORKFLOW_ROOT / "01-生成成果"
TOPICS_DIR = WORKFLOW_ROOT / "02-选题策划"
LOGS_DIR = WORKFLOW_ROOT / "06-运营日志"
DOCS_DIR = WORKFLOW_ROOT / "07-文档与配置"
SKILLS_DIR = WORKFLOW_ROOT / "05-第三方技能"
CONFIG_DIR = WORKFLOW_ROOT / "config"

# 运行中任务
RUNNING_TASKS: Dict[str, dict] = {}
TASK_LOCK = threading.Lock()
TASK_COUNTER = 0


# ---------------------------------------------------------------------------
# 脚本元数据
# ---------------------------------------------------------------------------

SCRIPT_REGISTRY = {
    "env_check": {
        "name": "环境检查",
        "file": "env_check.py",
        "desc": "检查 Python 环境、依赖包、FFmpeg 等是否就绪",
        "params": [],
        "icon": "🔧",
        "category": "诊断",
        "stub": True,
    },
    "daily_topic": {
        "name": "每日选题",
        "file": "daily_topic_selector.py",
        "desc": "从选题池中按规则选出今日候选选题",
        "params": [
            {"name": "count", "label": "选题数量", "type": "number", "default": 3, "min": 1, "max": 10},
            {"name": "category", "label": "分类筛选", "type": "text", "default": "", "placeholder": "留空为全部"},
        ],
        "icon": "📋",
        "category": "内容",
        "stub": True,
    },
    "batch_generate": {
        "name": "每日视频生成",
        "file": "batch_generate.py",
        "desc": "根据选题调用 OpenMontage 生成视频（含预算检查）",
        "params": [
            {"name": "topic_id", "label": "选题ID", "type": "text", "default": "", "placeholder": "留空则自动选"},
            {"name": "mode", "label": "生成模式", "type": "select", "default": "auto", "options": ["auto", "s2v", "mix", "pip"]},
        ],
        "icon": "🎬",
        "category": "生成",
        "stub": True,
    },
    "make_cards": {
        "name": "生成流程卡片",
        "file": "make_cards.py",
        "desc": "生成画中画卡片（脚本卡/流程卡/时间线卡/真相弹卡）",
        "params": [],
        "icon": "🃏",
        "category": "工具",
        "stub": True,
    },
    "make_cards2": {
        "name": "生成流程卡片 V2",
        "file": "make_cards2.py",
        "desc": "V2版卡片生成，支持更多样式",
        "params": [],
        "icon": "🃏",
        "category": "工具",
        "stub": True,
    },
    "error_scan": {
        "name": "错误扫描",
        "file": "error_scanner.py",
        "desc": "扫描工作流中常见的配置错误和缺失文件",
        "params": [],
        "icon": "🔍",
        "category": "诊断",
        "stub": True,
    },
    "cost_summary": {
        "name": "成本汇总",
        "file": "cost_tracker.py",
        "desc": "汇总今日/本周/本月的 API 调用成本",
        "params": [
            {"name": "days", "label": "天数", "type": "number", "default": 7, "min": 1, "max": 90},
        ],
        "icon": "💰",
        "category": "运营",
        "stub": True,
    },
    "parse_douyin": {
        "name": "抖音解析",
        "file": "parse_douyin.py",
        "desc": "解析抖音视频链接，提取文案和音频",
        "params": [
            {"name": "url", "label": "抖音链接", "type": "text", "default": "", "placeholder": "粘贴抖音分享链接"},
        ],
        "icon": "🎵",
        "category": "内容",
        "stub": True,
    },
    "replicate_viral": {
        "name": "爆款复刻",
        "file": "replicate_viral.py",
        "desc": "根据分析好的爆款视频，复刻生成同款",
        "params": [
            {"name": "report", "label": "分析报告路径", "type": "text", "default": "", "placeholder": "analysis_report.json 路径"},
        ],
        "icon": "🔥",
        "category": "生成",
        "stub": True,
    },
    "lipsync_batch": {
        "name": "唇同步批量",
        "file": "lipsync_batch.py",
        "desc": "批量生成唇同步视频",
        "params": [
            {"name": "script", "label": "脚本JSON", "type": "text", "default": "", "placeholder": "脚本文件路径"},
        ],
        "icon": "👄",
        "category": "生成",
        "stub": True,
    },
}


# ---------------------------------------------------------------------------
# 任务管理
# ---------------------------------------------------------------------------

def _next_task_id() -> str:
    global TASK_COUNTER
    TASK_COUNTER += 1
    return f"wf_{int(time.time())}_{TASK_COUNTER}"


def run_script(script_key: str, params: dict = None, user: str = "web") -> dict:
    """运行工作流脚本，返回任务信息"""
    meta = SCRIPT_REGISTRY.get(script_key)
    if not meta:
        return {"error": f"未知脚本: {script_key}"}

    script_path = SCRIPTS_DIR / meta["file"]
    if not script_path.exists():
        return {"error": f"脚本文件不存在: {script_path}"}

    # 构建命令
    cmd = [sys.executable, str(script_path)]

    # 添加参数
    if params:
        for p in meta.get("params", []):
            name = p["name"]
            val = params.get(name)
            if val is not None and str(val).strip() != "":
                # 根据参数类型处理
                if p.get("type") == "select":
                    cmd.extend([f"--{name}", str(val)])
                elif p.get("type") == "number":
                    cmd.extend([f"--{name}", str(int(val))])
                else:
                    cmd.extend([f"--{name}", str(val)])

    task_id = _next_task_id()

    # 启动进程
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(SCRIPTS_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except Exception as e:
        return {"error": f"启动失败: {e}"}

    task = {
        "id": task_id,
        "script_key": script_key,
        "script_name": meta["name"],
        "pid": proc.pid,
        "cmd": " ".join(cmd),
        "status": "running",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "output": [],
        "user": user,
        "params": params or {},
    }

    with TASK_LOCK:
        RUNNING_TASKS[task_id] = task

    # 启动输出收集线程
    def _collect_output():
        try:
            for line in proc.stdout:
                line = line.rstrip("\n\r")
                with TASK_LOCK:
                    if task_id in RUNNING_TASKS:
                        RUNNING_TASKS[task_id]["output"].append(line)
                        # 保留最近 500 行
                        if len(RUNNING_TASKS[task_id]["output"]) > 500:
                            RUNNING_TASKS[task_id]["output"] = RUNNING_TASKS[task_id]["output"][-500:]
        except Exception:
            pass
        finally:
            proc.wait()
            with TASK_LOCK:
                if task_id in RUNNING_TASKS:
                    RUNNING_TASKS[task_id]["status"] = "completed" if proc.returncode == 0 else "failed"
                    RUNNING_TASKS[task_id]["returncode"] = proc.returncode
                    RUNNING_TASKS[task_id]["end_time"] = datetime.now().isoformat()

    t = threading.Thread(target=_collect_output, daemon=True)
    t.start()

    return {"task_id": task_id, "status": "running"}


def get_task(task_id: str) -> Optional[dict]:
    with TASK_LOCK:
        t = RUNNING_TASKS.get(task_id)
        if t:
            return dict(t)
    return None


def kill_task(task_id: str) -> dict:
    with TASK_LOCK:
        t = RUNNING_TASKS.get(task_id)
        if not t:
            return {"error": "任务不存在"}
        pid = t.get("pid")
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                t["status"] = "killed"
                return {"success": True}
            except Exception as e:
                return {"error": str(e)}
    return {"error": "任务没有PID"}


def list_tasks(limit: int = 50) -> List[dict]:
    with TASK_LOCK:
        tasks = sorted(RUNNING_TASKS.values(), key=lambda x: x["start_time"], reverse=True)
    # 深拷贝并截断输出
    result = []
    for t in tasks[:limit]:
        tc = dict(t)
        tc["output"] = tc["output"][-100:]  # 只返回最近100行
        result.append(tc)
    return result


# ---------------------------------------------------------------------------
# 文件管理
# ---------------------------------------------------------------------------

def list_directory(path: str, pattern: str = "*") -> List[dict]:
    """列出目录内容"""
    p = Path(path)
    if not p.exists():
        return []
    results = []
    for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        try:
            stat = item.stat()
            results.append({
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "ext": item.suffix.lower(),
            })
        except Exception:
            pass
    return results


def list_outputs() -> List[dict]:
    """列出生成成果"""
    if not OUTPUTS_DIR.exists():
        return []
    results = []
    for item in sorted(OUTPUTS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            stat = item.stat()
            info = {
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            }
            if item.is_dir():
                # 查找视频文件
                videos = list(item.glob("*.mp4")) + list(item.glob("*.mov")) + list(item.glob("*.avi"))
                images = list(item.glob("*.jpg")) + list(item.glob("*.png"))
                info["videos"] = [v.name for v in videos]
                info["images"] = [i.name for i in images]
                info["video_count"] = len(videos)
                info["image_count"] = len(images)
                # 查找元数据
                meta = item / "meta.json"
                if meta.exists():
                    try:
                        with open(meta, "r", encoding="utf-8") as f:
                            info["meta"] = json.load(f)
                    except Exception:
                        pass
            results.append(info)
        except Exception:
            pass
    return results


# ---------------------------------------------------------------------------
# 选题管理
# ---------------------------------------------------------------------------

def load_topics_pool() -> dict:
    """加载选题池"""
    pool_file = CONFIG_DIR / "topics_pool.json"
    if pool_file.exists():
        try:
            with open(pool_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"categories": {}}


def save_topics_pool(data: dict) -> bool:
    """保存选题池"""
    pool_file = CONFIG_DIR / "topics_pool.json"
    try:
        pool_file.parent.mkdir(parents=True, exist_ok=True)
        with open(pool_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存选题池失败: {e}")
        return False


def list_topics(category: str = None) -> List[dict]:
    """列出所有选题"""
    data = load_topics_pool()
    topics = []
    for cat_key, cat in data.get("categories", {}).items():
        if category and cat_key != category:
            continue
        for t in cat.get("topics", []):
            t["category"] = cat_key
            t["category_name"] = cat.get("name", cat_key)
            topics.append(t)
    return topics


# ---------------------------------------------------------------------------
# 日志管理
# ---------------------------------------------------------------------------

def load_daily_selections() -> List[dict]:
    """加载每日选题记录"""
    log_file = LOGS_DIR / "daily_selections.json"
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def load_cost_log() -> List[dict]:
    """加载成本日志"""
    log_file = LOGS_DIR / "cost_log.json"
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def get_cost_summary(days: int = 7) -> dict:
    """获取成本汇总"""
    logs = load_cost_log()
    total = 0.0
    by_service = {}
    recent_logs = []
    now = datetime.now()
    for entry in logs:
        try:
            d = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
            if (now - d).days <= days:
                cost = entry.get("cost", 0)
                total += cost
                recent_logs.append(entry)
                svc = entry.get("service", "unknown")
                by_service[svc] = by_service.get(svc, 0) + cost
        except Exception:
            pass
    return {
        "total": round(total, 2),
        "days": days,
        "count": len(recent_logs),
        "by_service": {k: round(v, 2) for k, v in by_service.items()},
        "entries": recent_logs[-20:],  # 最近20条
    }


# ---------------------------------------------------------------------------
# 环境检查
# ---------------------------------------------------------------------------

def check_environment() -> dict:
    """检查工作环境"""
    checks = {
        "workflow_exists": WORKFLOW_ROOT.exists(),
        "scripts_dir_exists": SCRIPTS_DIR.exists(),
        "outputs_dir_exists": OUTPUTS_DIR.exists(),
        "topics_pool_exists": (CONFIG_DIR / "topics_pool.json").exists(),
    }

    # Python 版本
    checks["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # FFmpeg（动态查找）
    ffmpeg = os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")
    if not ffmpeg:
        # 尝试常见路径
        for candidate in [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        ]:
            if Path(candidate).exists():
                ffmpeg = candidate
                break
    checks["ffmpeg_exists"] = bool(ffmpeg) and Path(ffmpeg).exists()
    checks["ffmpeg_path"] = ffmpeg

    # OpenMontage（可选，从环境变量或配置读取）
    om_path = os.environ.get("OPENMONTAGE_ROOT") or os.environ.get("OPENMONTAGE_PATH")
    om = Path(om_path) if om_path else None
    checks["openmontage_exists"] = om.exists() if om else False
    checks["openmontage_venv"] = (om / ".venv/Scripts/python.exe").exists() if om else False

    # GPU
    try:
        subprocess.run(["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        checks["gpu"] = True
    except Exception:
        checks["gpu"] = False

    # 磁盘空间
    try:
        total, used, free = shutil.disk_usage("C:/")
        checks["disk_free_gb"] = round(free / (1024**3), 1)
    except Exception:
        checks["disk_free_gb"] = -1

    # 总体状态
    checks["healthy"] = all([
        checks["workflow_exists"],
        checks["scripts_dir_exists"],
        checks["ffmpeg_exists"],
    ])

    return checks
