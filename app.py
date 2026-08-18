#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频自动化 Web 控制台 —— Video ShotCraft 整合模块
基于 video-shotcraft (Vincentwei1021/video-shotcraft) 的镜头配方卡系统
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread

# 修复 Windows Git Bash 等终端的 UTF-8 编码问题
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from flask import Flask, jsonify, render_template, request
# -*- coding: utf-8 -*-
"""
视频自动化 Web 控制台 —— Video ShotCraft 整合模块
基于 video-shotcraft (Vincentwei1021/video-shotcraft) 的镜头配方卡系统
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Thread

from flask import Flask, jsonify, render_template, request

# 工作流引擎
sys.path.insert(0, str(Path(__file__).resolve().parent / "modules"))
from workflow_engine import (
    SCRIPT_REGISTRY,
    WORKFLOW_ROOT, SCRIPTS_DIR, OUTPUTS_DIR, TOPICS_DIR, LOGS_DIR,
    run_script, get_task, kill_task, list_tasks,
    list_directory, list_outputs,
    load_topics_pool, save_topics_pool, list_topics,
    load_daily_selections, load_cost_log, get_cost_summary,
    check_environment,
)
# 增强功能模块
from enhanced_features import (
    generate_topic_matrix, get_matrix_categories,
    generate_script_outline, SCRIPT_TEMPLATES, generate_script_with_deepseek,
    list_assets, get_video_fingerprint, check_duplicate_videos,
    load_scheduled_tasks, save_scheduled_tasks, add_scheduled_task, delete_scheduled_task,
    get_dashboard_stats, get_mix_configs, load_publish_log, get_publish_stats,
)
# 配音模块
from voiceforge_tts import (
    synthesize, get_engine_status, get_all_voices,
    list_reference_voices, save_reference_audio, delete_reference_voice,
    VOICE_OUTPUT_DIR, VOICE_DIR,
)


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
HISTORY_FILE = BASE_DIR / "history.json"

DEFAULT_CONFIG = {
    "workflow_root": "",
    "openmontage_root": "",
    "vibefilming_root": "",
    "skills_root": "",
    "output_dir": "",
    "daily_budget": 50.0,
    "api_keys": {
        "dashscope": "",
        "deepseek": "",
        "openai": "",
        "elevenlabs": "",
        "google": "",
        "pixabay": "",
        "pexels": "",
        "seedance": "",
    },
    "paths": {
        "ffmpeg": "ffmpeg",
        "python": "",
    },
    # video-shotcraft 配置
    "shotcraft": {
        "github_owner": "Vincentwei1021",
        "github_repo": "video-shotcraft",
        "gallery_url": "https://vincentwei1021.github.io/video-shotcraft/",
        "enabled": True,
    },
}

# 动态路径默认值（基于 BASE_DIR，不硬编码到配置文件）
PATH_DEFAULTS = {
    "workflow_root": lambda: str(BASE_DIR / "workspace"),
    "openmontage_root": lambda: str(BASE_DIR / "workspace" / "OpenMontage"),
    "vibefilming_root": lambda: str(BASE_DIR / "workspace" / "Vibefilming"),
    "skills_root": lambda: str(BASE_DIR / "skills"),
    "output_dir": lambda: str(BASE_DIR / "workspace" / "01-生成成果"),
}


def _resolve_config_paths(cfg):
    """将配置中的空路径自动填充为基于 BASE_DIR 的动态默认值，确保跨机器兼容。"""
    for key, default_fn in PATH_DEFAULTS.items():
        val = cfg.get(key)
        if not val or not str(val).strip():
            cfg[key] = default_fn()
    paths = cfg.get("paths", {})
    if not paths.get("python"):
        paths["python"] = sys.executable
    return cfg


def _strip_config_paths(cfg):
    """保存配置前，将等于默认值的绝对路径替换为空字符串，确保跨机器兼容。"""
    save_cfg = {k: v for k, v in cfg.items()}
    for key, default_fn in PATH_DEFAULTS.items():
        if save_cfg.get(key) == default_fn():
            save_cfg[key] = ""
    paths = save_cfg.get("paths", {})
    if paths.get("python") == sys.executable:
        paths["python"] = ""
    return save_cfg


def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
            cfg.update(user_cfg)
    return _resolve_config_paths(cfg)


def save_config(cfg):
    save_cfg = _strip_config_paths(cfg)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(save_cfg, f, ensure_ascii=False, indent=2)


CONFIG = load_config()


def get_script_path(name):
    """获取脚本工具目录下的脚本路径"""
    return BASE_DIR / "tools" / name


def get_om_venv_python():
    """获取脚本工具目录下的脚本路径"""
    return BASE_DIR / "tools" / name
    """获取脚本工具目录下的脚本路径"""
    root = Path(CONFIG["workflow_root"])
    return root / "04-脚本工具" / name


def get_om_venv_python():
    """获取 OpenMontage 虚拟环境 Python"""
    root = Path(CONFIG["openmontage_root"])
    return root / ".venv" / "Scripts" / "python.exe"


# ---------------------------------------------------------------------------
# Flask App
# ---------------------------------------------------------------------------

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["JSON_AS_ASCII"] = False

# 全局任务状态存储
TASKS = {}

# video-shotcraft 镜头卡缓存
SHOTCRAFT_LIBRARY = None
SHOTCRAFT_LIBRARY_LOADED_AT = 0


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def _run_subprocess(cmd, cwd=None, task_id=None):
    """运行脚本并实时返回输出（本地辅助函数）"""
    """运行脚本并实时返回输出"""
    # 强制子进程使用 UTF-8 编码，避免 Windows 中文系统 GBK 崩溃
    _env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    def target():
        try:
            proc = subprocess.Popen(
                [str(c) for c in cmd],
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=_env,
            )
            TASKS[task_id]["pid"] = proc.pid
            output = []
            for line in proc.stdout:
                line = line.rstrip()
                output.append(line)
                TASKS[task_id]["output"] = "\n".join(output)
            proc.wait()
            TASKS[task_id]["status"] = "done" if proc.returncode == 0 else "error"
            TASKS[task_id]["returncode"] = proc.returncode
        except Exception as e:
            TASKS[task_id]["status"] = "error"
            TASKS[task_id]["output"] += f"\n[ERROR] {e}"

    if task_id:
        TASKS[task_id] = {"status": "running", "output": "", "pid": None}
        Thread(target=target, daemon=True).start()
        return task_id
    else:
        result = subprocess.run(
            [str(c) for c in cmd],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_env,
        )
        return result
    """运行脚本并实时返回输出（本地辅助函数）"""
    """运行脚本并实时返回输出"""
    def target():
        try:
            proc = subprocess.Popen(
                [str(c) for c in cmd],
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            TASKS[task_id]["pid"] = proc.pid
            output = []
            for line in proc.stdout:
                line = line.rstrip()
                output.append(line)
                TASKS[task_id]["output"] = "\n".join(output)
            proc.wait()
            TASKS[task_id]["status"] = "done" if proc.returncode == 0 else "error"
            TASKS[task_id]["returncode"] = proc.returncode
        except Exception as e:
            TASKS[task_id]["status"] = "error"
            TASKS[task_id]["output"] += f"\n[ERROR] {e}"

    if task_id:
        TASKS[task_id] = {"status": "running", "output": "", "pid": None}
        Thread(target=target, daemon=True).start()
        return task_id
    else:
        result = subprocess.run(
            [str(c) for c in cmd],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result


def log_history(action, params, result=None):
    """记录操作历史（带容错，写失败不抛异常）"""
    try:
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        history.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "params": params,
            "result": result,
        })
        # 只保留最近 200 条
        history = history[-200:]
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        # 写历史失败不阻断主流程（只读目录/磁盘满/权限问题等）
        pass
    """记录操作历史"""
    history = []
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    history.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "params": params,
        "result": result,
    })
    # 只保留最近 200 条
    history = history[-200:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------------- 系统状态 ----------------------

@app.route("/api/system/status")
def system_status():
    """获取系统状态"""
    cfg = CONFIG
    status = {
        "workflow_exists": Path(cfg["workflow_root"]).exists(),
        "openmontage_exists": Path(cfg["openmontage_root"]).exists(),
        "ffmpeg_available": False,
        "gpu_available": False,
        "api_keys": {
            k: bool(v) for k, v in cfg["api_keys"].items()
        },
        "shotcraft_enabled": cfg.get("shotcraft", {}).get("enabled", False),
    }
    # 检查 FFmpeg
    try:
        result = subprocess.run(
            [cfg["paths"]["ffmpeg"], "-version"],
            capture_output=True,
        )
        status["ffmpeg_available"] = result.returncode == 0
    except Exception:
        status["ffmpeg_available"] = False

    # 检查 GPU
    try:
        subprocess.run(
            ["nvidia-smi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True
        )
        status["gpu_available"] = True
    except Exception:
        pass
    return jsonify(status)


@app.route("/api/system/config", methods=["GET", "POST"])
def system_config():
    global CONFIG
    if request.method == "GET":
        # 返回配置（隐藏敏感key的部分内容）
        safe_config = json.loads(json.dumps(CONFIG))
        for k in safe_config.get("api_keys", {}):
            v = safe_config["api_keys"][k]
            if v:
                safe_config["api_keys"][k] = v[:4] + "****" + v[-4:] if len(v) > 8 else "****"
        return jsonify(safe_config)

    elif request.method == "POST":
        data = request.get_json() or {}
        # 只更新提供的字段
        for key in ["workflow_root", "openmontage_root", "vibefilming_root",
                    "skills_root", "output_dir", "daily_budget"]:
            if key in data:
                CONFIG[key] = data[key]
        if "api_keys" in data:
            for k, v in data["api_keys"].items():
                if v and "****" not in v:
                    CONFIG["api_keys"][k] = v
        if "paths" in data:
            CONFIG["paths"].update(data["paths"])
        if "shotcraft" in data:
            CONFIG["shotcraft"].update(data["shotcraft"])
        save_config(CONFIG)
        return jsonify({"success": True, "message": "配置已保存"})


@app.route("/api/system/history")
def system_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
        return jsonify(history[-50:][::-1])
    return jsonify([])


# ---------------------- 智能导演 ----------------------

@app.route("/api/director/plan", methods=["POST"])
def director_plan():
    """获取导演方案（dry-run）"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    style = data.get("style", "auto")
    budget = data.get("budget", 10)
    dynamic = data.get("dynamic", False)
    duration = data.get("duration")
    reference_url = data.get("reference_url", "").strip()
    topic_id = data.get("topic_id", "").strip()

    if not topic and not reference_url and not topic_id:
        return jsonify({"error": "请提供主题、参考链接或选题ID"}), 400

    script = get_script_path("auto_video_director.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "--style", style, "--budget", str(budget)]
    if topic:
        cmd += ["--topic", topic]
    if reference_url:
        cmd += ["--reference-url", reference_url]
    if topic_id:
        cmd += ["--topic-id", topic_id]
    if dynamic:
        cmd.append("--dynamic")
    if duration:
        cmd += ["--duration", str(duration)]
    cmd.append("--dry-run")

    result = _run_subprocess(cmd)
    log_history("director_plan", data, {"stdout": result.stdout, "stderr": result.stderr})
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    })


@app.route("/api/director/run", methods=["POST"])
def director_run():
    """执行导演方案"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    style = data.get("style", "auto")
    budget = data.get("budget", 10)
    dynamic = data.get("dynamic", False)
    duration = data.get("duration")
    reference_url = data.get("reference_url", "").strip()
    topic_id = data.get("topic_id", "").strip()

    if not topic and not reference_url and not topic_id:
        return jsonify({"error": "请提供主题、参考链接或选题ID"}), 400

    script = get_script_path("auto_video_director.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    task_id = f"director_{int(time.time() * 1000)}"
    cmd = [CONFIG["paths"]["python"], str(script), "--style", style, "--budget", str(budget)]
    if topic:
        cmd += ["--topic", topic]
    if reference_url:
        cmd += ["--reference-url", reference_url]
    if topic_id:
        cmd += ["--topic-id", topic_id]
    if dynamic:
        cmd.append("--dynamic")
    if duration:
        cmd += ["--duration", str(duration)]

    _run_subprocess(cmd, task_id=task_id)
    log_history("director_run", data)
    return jsonify({"task_id": task_id, "status": "running"})


# ---------------------- OpenMontage ----------------------

@app.route("/api/openmontage/run", methods=["POST"])
def openmontage_run():
    """运行 OpenMontage"""
    data = request.get_json() or {}
    pipeline = data.get("pipeline", "factory")
    topic = data.get("topic", "").strip()
    url = data.get("url", "").strip()
    topic_id = data.get("topic_id", "").strip()
    use_wan = data.get("use_wan", False)

    script = get_script_path("run_openmontage.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    om_python = get_om_venv_python()
    if not om_python.exists():
        return jsonify({"error": f"找不到 OpenMontage Python: {om_python}"}), 500

    task_id = f"om_{pipeline}_{int(time.time() * 1000)}"
    cmd = [str(om_python), str(script), pipeline]

    if pipeline == "factory" and topic:
        cmd += ["--topic", topic]
    elif pipeline == "replicate" and url:
        cmd += ["--url", url]
    elif pipeline == "yaosheng" and topic_id:
        cmd += ["--topic-id", topic_id]
        if use_wan:
            cmd.append("--wan")
    elif pipeline == "documentary" and topic:
        cmd += ["--topic", topic]
    elif pipeline == "preflight":
        pass
    else:
        return jsonify({"error": "参数不匹配"}), 400

    _run_subprocess(cmd, task_id=task_id)
    log_history("openmontage_run", data)
    return jsonify({"task_id": task_id, "status": "running"})


# ---------------------- 爆款复刻 ----------------------

@app.route("/api/replicate/analyze", methods=["POST"])
def replicate_analyze():
    """分析爆款视频（dry-run）"""
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "请提供视频链接"}), 400

    script = get_script_path("replicate_viral.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "--url", url, "--dry-run"]
    result = _run_subprocess(cmd)
    log_history("replicate_analyze", data, {"stdout": result.stdout})
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    })


@app.route("/api/replicate/run", methods=["POST"])
def replicate_run():
    """执行爆款复刻"""
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    shot_duration = data.get("shot_duration", 4)
    search_name = data.get("search_name", "").strip()

    if not url:
        return jsonify({"error": "请提供视频链接"}), 400

    script = get_script_path("replicate_viral.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    task_id = f"replicate_{int(time.time() * 1000)}"
    cmd = [CONFIG["paths"]["python"], str(script), "--url", url, "--confirm"]
    cmd += ["--shot-duration", str(shot_duration)]
    if search_name:
        cmd += ["--search-name", search_name]

    _run_subprocess(cmd, task_id=task_id)
    log_history("replicate_run", data)
    return jsonify({"task_id": task_id, "status": "running"})


# ---------------------- 每日选题 ----------------------

@app.route("/api/topics/daily")
def topics_daily():
    """获取每日选题"""
    count = request.args.get("count", 3, type=int)
    script = get_script_path("daily_topic_selector.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "--count", str(count)]
    result = _run_subprocess(cmd)
    log_history("topics_daily", {"count": count}, {"stdout": result.stdout})
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    })


# ---------------------- 成本追踪 ----------------------

@app.route("/api/cost/summary")
def cost_summary():
    days = request.args.get("days", type=int)
    script = get_script_path("cost_tracker.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "--summary"]
    if days:
        cmd += ["--days", str(days)]
    result = _run_subprocess(cmd)
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
    })


@app.route("/api/cost/add", methods=["POST"])
def cost_add():
    data = request.get_json() or {}
    script = get_script_path("cost_tracker.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [
        CONFIG["paths"]["python"], str(script),
        "--add",
        "--topic-id", data.get("topic_id", ""),
        "--title", data.get("title", ""),
        "--mode", data.get("mode", "seedance"),
        "--cost", str(data.get("cost", 0)),
    ]
    result = _run_subprocess(cmd)
    log_history("cost_add", data, {"stdout": result.stdout})
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
    })


# ---------------------- Skill Hub ----------------------

@app.route("/api/skill/parse", methods=["POST"])
def skill_parse():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    download = data.get("download", False)
    if not url:
        return jsonify({"error": "请提供视频链接"}), 400

    script = get_script_path("skill_hub.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "parse", "--url", url]
    if download:
        cmd.append("--download")
    result = _run_subprocess(cmd)
    return jsonify({"stdout": result.stdout, "stderr": result.stderr})


@app.route("/api/skill/transcribe", methods=["POST"])
def skill_transcribe():
    data = request.get_json() or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "请提供视频链接"}), 400

    script = get_script_path("skill_hub.py")
    if not script.exists():
        return jsonify({"error": f"找不到脚本: {script}"}), 500

    cmd = [CONFIG["paths"]["python"], str(script), "transcribe", "--url", url]
    result = _run_subprocess(cmd)
    return jsonify({"stdout": result.stdout, "stderr": result.stderr})


# ========================================================================
# Video ShotCraft 整合模块
# ========================================================================

# 内置镜头卡库数据（从 GitHub API 获取的简化版本）
# 实际运行时可以通过 GitHub API 动态获取，这里缓存核心数据

BUILTIN_SHOTCRAFT_LIBRARY = {
    "generatedAt": "2026-07-27T05:24:52.000Z",
    "revision": "bdd94be16d60fa8f",
    "stats": {"cardCount": 104, "styleCount": 161, "previewCount": 161},
    "categories": [
        {"key": "opening", "name": "开场", "icon": "🎬", "desc": "品牌开场、定场镜头、主视觉揭幕"},
        {"key": "camera", "name": "运镜", "icon": "📷", "desc": "3D空间运镜、俯拍、推进、环绕"},
        {"key": "ui-entrance", "name": "UI入场", "icon": "🎯", "desc": "卡片飞入、列表堆叠、页面登场"},
        {"key": "transition", "name": "转场", "icon": "🔄", "desc": "镜头交棒、穿越、隐藏切点"},
        {"key": "typography", "name": "文字", "icon": "🔤", "desc": "标题动效、打字机、翻牌、字标"},
        {"key": "effects", "name": "特效", "icon": "✨", "desc": "光效、粒子、冲击、霓虹"},
        {"key": "interaction", "name": "交互", "icon": "👆", "desc": "光标表演、命令面板、切换"},
        {"key": "data", "name": "数据", "icon": "📊", "desc": "图表、计数器、时间轴、仪表盘"},
        {"key": "rhythm", "name": "节奏", "icon": "🥁", "desc": "卡点、变速、频闪、节拍器"},
        {"key": "outro", "name": "收尾", "icon": "🏁", "desc": "片尾、品牌合影、钩子"},
    ],
    "cards": [
        {"name": "brand-ink-open", "summary": "墨线十字准星描画→字标逐字压印→打字机副标→满一秒静止再上浮消散", "category": "opening", "energy": "低", "duration": "约2.8s", "tags": ["opening", "typography"]},
        {"name": "spotlight-hero-card", "summary": "聚光灯扫过页面锁定一张卡，斜45°推进后卡片弹起悬浮、光束沿轮廓两圈、贴回原位", "category": "opening", "energy": "中", "duration": "约4.6s", "tags": ["opening", "effects", "camera"]},
        {"name": "crane-rise-reveal", "summary": "升降臂拉升揭示——开场怼在一行数据特写，相机沿Y轴减速升起后拉，行行涌入直到整面dashboard铺满全幅", "category": "opening", "energy": "中高", "duration": "5s", "tags": ["opening", "camera", "data"]},
        {"name": "icon-field-colorize", "summary": "灰阶小图标点阵错峰浮现铺满全屏，停一拍后多道品牌色横带波纹极快向下扫翻全场", "category": "opening", "energy": "中", "duration": "3-4s", "tags": ["opening", "ui-entrance", "outro"]},
        {"name": "dataviz-landscape-open", "summary": "暗场支流线束地景开场——多条流线汇入主干、虚构ID标签浮在线上、相机重景深低速飞越", "category": "opening", "energy": "低开缓升", "duration": "5-8s", "tags": ["opening", "data", "camera"]},
        {"name": "deck-deal-flyin", "summary": "暗场金属背景里的实体牌堆特写环绕开局，拉远交给页面后一摞卡像发牌一样硬加速甩进网格", "category": "ui-entrance", "energy": "高", "duration": "约2.6s", "tags": ["ui-entrance"]},
        {"name": "row-embed", "summary": "内容行像卡片一样从空中降下、rotateX收平、嵌入瞬间底边亮一道强调色的缝", "category": "ui-entrance", "energy": "中", "duration": "约2s", "tags": ["ui-entrance"]},
        {"name": "list-stack-press", "summary": "列表卡从画面底部逐张飞上摞起，每张落地压弹整摞、计数器同步跳一格", "category": "ui-entrance", "energy": "中", "duration": "约3s", "tags": ["ui-entrance"]},
        {"name": "cloner-depth-echo", "summary": "克隆纵队——主卡瞬间「复印」出7个半透明分身沿斜向纵深排开成队，停一拍后全体加速吸回本体合一+弹跳", "category": "ui-entrance", "energy": "中", "duration": "4-5s", "tags": ["ui-entrance"]},
        {"name": "crash-zoom-punch", "summary": "全景一拍急推到目标特写（6f），落位二选一——过冲回弹（弹性）或撞停震屏（重量）", "category": "camera", "energy": "高", "duration": "约0.5s动作+hold", "tags": ["camera", "effects"]},
        {"name": "depth-layer-moves", "summary": "分层深度两款运镜——多层视差滑轨与伪dolly-zoom（主体钉死、背景膨胀压来）", "category": "camera", "energy": "中/中高", "duration": "4-5s", "tags": ["camera"]},
        {"name": "space-camera-moves", "summary": "3D空间化运镜——爆炸分解（构件沿Z炸开再合体）、无人机俯冲降落", "category": "camera", "energy": "高", "duration": "3-5s", "tags": ["camera"]},
        {"name": "tension-camera-moves", "summary": "情绪运镜四式——冻结环绕、斜角滚正、慢推压迫、拉远孤立", "category": "camera", "energy": "多变", "duration": "4-5s", "tags": ["camera"]},
        {"name": "shot-transitions", "summary": "镜头交棒六式——推进流白、穿暗场直航、虚焦接力、黑场字卡、甩镜、穿窗", "category": "transition", "energy": "技法卡", "duration": "n/a", "tags": ["transition"]},
        {"name": "transition-hidden-cut", "summary": "藏切点转场三式——前景遮挡隐形切、对撞开屏、暖色漏光", "category": "transition", "energy": "技法卡", "duration": "n/a", "tags": ["transition"]},
        {"name": "transition-travel", "summary": "穿越式转场——共享元素归位、字腔穿越，镜头钻进画面里的真实元素完成换景", "category": "transition", "energy": "技法卡", "duration": "25-60f", "tags": ["transition", "camera"]},
        {"name": "page-turn-transitions", "summary": "整页体块转场——立方体翻转、对开门裂幕", "category": "transition", "energy": "中高", "duration": "约4.4-4.7s", "tags": ["transition"]},
        {"name": "document-typewriter-reveal", "summary": "整页真排版文档在光标后自己「写」出来、侧栏跟进、历史条目逐个落入轨道", "category": "typography", "energy": "低中", "duration": "约3.7s", "tags": ["typography", "ui-entrance"]},
        {"name": "split-flap-title", "summary": "机场翻牌屏字标题——每字符上下两半机械翻牌格，翻过2个乱码咔哒停在目标字", "category": "typography", "energy": "中", "duration": "约4.7s", "tags": ["typography", "opening"]},
        {"name": "odometer-digit-roll", "summary": "里程表数字滚动大字报——全屏巨号指标每个数位像老虎机滚轮独立纵向滚动带残影", "category": "data", "energy": "中高", "duration": "约5s", "tags": ["data", "typography"]},
        {"name": "chart-live-moves", "summary": "活体图表三式——示波流线、点阵重组、轴爆表重标", "category": "data", "energy": "中高", "duration": "4-6s", "tags": ["data"]},
        {"name": "scroll-brake-moves", "summary": "长卷急刹——高速长卷指数减速精准停位+目标抬升，可选急刹帧同帧准星咬合", "category": "data", "energy": "高开中收", "duration": "4-5s", "tags": ["data", "rhythm"]},
        {"name": "glow-flyline-moves", "summary": "暗场光斑与飞线——光斑底噪、飞线连接、同帧共振组合", "category": "effects", "energy": "低/中/中高", "duration": "4-5.2s", "tags": ["effects", "data"]},
        {"name": "light-play-moves", "summary": "光效三式——聚光扫字、单点扫光、撞停晕染", "category": "effects", "energy": "中/低/高", "duration": "4.7-5.3s", "tags": ["effects", "typography"]},
        {"name": "slam-entrance-moves", "summary": "高能砸入三式——金田透视急停、比分砸落、落点冲击套件", "category": "effects", "energy": "高", "duration": "动作6-22f+hold", "tags": ["effects", "ui-entrance"]},
        {"name": "input-trigger-moves", "summary": "输入触发——光标表演点击推近、键帽引信引爆猛切", "category": "interaction", "energy": "中/高", "duration": "约5s", "tags": ["interaction", "opening"]},
        {"name": "command-palette-summon", "summary": "命令面板降临——整屏压暗加模糊，⌘K面板带过冲弹落，候选行错峰浮现，敲字列表实时收窄", "category": "interaction", "energy": "中", "duration": "4-5s", "tags": ["interaction", "ui-entrance"]},
        {"name": "ai-stream-response", "summary": "AI响应面板先落一句可读摘要，再让带状态图标的证据行逐条汇入，最后统一收束成完成态", "category": "interaction", "energy": "中高", "duration": "约4-5s", "tags": ["interaction"]},
        {"name": "beat-cut-moves", "summary": "硬切当节拍乐器——递进硬切串（间隔减半加速逼近）与连闪定格（三次白闪各切一个裁切）", "category": "rhythm", "energy": "高", "duration": "约4.3s", "tags": ["rhythm", "transition"]},
        {"name": "montage-rhythm-moves", "summary": "蒙太奇节奏——黑场蓄爆、三连咔哒特写、多米诺连锁入场", "category": "rhythm", "energy": "高", "duration": "4.3-5s", "tags": ["rhythm"]},
        {"name": "trailer-grammar-moves", "summary": "预告片语法——前置速剪钩子、字卡穿插对话、猛切入定", "category": "rhythm", "energy": "高/中/高", "duration": "4.5-5s", "tags": ["rhythm", "opening", "transition"]},
        {"name": "outro-group-photo-launch", "summary": "全片元素从四面八方飞来围住字标合影，crane落机位+舞台光+金尘做成发布会收场", "category": "outro", "energy": "峰值", "duration": "约4.8s", "tags": ["outro"]},
        {"name": "paper-title-card", "summary": "一句话逐词压印上纸、一个词标强调色斜体、短划线收束", "category": "typography", "energy": "低", "duration": "1.7-1.8s", "tags": ["typography", "transition", "rhythm"]},
    ]
}


def _get_shotcraft_library():
    """获取镜头卡库（优先从GitHub API获取，失败则使用内置数据）"""
    global SHOTCRAFT_LIBRARY, SHOTCRAFT_LIBRARY_LOADED_AT
    
    # 缓存1小时
    if SHOTCRAFT_LIBRARY is not None and (time.time() - SHOTCRAFT_LIBRARY_LOADED_AT) < 3600:
        return SHOTCRAFT_LIBRARY
    
    # 尝试从本地缓存文件加载
    cache_file = BASE_DIR / "video-shotcraft" / "api" / "library.json"
    if not cache_file.exists():
        cache_file = BASE_DIR / "skills" / "video-shotcraft" / "gallery" / "api" / "library.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "cards" in data:
                    SHOTCRAFT_LIBRARY = data
                    SHOTCRAFT_LIBRARY_LOADED_AT = time.time()
                    return SHOTCRAFT_LIBRARY
        except Exception:
            pass
    
    # 使用内置数据
    SHOTCRAFT_LIBRARY = BUILTIN_SHOTCRAFT_LIBRARY
    SHOTCRAFT_LIBRARY_LOADED_AT = time.time()
    return SHOTCRAFT_LIBRARY


@app.route("/api/shotcraft/library")
def shotcraft_library():
    """获取Video ShotCraft镜头卡库"""
    lib = _get_shotcraft_library()
    return jsonify({
        "stats": lib.get("stats", {}),
        "categories": lib.get("categories", []),
        "cards": lib.get("cards", []),
        "gallery_url": CONFIG.get("shotcraft", {}).get("gallery_url", "https://vincentwei1021.github.io/video-shotcraft/"),
    })


@app.route("/api/shotcraft/search")
def shotcraft_search():
    """搜索镜头卡"""
    query = request.args.get("q", "").lower().strip()
    category = request.args.get("category", "").strip()
    energy = request.args.get("energy", "").strip()
    
    lib = _get_shotcraft_library()
    cards = lib.get("cards", [])
    
    results = []
    for card in cards:
        # 分类过滤
        if category and card.get("category") != category:
            continue
        # 能量过滤
        if energy and energy.lower() not in card.get("energy", "").lower():
            continue
        # 文本搜索
        if query:
            searchable = " ".join([
                card.get("name", ""),
                card.get("summary", ""),
                " ".join(card.get("tags", [])),
                card.get("category", ""),
            ]).lower()
            if query not in searchable:
                continue
        results.append(card)
    
    return jsonify({
        "query": query,
        "category": category,
        "energy": energy,
        "count": len(results),
        "cards": results,
    })


@app.route("/api/shotcraft/categories")
def shotcraft_categories():
    """获取镜头卡分类列表"""
    lib = _get_shotcraft_library()
    return jsonify(lib.get("categories", []))


@app.route("/api/shotcraft/card/<name>")
def shotcraft_card_detail(name):
    """获取单张镜头卡详情（返回markdown内容链接）"""
    lib = _get_shotcraft_library()
    cards = lib.get("cards", [])
    
    for card in cards:
        if card.get("name") == name:
            # 构建GitHub原始文件URL
            owner = CONFIG.get("shotcraft", {}).get("github_owner", "Vincentwei1021")
            repo = CONFIG.get("shotcraft", {}).get("github_repo", "video-shotcraft")
            category = card.get("category", "")
            
            # 映射分类到目录
            category_map = {
                "opening": "opening",
                "camera": "camera", 
                "ui-entrance": "ui-entrance",
                "transition": "transition",
                "typography": "typography",
                "effects": "effects",
                "interaction": "interaction",
                "data": "data",
                "rhythm": "rhythm",
                "outro": "outro",
            }
            dir_name = category_map.get(category, category)
            
            github_url = f"https://github.com/{owner}/{repo}/blob/main/references/shots/{dir_name}/{name}.md"
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/references/shots/{dir_name}/{name}.md"
            
            return jsonify({
                "card": card,
                "github_url": github_url,
                "raw_url": raw_url,
                "gallery_url": f"https://vincentwei1021.github.io/video-shotcraft/library.html",
            })
    
    return jsonify({"error": f"找不到镜头卡: {name}"}), 404


@app.route("/api/shotcraft/generate-plan", methods=["POST"])
def shotcraft_generate_plan():
    """基于选中的镜头卡生成视频分镜方案"""
    data = request.get_json() or {}
    cards = data.get("cards", [])  # 选中的镜头卡名列表
    product_type = data.get("product_type", "web")  # web/desktop/mobile
    duration = data.get("duration", 30)  # 目标时长(秒)
    style = data.get("style", "auto")  # 视觉风格
    
    if not cards:
        return jsonify({"error": "请至少选择一张镜头卡"}), 400
    
    lib = _get_shotcraft_library()
    all_cards = {c["name"]: c for c in lib.get("cards", [])}
    
    # 构建分镜方案
    plan = {
        "product_type": product_type,
        "target_duration": duration,
        "style": style,
        "shots": [],
        "timeline": [],
        "notes": [],
    }
    
    current_time = 0
    for i, card_name in enumerate(cards):
        card = all_cards.get(card_name)
        if not card:
            continue
        
        # 估算时长（从duration字段解析）
        est_duration = 4  # 默认4秒
        dur_str = card.get("duration", "")
        if "s" in dur_str:
            try:
                est_duration = int(re.search(r'(\d+)', dur_str).group(1))
            except Exception:
                pass
        
        shot = {
            "order": i + 1,
            "name": card_name,
            "summary": card.get("summary", ""),
            "category": card.get("category", ""),
            "energy": card.get("energy", ""),
            "estimated_duration": est_duration,
            "start_time": current_time,
            "end_time": current_time + est_duration,
            "tags": card.get("tags", []),
        }
        plan["shots"].append(shot)
        plan["timeline"].append(f"[{current_time}s - {current_time + est_duration}s] {card_name}")
        current_time += est_duration
    
    plan["total_duration"] = current_time
    plan["notes"] = [
        f"方案包含 {len(plan['shots'])} 个镜头，预估总时长 {current_time} 秒",
        "每个镜头请参考对应的配方卡文档获取完整参数和实现细节",
        "建议在Remotion中实现，使用assets/lib/中的基础组件",
        "声音设计请参考references/sound-design.md",
    ]
    
    log_history("shotcraft_generate_plan", data, {"total_duration": current_time, "shots_count": len(plan["shots"])})
    return jsonify(plan)


# ---------------------- 任务管理 ----------------------

@app.route("/api/task/<task_id>")
def task_status(task_id):
    if task_id not in TASKS:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(TASKS[task_id])


@app.route("/api/task/<task_id>/kill", methods=["POST"])
def task_kill(task_id):
    if task_id not in TASKS:
        return jsonify({"error": "任务不存在"}), 404
    task = TASKS[task_id]
    if task.get("pid"):
        try:
            import signal
            os.kill(task["pid"], signal.SIGTERM)
            task["status"] = "killed"
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "任务没有PID"}), 400


@app.route("/api/tasks")
def task_list():
    return jsonify(TASKS)


# ---------------------- 生成成果 ----------------------

@app.route("/api/outputs")
def outputs_list():
    """获取生成成果列表"""
    output_dir = Path(CONFIG["output_dir"])
    if not output_dir.exists():
        return jsonify([])

    results = []
    for item in sorted(output_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if item.is_dir():
            meta = item / "meta.json"
            meta_data = {}
            if meta.exists():
                try:
                    with open(meta, "r", encoding="utf-8") as f:
                        meta_data = json.load(f)
                except Exception:
                    pass
            video = item / "final.mp4"
            if not video.exists():
                video = item / "video.mp4"
            cover = item / "cover.jpg"
            results.append({
                "name": item.name,
                "path": str(item),
                "mtime": item.stat().st_mtime,
                "has_video": video.exists(),
                "has_cover": cover.exists(),
                "meta": meta_data,
            })
    return jsonify(results)


# ===========================================================================
# 工作流深度对接 —— 视频自动化 VideoForge 集成
# ===========================================================================

# ---------------------- 脚本执行 ----------------------

@app.route("/api/workflow/scripts")
def workflow_scripts():
    """获取所有可用脚本"""
    return jsonify({
        "scripts": [
            {**v, "key": k} for k, v in SCRIPT_REGISTRY.items()
        ]
    })


@app.route("/api/workflow/run", methods=["POST"])
def workflow_run():
    """运行工作流脚本"""
    data = request.get_json() or {}
    script_key = data.get("script")
    params = data.get("params", {})
    if not script_key:
        return jsonify({"error": "缺少 script 参数"}), 400
    result = run_script(script_key, params, user="web")
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@app.route("/api/workflow/tasks")
def workflow_tasks():
    """获取工作流任务列表"""
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"tasks": list_tasks(limit)})


@app.route("/api/workflow/task/<task_id>")
def workflow_task_detail(task_id):
    """获取单个任务详情"""
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)


@app.route("/api/workflow/task/<task_id>/kill", methods=["POST"])
def workflow_task_kill(task_id):
    """终止任务"""
    result = kill_task(task_id)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


# ---------------------- 文件管理 ----------------------

@app.route("/api/files/browse")
def files_browse():
    """浏览目录"""
    path = request.args.get("path", str(WORKFLOW_ROOT))
    pattern = request.args.get("pattern", "*")
    # 安全检查：禁止访问工作流根目录之外
    p = Path(path).resolve()
    if not str(p).startswith(str(WORKFLOW_ROOT.resolve())):
        return jsonify({"error": "禁止访问工作流目录之外的文件"}), 403
    return jsonify({
        "path": str(p),
        "items": list_directory(str(p), pattern),
    })


@app.route("/api/outputs/list")
def outputs_list_v2():
    """获取生成成果列表"""
    return jsonify({"outputs": list_outputs()})


@app.route("/api/outputs/file/<path:filepath>")
def outputs_file(filepath):
    """获取生成成果中的文件"""
    safe_path = (OUTPUTS_DIR / filepath).resolve()
    if not str(safe_path).startswith(str(OUTPUTS_DIR.resolve())):
        return jsonify({"error": "非法路径"}), 403
    if not safe_path.exists():
        return jsonify({"error": "文件不存在"}), 404
    from flask import send_file
    return send_file(str(safe_path))


# ---------------------- 选题管理 ----------------------

@app.route("/api/topics/pool")
def topics_pool():
    """获取选题池"""
    return jsonify(load_topics_pool())


@app.route("/api/topics/list")
def topics_list_v2():
    """列出所有选题"""
    category = request.args.get("category")
    return jsonify({"topics": list_topics(category)})


@app.route("/api/topics/save", methods=["POST"])
def topics_save():
    """保存选题池"""
    data = request.get_json() or {}
    if save_topics_pool(data):
        return jsonify({"success": True})
    return jsonify({"error": "保存失败"}), 500


# ---------------------- 日志与成本 ----------------------

@app.route("/api/logs/daily")
def logs_daily():
    """每日选题日志"""
    return jsonify({"selections": load_daily_selections()})


@app.route("/api/logs/cost")
def logs_cost():
    """成本日志"""
    days = request.args.get("days", 7, type=int)
    return jsonify(get_cost_summary(days))


# ---------------------- 环境检查 ----------------------

@app.route("/api/workflow/env-check")
def workflow_env_check():
    """环境检查"""
    return jsonify(check_environment())




# ---------------------- 配音模块 API ----------------------

@app.route("/api/voice/engines")
def voice_engines():
    """获取所有 TTS 引擎状态"""
    return jsonify(get_engine_status())


@app.route("/api/voice/voices")
def voice_voices():
    """获取所有可用音色列表"""
    return jsonify(get_all_voices())


@app.route("/api/voice/synthesize", methods=["POST"])
def voice_synthesize():
    """语音合成主接口"""
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"success": False, "error": "文本不能为空"}), 400

    engine = data.get("engine", "auto")
    voice = data.get("voice")
    rate = data.get("rate", "+0%")
    speed = data.get("speed", 1.0)

    if engine == "gpt-sovits":
        refer_wav = data.get("refer_wav_path", "")
        prompt_text = data.get("prompt_text", "")
        prompt_lang = data.get("prompt_lang", "zh")
        text_lang = data.get("text_lang", "zh")
        result = synthesize(
            text, engine="gpt-sovits",
            refer_wav_path=refer_wav, prompt_text=prompt_text,
            prompt_lang=prompt_lang, text_lang=text_lang
        )
    else:
        result = synthesize(text, engine=engine, voice=voice, rate=rate, speed=speed)

    return jsonify(result)


@app.route("/api/voice/upload-reference", methods=["POST"])
def voice_upload_reference():
    """上传参考音频用于音色克隆"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未上传文件"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "文件名为空"}), 400
    description = request.form.get("description", "")
    result = save_reference_audio(file.stream, file.filename, description)
    return jsonify(result)


@app.route("/api/voice/references")
def voice_references():
    """列出所有参考音频"""
    return jsonify({"voices": list_reference_voices()})


@app.route("/api/voice/reference/<voice_id>/delete", methods=["POST"])
def voice_delete_reference(voice_id):
    """删除参考音频"""
    result = delete_reference_voice(voice_id)
    return jsonify(result)


@app.route("/api/voice/outputs")
def voice_outputs():
    """列出所有生成的音频文件"""
    try:
        files = []
        for f in sorted(VOICE_OUTPUT_DIR.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
                stat = f.stat()
                files.append({
                    "name": f.name,
                    "path": str(f),
                    "size": stat.st_size,
                    "created": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# 启动
# ---------------------------------------------------------------------------


# ===========================================================================
# 增强功能 —— 海纳百川模块
# ===========================================================================

# ---------------------- 选题矩阵 ----------------------

@app.route("/api/matrix/categories")
def matrix_categories():
    """获取选题矩阵分类"""
    return jsonify({"categories": get_matrix_categories()})


@app.route("/api/matrix/generate", methods=["POST"])
def matrix_generate():
    """生成选题矩阵"""
    data = request.get_json() or {}
    category = data.get("category", "emotional")
    count = data.get("count", 10)
    results = generate_topic_matrix(category, min(count, 30))
    return jsonify({"category": category, "topics": results})


# ---------------------- AI 脚本生成 ----------------------

@app.route("/api/script/templates")
def script_templates():
    """获取脚本模板列表"""
    return jsonify({
        "templates": [
            {**v, "key": k} for k, v in SCRIPT_TEMPLATES.items()
        ]
    })


@app.route("/api/script/outline", methods=["POST"])
def script_outline():
    """生成脚本大纲"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "请提供主题"}), 400
    result = generate_script_outline(
        topic=topic,
        template=data.get("template", "hook_scene_turn_punchline_cta"),
        duration=data.get("duration", 30),
        style=data.get("style", "口播"),
    )
    return jsonify(result)


@app.route("/api/script/generate", methods=["POST"])
def script_generate_ai():
    """使用 DeepSeek API 生成脚本"""
    data = request.get_json() or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "请提供主题"}), 400
    api_key = CONFIG.get("api_keys", {}).get("deepseek", "")
    if not api_key:
        return jsonify({"error": "未配置 DeepSeek API Key，请去设置页配置"}), 400
    result = generate_script_with_deepseek(
        topic=topic,
        style=data.get("style", "口播"),
        duration=data.get("duration", 30),
        api_key=api_key,
    )
    log_history("script_generate_ai", data, {"success": "script" in result})
    return jsonify(result)


# ---------------------- 素材库管理 ----------------------

@app.route("/api/assets/list")
def assets_list():
    """列出素材库"""
    asset_type = request.args.get("type")
    return jsonify({"assets": list_assets(asset_type)})


@app.route("/api/assets/stats")
def assets_stats():
    """素材库统计"""
    assets = list_assets()
    by_type = {}
    total_size = 0
    for a in assets:
        t = a["type"]
        by_type[t] = by_type.get(t, 0) + 1
        total_size += a.get("size", 0)
    return jsonify({
        "total": len(assets),
        "by_type": by_type,
        "total_size_human": _human_size(total_size) if assets else "0 B",
    })


def _human_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ---------------------- 视频去重检测 ----------------------

@app.route("/api/video/fingerprint", methods=["POST"])
def video_fingerprint():
    """获取视频指纹"""
    data = request.get_json() or {}
    path = data.get("path", "").strip()
    if not path:
        return jsonify({"error": "请提供视频路径"}), 400
    return jsonify(get_video_fingerprint(path))


@app.route("/api/video/duplicates")
def video_duplicates():
    """检测重复视频"""
    directory = request.args.get("directory", str(OUTPUTS_DIR))
    return jsonify({"duplicates": check_duplicate_videos(directory)})


# ---------------------- 定时任务队列 ----------------------

@app.route("/api/schedule/list")
def schedule_list():
    """获取定时任务列表"""
    return jsonify({"tasks": load_scheduled_tasks()})


@app.route("/api/schedule/add", methods=["POST"])
def schedule_add():
    """添加定时任务"""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    script_key = data.get("script_key", "").strip()
    schedule = data.get("schedule", "").strip()
    if not name or not script_key or not schedule:
        return jsonify({"error": "缺少必要参数"}), 400
    task = add_scheduled_task(
        name=name,
        script_key=script_key,
        params=data.get("params", {}),
        schedule=schedule,
        enabled=data.get("enabled", True),
    )
    log_history("schedule_add", data, {"task_id": task["id"]})
    return jsonify({"success": True, "task": task})


@app.route("/api/schedule/delete/<task_id>", methods=["POST"])
def schedule_delete(task_id):
    """删除定时任务"""
    if delete_scheduled_task(task_id):
        return jsonify({"success": True})
    return jsonify({"error": "任务不存在"}), 404


# ---------------------- 数据看板 ----------------------

@app.route("/api/dashboard/stats")
def dashboard_stats():
    """获取综合数据看板"""
    return jsonify(get_dashboard_stats())


# ---------------------- 混剪配置 ----------------------

@app.route("/api/mix/configs")
def mix_configs():
    """获取混剪配置模板"""
    return jsonify({"configs": get_mix_configs()})


# ---------------------- 发布统计 ----------------------

@app.route("/api/publish/stats")
def publish_stats():
    """获取发布统计"""
    return jsonify(get_publish_stats())





if __name__ == "__main__":
    # 不再自动保存默认配置到 config.json，路径始终从 DEFAULT_CONFIG + BASE_DIR 动态计算
    # 确保项目克隆到其他机器/目录后路径仍然正确
    print(f"🎬 视频自动化 Web 控制台启动中...")
    print(f"   访问地址: http://localhost:5000")
    print(f"   工作目录: {CONFIG.get('workflow_root')}")
    print(f"   配置文件: {CONFIG_FILE} (用户自定义配置会保存于此)")
    print(f"   Video ShotCraft: 已整合 {BUILTIN_SHOTCRAFT_LIBRARY['stats']['cardCount']} 张镜头配方卡")
    app.run(host="0.0.0.0", port=5000, debug=True)
