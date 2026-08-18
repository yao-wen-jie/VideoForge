#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日选题脚本（占位/演示版本）

功能：
  - 从选题池读取选题，随机选出 N 条
  - 打印候选选题列表

说明：
  这是一个占位脚本，实际使用时需要接入真实的选题数据源
  （如 Google Trends、微博热搜、竞品分析库等）。
"""

import argparse
import json
import random
import sys
from pathlib import Path


DEFAULT_TOPICS = [
    {"id": "t001", "title": "10个你不知道的冷知识", "category": "科普"},
    {"id": "t002", "title": "为什么猫喜欢纸箱？", "category": "萌宠"},
    {"id": "t003", "title": "3分钟学会做蛋炒饭", "category": "美食"},
    {"id": "t004", "title": "早起的好处你知道吗", "category": "生活"},
    {"id": "t005", "title": "手机隐藏的5个功能", "category": "科技"},
    {"id": "t006", "title": "办公室拉伸操", "category": "健康"},
    {"id": "t007", "title": "周末去哪儿玩", "category": "旅游"},
]


def load_topics_pool(pool_path: Path = None):
    """尝试从配置目录加载选题池"""
    if pool_path and pool_path.exists():
        try:
            return json.loads(pool_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # 尝试默认路径
    default = Path(__file__).resolve().parent.parent / "config" / "topics_pool.json"
    if default.exists():
        try:
            return json.loads(default.read_text(encoding="utf-8"))
        except Exception:
            pass

    return None


def main():
    parser = argparse.ArgumentParser(
        description="从选题池中随机选出今日候选选题"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=3,
        help="选题数量（默认 3）",
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        default="",
        help="分类筛选（留空为全部）",
    )
    parser.add_argument(
        "--pool",
        type=str,
        default="",
        help="选题池 JSON 文件路径",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("📋  每日选题（占位/演示版本）")
    print("=" * 60)
    print()

    # 加载选题
    pool = load_topics_pool(Path(args.pool) if args.pool else None)
    if pool and "categories" in pool:
        topics = []
        for cat_key, cat in pool["categories"].items():
            if args.category and cat_key != args.category:
                continue
            for t in cat.get("topics", []):
                t["category"] = cat_key
                topics.append(t)
        print(f"📁 已加载选题池：{len(topics)} 条选题")
    else:
        topics = DEFAULT_TOPICS
        print("📁 未找到选题池，使用内置演示数据")

    # 筛选
    if args.category:
        topics = [t for t in topics if t.get("category") == args.category]

    if not topics:
        print(f"⚠️  分类 '{args.category}' 下没有选题")
        return 0

    # 随机选取
    count = min(args.count, len(topics))
    selected = random.sample(topics, count)

    print()
    print(f"🎯 今日候选选题（共 {count} 条）：")
    print("-" * 60)
    for i, t in enumerate(selected, 1):
        cat = t.get("category", "未分类")
        print(f"  {i}. [{cat}] {t.get('title', '无标题')}")
    print("-" * 60)
    print()
    print("💡 提示：这是一个占位脚本。")
    print("   实际使用时请接入真实选题数据源（Google Trends / 微博热搜等）。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
