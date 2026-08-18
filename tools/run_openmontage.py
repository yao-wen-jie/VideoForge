#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenMontage 视频生成 - 存根版本
调用外部 OpenMontage 工具生成视频
"""
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(description="OpenMontage 视频生成")
    parser.add_argument("--script", required=True, help="脚本文件路径")
    parser.add_argument("--assets", default="", help="素材目录")
    parser.add_argument("--output", default="output.mp4", help="输出视频路径")
    args = parser.parse_args()

    print(f"[OpenMontage] 开始生成视频")
    print(f"  脚本: {args.script}")
    print(f"  素材: {args.assets or '默认素材'}")
    print(f"  输出: {args.output}")
    print()
    print("注意: 完整功能需要安装 OpenMontage 工具")
    print("      当前为存根版本，仅生成方案文件")

    result = {
        "status": "stub",
        "output": args.output,
        "message": "OpenMontage 未安装，此为存根输出。如需完整功能请安装 OpenMontage。",
    }

    with open(args.output + ".json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n方案文件已保存: {args.output}.json")


if __name__ == "__main__":
    main()
