#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误扫描脚本（占位/演示版本）

功能：
  - 扫描工作流目录中常见的配置错误和缺失文件
  - 打印诊断报告

说明：
  这是一个占位脚本，诊断功能已部分可用，无需外部工具。
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="扫描工作流中常见的配置错误和缺失文件"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="尝试自动修复发现的问题",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🔍  错误扫描（占位/演示版本）")
    print("=" * 60)
    print()

    base = Path(__file__).resolve().parent.parent
    issues = []
    warnings = []

    # 检查目录结构
    required_dirs = [
        "01-生成成果",
        "02-选题策划",
        "04-脚本工具",
        "06-运营日志",
        "07-文档与配置",
    ]
    for dname in required_dirs:
        d = base / dname
        if not d.exists():
            issues.append(f"缺失目录: {dname}")
            if args.fix:
                d.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ 已创建目录: {dname}")

    # 检查配置文件
    config_dir = base / "config"
    topics_pool = config_dir / "topics_pool.json"
    if not topics_pool.exists():
        warnings.append("选题池配置文件不存在")
        if args.fix:
            config_dir.mkdir(parents=True, exist_ok=True)
            topics_pool.write_text(
                '{"categories": {}}',
                encoding="utf-8",
            )
            print(f"  ✅ 已创建默认选题池: config/topics_pool.json")

    # 检查脚本文件
    scripts_dir = base / "04-脚本工具"
    expected_scripts = [
        "env_check.py",
        "daily_topic_selector.py",
        "batch_generate.py",
        "make_cards.py",
        "make_cards2.py",
        "error_scanner.py",
        "cost_tracker.py",
        "parse_douyin.py",
        "replicate_viral.py",
        "lipsync_batch.py",
    ]
    for sname in expected_scripts:
        s = scripts_dir / sname
        if not s.exists():
            issues.append(f"缺失脚本: {sname}")

    # 打印报告
    print("📋 扫描结果：")
    print()

    if issues:
        print(f"  ❌ 发现 {len(issues)} 个问题：")
        for i in issues:
            print(f"     • {i}")
        print()
    else:
        print("  ✅ 未发现严重问题")
        print()

    if warnings:
        print(f"  ⚠️  发现 {len(warnings)} 个警告：")
        for w in warnings:
            print(f"     • {w}")
        print()

    print("-" * 60)
    if not issues and not warnings:
        print("✅ 工作流环境检查通过")
    elif not issues:
        print("⚠️  存在警告，但不影响基本运行")
    else:
        print("❌ 存在问题，建议修复后再运行工作流")
    print("-" * 60)
    print()
    print("💡 提示：这是一个占位脚本，错误扫描功能已部分可用。")
    print("   使用 --fix 参数可尝试自动创建缺失的目录和文件。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
