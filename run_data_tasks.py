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
    "support-skill-tags": "sync_support_skill_tags.py",
    "noble-support-skill-tags": "sync_noble_support_skill_tags.py",
    "magnificent-support-skill-tags": "sync_magnificent_support_skill_tags.py",
    "passive-skill-tags": "sync_passive_skill_tags.py",
    "skill-page-stats": "sync_skill_page_stats.py",
    "exclusive-support-stats": "sync_skill_page_stats.py",
}


def run_task(task_name: str) -> int:
    script = TASKS[task_name]
    root = Path(__file__).resolve().parent
    cmd = [sys.executable, str(root / script)]
    if task_name == "exclusive-support-stats":
        cmd.append("--exclusive-support-only")
    return subprocess.call(cmd, cwd=root)


def main() -> int:
    parser = argparse.ArgumentParser(description="统一执行项目根目录数据脚本")
    parser.add_argument("task", choices=[*TASKS.keys(), "all"], help="要执行的任务")
    args = parser.parse_args()

    if args.task == "all":
        for name in (
            "hero-data",
            "talent-data",
            "active-skill-tags",
            "support-skill-tags",
            "passive-skill-tags",
        ):
            print(f"[run] {name}")
            code = run_task(name)
            if code != 0:
                return code
        return 0

    print(f"[run] {args.task}")
    return run_task(args.task)


if __name__ == "__main__":
    raise SystemExit(main())
