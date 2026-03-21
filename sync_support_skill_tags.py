#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Support_Skill 抓取辅助技能标签与技能列表，
写入 torchlight-builder/src/data/skills/supportSkillTags.json，
并缓存图标到 public/assets/skills/support/。

用法：在仓库根目录执行  python sync_support_skill_tags.py
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

SOURCE_URL = "https://tlidb.com/cn/Support_Skill"
OUT_FILE = Path("torchlight-builder/src/data/skills/supportSkillTags.json")
ICON_CACHE_DIR = Path("torchlight-builder/public/assets/skills/support")
ICON_PUBLIC_PREFIX = "/assets/skills/support"


def strip_html(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_support_skill_tags(html: str) -> list[str]:
    plain_text = strip_html(html)
    matches = re.findall(r"辅助技能 Tag /\d+\s+(.+?)\s+Reset", plain_text)
    if not matches:
        raise RuntimeError("页面中未找到「辅助技能 Tag」区块")

    content = matches[-1].strip()
    if not content:
        raise RuntimeError("标签区块为空，未提取到标签")

    excluded = {"技能等级", "技能", "帮助手册", "主动技能", "辅助技能"}
    seen: set[str] = set()
    tags: list[str] = []
    for token in content.split():
        t = token.strip()
        if not t:
            continue
        if not re.fullmatch(r"[\u4e00-\u9fa5]{1,8}", t):
            continue
        if t in excluded or t in seen:
            continue
        seen.add(t)
        tags.append(t)
    return tags


def extract_support_skills(html: str, allowed_tags: set[str]) -> list[dict[str, object]]:
    pattern = re.compile(
        r'<div class="d-flex border-top rounded">.*?'
        r'<a[^>]*href="([^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*>\s*</a>.*?'
        r'<a[^>]*href="[^"]+"[^>]*>\s*([^<]+?)\s*</a>\s*'
        r'<div>\s*((?:<span[^>]*>[^<]+</span>\s*,?\s*)+)</div>.*?</div>\s*</div>',
        re.S,
    )
    tag_pattern = re.compile(r"<span[^>]*>([^<]+)</span>")

    skills: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for href, icon_url, raw_name, tags_html in pattern.findall(html):
        if href.startswith(("http://", "https://", "#", "/", "javascript:")):
            continue

        name = unescape(raw_name).strip()
        if not name or not re.fullmatch(
            r"[\u4e00-\u9fa5A-Za-z0-9·\-\(\)（）' ]{1,40}", name
        ):
            continue

        raw_tags = [unescape(t).strip() for t in tag_pattern.findall(tags_html)]
        tags = [t for t in raw_tags if t in allowed_tags]
        if not tags:
            continue

        skill_id = href.strip()
        if skill_id in seen_ids:
            continue

        seen_ids.add(skill_id)
        skills.append({"id": skill_id, "name": name, "iconUrl": icon_url.strip(), "tags": tags})

    return skills


def safe_filename(raw: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
    return normalized or "skill_icon"


def download_icon(url: str, output: Path) -> None:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Referer": "https://tlidb.com/",
            "Origin": "https://tlidb.com",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=30) as resp:
        data = resp.read()
    output.write_bytes(data)


def cache_support_skill_icons(support_skills: list[dict[str, object]]) -> tuple[int, int, int]:
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0

    for skill in support_skills:
        skill_id = str(skill.get("id", "")).strip()
        remote_url = str(skill.get("iconUrl", "")).strip()
        if not skill_id or not remote_url:
            continue

        parsed = urlparse(remote_url)
        ext = Path(parsed.path).suffix or ".webp"
        filename = f"{safe_filename(skill_id)}{ext}"
        local_file = ICON_CACHE_DIR / filename
        local_public_url = f"{ICON_PUBLIC_PREFIX}/{filename}"

        if local_file.exists():
            skipped += 1
        else:
            try:
                download_icon(remote_url, local_file)
                downloaded += 1
            except Exception:
                failed += 1

        if local_file.exists():
            skill["localIconUrl"] = local_public_url

    return downloaded, skipped, failed


def run() -> None:
    req = Request(
        SOURCE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    tags = extract_support_skill_tags(html)
    support_skills = extract_support_skills(html, set(tags))
    downloaded_count, skipped_count, failed_count = cache_support_skill_icons(support_skills)

    payload = {
        "source": SOURCE_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(tags),
        "tags": tags,
        "supportSkillCount": len(support_skills),
        "supportSkills": support_skills,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"辅助技能标签: {payload['count']} 个，辅助技能: {payload['supportSkillCount']} 个，"
        f"图标下载: {downloaded_count}，缓存复用: {skipped_count}，失败: {failed_count} -> {OUT_FILE}"
    )


if __name__ == "__main__":
    run()
