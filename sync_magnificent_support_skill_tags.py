#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Magnificent_Support_Skill 抓取「专属辅助技能（华贵）」列表，
写入 torchlight-builder/src/data/skills/magnificentSupportSkillTags.json，
图标缓存到 public/assets/skills/support/magnificent/。

仓库根目录: python sync_magnificent_support_skill_tags.py
"""
from __future__ import annotations

from pathlib import Path

from exclusive_support_skill_tags_sync import run

SOURCE_URL = "https://tlidb.com/cn/Magnificent_Support_Skill"
OUT_FILE = Path("torchlight-builder/src/data/skills/magnificentSupportSkillTags.json")
ICON_CACHE_DIR = Path("torchlight-builder/public/assets/skills/support/magnificent")
ICON_PUBLIC_PREFIX = "/assets/skills/support/magnificent"

if __name__ == "__main__":
    run(SOURCE_URL, OUT_FILE, ICON_CACHE_DIR, ICON_PUBLIC_PREFIX)
