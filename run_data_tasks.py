#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TASKS = {
    "hero-data": "build_hero_data.py",
    "talent-data": "build_all_talent_trees.py",
    "active-skill-tags": "sync_active_skill_tags.py",
}


def run_task(task_name: str) -> int:
    script = TASKS[task_name]
    root = Path(__file__).resolve().parent
    cmd = [sys.executable, str(root / script)]
    return subprocess.call(cmd, cwd=root)


def main() -> int:
    parser = argparse.ArgumentParser(description="统一执行项目根目录数据脚本")
    parser.add_argument("task", choices=[*TASKS.keys(), "all"], help="要执行的任务")
    args = parser.parse_args()

    if args.task == "all":
        for name in ("hero-data", "talent-data", "active-skill-tags"):
            print(f"[run] {name}")
            code = run_task(name)
            if code != 0:
                return code
        return 0

    print(f"[run] {args.task}")
    return run_task(args.task)


if __name__ == "__main__":
    raise SystemExit(main())
