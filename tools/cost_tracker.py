#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成本汇总脚本

功能：
  - --summary: 汇总指定天数的 API 调用成本
  - --add: 添加一条成本记录到日志
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_log_dir():
    """获取成本日志目录（基于脚本位置动态计算）"""
    return Path(__file__).resolve().parent.parent / "06-运营日志"


def load_cost_log(log_dir: Path):
    """加载成本日志"""
    log_file = log_dir / "cost_log.json"
    if not log_file.exists():
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_cost_log(log_dir: Path, logs):
    """保存成本日志"""
    log_file = log_dir / "cost_log.json"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存日志失败: {e}", file=sys.stderr)
        return False


def generate_demo_data(days: int):
    """生成演示数据"""
    now = datetime.now()
    services = ["DeepSeek", "DashScope", "Seedance", "Pixabay", "Pexels"]
    logs = []
    for i in range(days):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        for svc in services:
            logs.append({
                "date": date,
                "service": svc,
                "cost": round(0.05 + (i % 3) * 0.02 + (hash(svc + date) % 100) / 500, 2),
                "calls": 5 + (hash(date) % 20),
            })
    return logs


def cmd_summary(args):
    """成本汇总子命令"""
    log_dir = Path(args.log_dir) if args.log_dir else get_log_dir()
    logs = load_cost_log(log_dir)

    if not logs:
        print("📁 未找到成本日志，使用演示数据")
        logs = generate_demo_data(args.days)

    # 汇总
    cutoff = datetime.now() - timedelta(days=args.days)
    total = 0.0
    by_service = {}
    count = 0
    recent_logs = []

    for entry in logs:
        try:
            d = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
            if d >= cutoff:
                cost = entry.get("cost", 0)
                total += cost
                count += 1
                svc = entry.get("service", "unknown")
                by_service[svc] = by_service.get(svc, 0) + cost
                recent_logs.append(entry)
        except Exception:
            pass

    # 输出结构化 JSON（供 app.py 解析）
    result = {
        "total": round(total, 2),
        "days": args.days,
        "count": count,
        "by_service": {k: round(v, 2) for k, v in sorted(by_service.items(), key=lambda x: -x[1])},
        "entries": recent_logs[-20:],
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_add(args):
    """添加成本记录子命令"""
    log_dir = get_log_dir()
    logs = load_cost_log(log_dir)

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": datetime.now().strftime("%H:%M:%S"),
        "service": args.service or args.mode or "unknown",
        "topic_id": args.topic_id or "",
        "title": args.title or "",
        "mode": args.mode or "auto",
        "cost": float(args.cost or 0),
        "calls": 1,
    }
    logs.append(entry)

    if save_cost_log(log_dir, logs):
        result = {"success": True, "entry": entry, "total_entries": len(logs)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    else:
        print(json.dumps({"success": False, "error": "保存失败"}, ensure_ascii=False))
        return 1


def main():
    parser = argparse.ArgumentParser(description="API 成本追踪")
    subparsers = parser.add_subparsers(dest="command")

    # summary 子命令
    p_summary = subparsers.add_parser("summary", help="汇总成本")
    p_summary.add_argument("--days", "-d", type=int, default=7, help="汇总天数（默认 7）")
    p_summary.add_argument("--log_dir", type=str, default="", help="日志目录")

    # add 子命令
    p_add = subparsers.add_parser("add", help="添加成本记录")
    p_add.add_argument("--topic-id", type=str, default="", help="选题ID")
    p_add.add_argument("--title", type=str, default="", help="标题")
    p_add.add_argument("--mode", type=str, default="auto", help="模式")
    p_add.add_argument("--service", type=str, default="", help="服务名")
    p_add.add_argument("--cost", type=str, default="0", help="成本金额")

    # 为了兼容旧式调用（--summary 作为 flag）
    parser.add_argument("--summary", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--days", "-d", type=int, default=7, help="汇总天数（默认 7）")
    parser.add_argument("--log_dir", type=str, default="", help="日志目录")
    parser.add_argument("--add", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--topic-id", type=str, default="", help=argparse.SUPPRESS)
    parser.add_argument("--title", type=str, default="", help=argparse.SUPPRESS)
    parser.add_argument("--mode", type=str, default="auto", help=argparse.SUPPRESS)
    parser.add_argument("--cost", type=str, default="0", help=argparse.SUPPRESS)

    args = parser.parse_args()

    # 优先使用子命令模式
    if args.command == "summary":
        return cmd_summary(args)
    elif args.command == "add":
        return cmd_add(args)

    # 兼容旧式 flag 模式
    if args.summary:
        return cmd_summary(args)
    if args.add:
        return cmd_add(args)

    # 默认行为：汇总
    return cmd_summary(args)


if __name__ == "__main__":
    sys.exit(main())
