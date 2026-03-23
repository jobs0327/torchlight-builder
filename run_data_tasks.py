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
    "legendary-gear": "sync_legendary_gear.py",
    "legendary-gear-icons": "sync_legendary_gear.py",
    "legendary-gear-attach-icons": "sync_legendary_gear.py",
    "legendary-gear-effects": "sync_legendary_gear.py",
    "legendary-gear-finalize-icons": "sync_legendary_gear.py",
    "crafted-affixes": "sync_crafted_gear_affixes.py",
    "tower-sequence-affixes": "sync_tower_sequence_affixes.py",
    "pactspirit": "sync_pactspirit.py",
    "pactspirit-icons": "sync_pactspirit.py",
    "pactspirit-icons-only": "sync_pactspirit.py",
    "pactspirit-finalize-icons": "sync_pactspirit.py",
    "hero-memories": "sync_hero_memories.py",
    "hero-memories-icons": "sync_hero_memories.py",
    "crafted-gear-bases": "sync_crafted_gear_bases.py",
    "crafted-gear-bases-icons": "sync_crafted_gear_bases.py",
    "crafted-gear-bases-attach-icons": "sync_crafted_gear_bases.py",
}


def run_task(task_name: str) -> int:
    script = TASKS[task_name]
    root = Path(__file__).resolve().parent
    cmd = [sys.executable, str(root / script)]
    if task_name == "exclusive-support-stats":
        cmd.append("--exclusive-support-only")
    if task_name == "legendary-gear-icons":
        cmd.append("--cache-icons")
    if task_name == "legendary-gear-attach-icons":
        cmd.append("--attach-local-icons")
    if task_name == "legendary-gear-effects":
        cmd.append("--enrich-effects")
    if task_name == "legendary-gear-finalize-icons":
        cmd.append("--finalize-local-icons")
    if task_name == "crafted-gear-bases-icons":
        cmd.append("--icons-only")
    if task_name == "crafted-gear-bases-attach-icons":
        cmd.append("--attach-local-icons")
    if task_name == "pactspirit-icons":
        cmd.append("--cache-icons")
    if task_name == "pactspirit-icons-only":
        cmd.append("--icons-only")
    if task_name == "pactspirit-finalize-icons":
        cmd.append("--finalize-local-icons")
    if task_name == "hero-memories-icons":
        cmd.append("--cache-icons")
    return subprocess.call(cmd, cwd=root)


def main() -> int:
    parser = argparse.ArgumentParser(description="统一执行项目根目录数据脚本")
    parser.add_argument(
        "task",
        choices=[*sorted(TASKS.keys()), "all"],
        help="要执行的任务",
    )
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
