#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VideoForge 配音模块 —— 三层 TTS 架构
L1: Edge-TTS (在线, 零门槛)
L2: Kokoro-FastAPI (本地, OpenAI兼容API)
L3: GPT-SoVITS (音色克隆, 高级功能)
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
VOICE_DIR = BASE_DIR / "workspace" / "voice_clones"
VOICE_OUTPUT_DIR = BASE_DIR / "workspace" / "voice_outputs"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
VOICE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 各引擎默认端口
KOKORO_API_URL = os.environ.get("KOKORO_API_URL", "http://localhost:8880")
GPT_SOVITS_API_URL = os.environ.get("GPT_SOVITS_API_URL", "http://localhost:9880")

# Edge-TTS 中文音色映射
EDGE_TTS_VOICES = {
    "zh-CN-XiaoxiaoNeural": {"name": "晓晓", "lang": "zh-CN", "gender": "Female", "style": "温暖自然"},
    "zh-CN-YunxiNeural": {"name": "云希", "lang": "zh-CN", "gender": "Male", "style": "年轻活力"},
    "zh-CN-YunjianNeural": {"name": "云健", "lang": "zh-CN", "gender": "Male", "style": "新闻播报"},
    "zh-CN-XiaoyiNeural": {"name": "晓伊", "lang": "zh-CN", "gender": "Female", "style": "温柔甜美"},
    "zh-CN-YunyangNeural": {"name": "云扬", "lang": "zh-CN", "gender": "Male", "style": "专业稳重"},
    "zh-CN-XiaochenNeural": {"name": "晓晨", "lang": "zh-CN", "gender": "Female", "style": "知性优雅"},
    "zh-HK-HiuMaanNeural": {"name": "晓曼(粤语)", "lang": "zh-HK", "gender": "Female", "style": "粤语女声"},
    "zh-TW-HsiaoChenNeural": {"name": "晓臻(台语)", "lang": "zh-TW", "gender": "Female", "style": "台湾女声"},
    "en-US-AriaNeural": {"name": "Aria(英文)", "lang": "en-US", "gender": "Female", "style": "英文女声"},
    "en-US-GuyNeural": {"name": "Guy(英文)", "lang": "en-US", "gender": "Male", "style": "英文男声"},
    "ja-JP-NanamiNeural": {"name": "七海(日文)", "lang": "ja-JP", "gender": "Female", "style": "日文女声"},
}

# Kokoro 常用音色（实际以 /v1/audio/voices 返回为准）
KOKORO_VOICES = {
    "zf_xiaobei": {"name": "小北(中文)", "lang": "zh", "gender": "Female"},
    "af_bella": {"name": "Bella(英文女)", "lang": "en", "gender": "Female"},
    "am_michael": {"name": "Michael(英文男)", "lang": "en", "gender": "Male"},
    "bf_emma": {"name": "Emma(英音女)", "lang": "en-gb", "gender": "Female"},
}

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _generate_id():
    return uuid.uuid4().hex[:12]


def _safe_filename(text, max_len=30):
    """生成安全的文件名"""
    cleaned = "".join(c for c in text if c.isalnum() or c in "_- ")
    return cleaned[:max_len].strip().replace(" ", "_") or "voice"


# ---------------------------------------------------------------------------
# L1: Edge-TTS
# ---------------------------------------------------------------------------

def edge_tts_available():
    """检测 edge-tts 是否可用"""
    try:
        import importlib.util
        return importlib.util.find_spec("edge_tts") is not None
    except Exception:
        return False


def edge_tts_synthesize(text, voice="zh-CN-XiaoxiaoNeural", rate="+0%", output_path=None):
    """
    使用 Edge-TTS 合成语音 (subprocess CLI 方式，Windows 更稳定)
    Args:
        text: 要合成的文本
        voice: 音色ID
        rate: 语速调整, e.g. "+10%" / "-10%"
        output_path: 输出文件路径, 默认自动生成
    Returns:
        dict: {success, output_path, duration_estimate, engine}
    """
    try:
        import subprocess
        import sys

        if output_path is None:
            fname = f"edge_{_safe_filename(text)}_{_generate_id()}.mp3"
            output_path = VOICE_OUTPUT_DIR / fname
        else:
            output_path = Path(output_path)

        cmd = [
            sys.executable, "-m", "edge_tts",
            "-t", text,
            "-v", voice,
            "--rate", rate,
            "--write-media", str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            err = result.stderr or "未知错误"
            return {"success": False, "error": f"Edge-TTS 错误: {err}", "engine": "edge-tts"}

        if not output_path.exists() or output_path.stat().st_size == 0:
            return {"success": False, "error": "Edge-TTS 未生成音频文件", "engine": "edge-tts"}

        # 估算时长 (粗略: 中文约 4 字/秒)
        char_count = len(text)
        duration = max(1, char_count / 4.5)

        return {
            "success": True,
            "output_path": str(output_path),
            "filename": output_path.name,
            "duration_estimate": round(duration, 1),
            "engine": "edge-tts",
            "voice": voice,
            "voice_name": EDGE_TTS_VOICES.get(voice, {}).get("name", voice),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "engine": "edge-tts"}


# ---------------------------------------------------------------------------
# L2: Kokoro (HTTP API)
# ---------------------------------------------------------------------------

def kokoro_available():
    """检测 Kokoro-FastAPI 服务是否在线"""
    try:
        resp = requests.get(f"{KOKORO_API_URL}/v1/audio/voices", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def kokoro_synthesize(text, voice="zf_xiaobei", speed=1.0, output_path=None, response_format="mp3"):
    """
    通过 Kokoro-FastAPI 合成语音
    """
    try:
        if output_path is None:
            fname = f"kokoro_{_safe_filename(text)}_{_generate_id()}.{response_format}"
            output_path = VOICE_OUTPUT_DIR / fname
        else:
            output_path = Path(output_path)

        resp = requests.post(
            f"{KOKORO_API_URL}/v1/audio/speech",
            json={
                "model": "kokoro",
                "input": text,
                "voice": voice,
                "speed": speed,
                "response_format": response_format,
            },
            timeout=60,
        )
        resp.raise_for_status()

        output_path.write_bytes(resp.content)

        # 估算时长
        char_count = len(text)
        duration = max(1, char_count / 4.5 / speed)

        return {
            "success": True,
            "output_path": str(output_path),
            "filename": output_path.name,
            "duration_estimate": round(duration, 1),
            "engine": "kokoro",
            "voice": voice,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "engine": "kokoro"}


def kokoro_list_voices():
    """获取 Kokoro 可用音色列表"""
    try:
        resp = requests.get(f"{KOKORO_API_URL}/v1/audio/voices", timeout=5)
        data = resp.json()
        return data.get("voices", [])
    except Exception:
        return []


# ---------------------------------------------------------------------------
# L3: GPT-SoVITS (音色克隆)
# ---------------------------------------------------------------------------

def gpt_sovits_available():
    """检测 GPT-SoVITS API 服务是否在线"""
    try:
        resp = requests.get(f"{GPT_SOVITS_API_URL}/", timeout=2)
        return resp.status_code in (200, 404)  # 404 也可能表示服务在但路径不对
    except Exception:
        return False


def gpt_sovits_synthesize(text, refer_wav_path, prompt_text="", prompt_lang="zh", text_lang="zh", output_path=None):
    """
    通过 GPT-SoVITS 进行音色克隆合成
    Args:
        text: 要合成的文本
        refer_wav_path: 参考音频路径（克隆目标音色）
        prompt_text: 参考音频对应的文本（可选，提升效果）
        prompt_lang: 参考音频语言
        text_lang: 合成文本语言
    """
    try:
        if output_path is None:
            fname = f"sovits_{_safe_filename(text)}_{_generate_id()}.wav"
            output_path = VOICE_OUTPUT_DIR / fname
        else:
            output_path = Path(output_path)

        # GPT-SoVITS 标准推理 API
        resp = requests.post(
            f"{GPT_SOVITS_API_URL}/",
            json={
                "refer_wav_path": str(refer_wav_path),
                "prompt_text": prompt_text,
                "prompt_lang": prompt_lang,
                "text": text,
                "text_lang": text_lang,
            },
            timeout=120,
        )
        resp.raise_for_status()

        output_path.write_bytes(resp.content)

        char_count = len(text)
        duration = max(1, char_count / 4.5)

        return {
            "success": True,
            "output_path": str(output_path),
            "filename": output_path.name,
            "duration_estimate": round(duration, 1),
            "engine": "gpt-sovits",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "engine": "gpt-sovits"}


# ---------------------------------------------------------------------------
# 参考音频管理
# ---------------------------------------------------------------------------

def save_reference_audio(uploaded_file_stream, filename, description=""):
    """
    保存用户上传的参考音频（用于音色克隆）
    Returns:
        dict: {success, voice_id, filepath, description}
    """
    try:
        voice_id = _generate_id()
        ext = Path(filename).suffix.lower()
        if ext not in (".wav", ".mp3", ".m4a", ".flac", ".ogg"):
            ext = ".wav"

        save_path = VOICE_DIR / f"{voice_id}{ext}"
        with open(save_path, "wb") as f:
            shutil.copyfileobj(uploaded_file_stream, f)

        # 保存元数据
        meta = {
            "voice_id": voice_id,
            "filename": filename,
            "filepath": str(save_path),
            "description": description,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        meta_path = VOICE_DIR / f"{voice_id}.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return {"success": True, **meta}
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_reference_voices():
    """列出所有已上传的参考音频"""
    voices = []
    try:
        for meta_file in sorted(VOICE_DIR.glob("*.json")):
            with open(meta_file, "r", encoding="utf-8") as f:
                voices.append(json.load(f))
    except Exception:
        pass
    return voices


def delete_reference_voice(voice_id):
    """删除参考音频"""
    try:
        for f in VOICE_DIR.glob(f"{voice_id}*"):
            f.unlink()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# 统一合成接口
# ---------------------------------------------------------------------------

def synthesize(text, engine="auto", voice=None, **kwargs):
    """
    统一语音合成入口
    engine: auto | edge-tts | kokoro | gpt-sovits
    auto 策略: kokoro(在线) > edge-tts(在线) > 报错
    """
    if engine == "auto":
        if kokoro_available():
            engine = "kokoro"
        elif edge_tts_available():
            engine = "edge-tts"
        else:
            return {"success": False, "error": "没有可用的 TTS 引擎。请先安装 edge-tts (pip install edge-tts) 或启动 Kokoro-FastAPI (docker run ...)"}

    if engine == "edge-tts":
        # Edge-TTS 只支持 rate，不支持 speed
        edge_kwargs = {k: v for k, v in kwargs.items() if k != "speed"}
        return edge_tts_synthesize(text, voice=voice or "zh-CN-XiaoxiaoNeural", **edge_kwargs)
    elif engine == "kokoro":
        # Kokoro 只支持 speed，不支持 rate
        kokoro_kwargs = {k: v for k, v in kwargs.items() if k != "rate"}
        return kokoro_synthesize(text, voice=voice or "zf_xiaobei", **kokoro_kwargs)
    elif engine == "gpt-sovits":
        return gpt_sovits_synthesize(text, **kwargs)
    else:
        return {"success": False, "error": f"不支持的引擎: {engine}"}


# ---------------------------------------------------------------------------
# 引擎状态总览
# ---------------------------------------------------------------------------

def get_engine_status():
    """获取所有引擎状态"""
    return {
        "edge-tts": {
            "available": edge_tts_available(),
            "type": "在线",
            "features": ["多音色", "多语言", "语速调节"],
            "cost": "免费（微软服务，商用需谨慎）",
        },
        "kokoro": {
            "available": kokoro_available(),
            "type": "本地/Docker",
            "features": ["多音色", "音色混合", "逐词时间戳", "SSML"],
            "cost": "免费（Apache 2.0，商用安全）",
            "api_url": KOKORO_API_URL,
        },
        "gpt-sovits": {
            "available": gpt_sovits_available(),
            "type": "本地（需GPU）",
            "features": ["音色克隆", "5秒样本", "情感丰富"],
            "cost": "免费（MIT，商用安全）",
            "api_url": GPT_SOVITS_API_URL,
        },
    }


def get_all_voices():
    """获取所有可用音色"""
    result = {
        "edge-tts": [
            {"id": k, **v, "engine": "edge-tts"}
            for k, v in EDGE_TTS_VOICES.items()
        ],
        "kokoro": [],
        "gpt-sovits": [],
    }

    # Kokoro 动态获取
    if kokoro_available():
        try:
            voices = kokoro_list_voices()
            result["kokoro"] = [{"id": v.get("id", v.get("voice_id", "")), "name": v.get("name", ""), "engine": "kokoro"} for v in voices]
        except Exception:
            result["kokoro"] = [{"id": k, **v, "engine": "kokoro"} for k, v in KOKORO_VOICES.items()]
    else:
        result["kokoro"] = [{"id": k, **v, "engine": "kokoro"} for k, v in KOKORO_VOICES.items()]

    # GPT-SoVITS 的参考音色
    result["gpt-sovits"] = [{"id": v["voice_id"], "name": v.get("description") or v["filename"], "engine": "gpt-sovits", **v} for v in list_reference_voices()]

    return result
