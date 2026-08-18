#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查脚本（占位/演示版本）

功能：
  - 检查 Python 版本（要求 >=3.9）
  - 检查 Flask / SQLAlchemy 是否安装
  - 检查 workspace 目录结构是否完整
  - 检查 FFmpeg 是否可用

说明：
  这是一个占位脚本，环境检查功能已实际可用，无需外部工具。
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本是否 >= 3.9"""
    major, minor = sys.version_info[:2]
    ok = (major, minor) >= (3, 9)
    print(f"  Python 版本: {sys.version.split()[0]}  {'✅' if ok else '❌ (需要 >= 3.9)'}")
    return ok


def check_flask():
    """检查 Flask 和 Flask-SQLAlchemy 是否安装"""
    results = []
    for pkg in ["flask", "flask_sqlalchemy"]:
        try:
            __import__(pkg)
            print(f"  {pkg:20s}  ✅ 已安装")
            results.append(True)
        except ImportError:
            print(f"  {pkg:20s}  ❌ 未安装 (pip install {pkg.replace('_', '-')})")
            results.append(False)
    return all(results)


def check_workspace():
    """检查 workspace 目录结构"""
    base = Path(__file__).resolve().parent.parent
    required = [
        base / "01-生成成果",
        base / "02-选题策划",
        base / "04-脚本工具",
        base / "06-运营日志",
        base / "07-文档与配置",
    ]
    ok = True
    for d in required:
        exists = d.exists()
        status = "✅" if exists else "❌"
        print(f"  {d.name:20s}  {status}")
        if not exists:
            ok = False
    return ok


def check_ffmpeg():
    """检查 FFmpeg 是否可用"""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        print(f"  FFmpeg               ✅  {ffmpeg}")
        return True

    # 尝试常见路径
    for candidate in [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
    ]:
        if Path(candidate).exists():
            print(f"  FFmpeg               ✅  {candidate}")
            return True

    print("  FFmpeg               ❌  未找到 (视频处理需要)")
    return False


def check_gpu():
    """检查是否有 NVIDIA GPU"""
    try:
        subprocess.run(
            ["nvidia-smi"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        print("  NVIDIA GPU           ✅  可用")
        return True
    except Exception:
        print("  NVIDIA GPU           ⚠️  未检测到 (部分功能需要)")
        return False  # GPU 不是强依赖


def main():
    parser = argparse.ArgumentParser(
        description="检查视频自动化项目运行环境"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="输出更详细的信息",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🔧  环境检查（占位/演示版本）")
    print("=" * 60)
    print()

    checks = [
        ("Python 环境", check_python_version()),
        ("Python 依赖", check_flask()),
        ("Workspace 目录", check_workspace()),
        ("FFmpeg", check_ffmpeg()),
        ("GPU 加速", check_gpu()),
    ]

    print()
    print("-" * 60)
    healthy = all(ok for _, ok in checks[:4])  # GPU 不算强依赖
    if healthy:
        print("✅ 环境检查通过，项目可以正常运行")
    else:
        print("⚠️  环境存在缺失项，部分功能可能不可用")
    print("-" * 60)

    if args.verbose:
        print()
        print("💡 提示：这是一个占位脚本，环境检查功能已实际可用。")
        print("   如需完整视频生成功能，请配置 OpenMontage 等外部工具。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
