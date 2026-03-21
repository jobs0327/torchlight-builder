#!/usr/bin/env python3
"""
从 tlidb 「专属辅助技能」列表页抓取标签与技能条目（崇高 / 华贵），
结构对齐 supportSkillTags.json，供前端与普通辅助合并展示。

由 sync_noble_support_skill_tags.py / sync_magnificent_support_skill_tags.py 调用。
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def extract_exclusive_support_tags(html: str) -> list[str]:
    """
    列表页标签在「px-2 pt-2」筛选按钮上，使用 data-filter="中文"，
    而非普通辅助页的纯文本 Tag 区块。
    """
    m = re.search(
        r'<div\s+class="px-2 pt-2">(.+?)</div>\s*<script>',
        html,
        re.S,
    )
    if not m:
        raise RuntimeError("页面中未找到专属辅助标签筛选区（px-2 pt-2）")

    chunk = m.group(1)
    raw = re.findall(r'data-filter="([^"]+)"', chunk)
    excluded = {"技能等级", "技能", "帮助手册", "主动技能", "辅助技能"}
    seen: set[str] = set()
    tags: list[str] = []
    for t in raw:
        t = unescape(t).strip()
        if not t or not re.fullmatch(r"[\u4e00-\u9fa5]{1,8}", t):
            continue
        if t in excluded or t in seen:
            continue
        seen.add(t)
        tags.append(t)
    if not tags:
        raise RuntimeError("未从筛选区解析到任何中文标签")
    return tags


# 含中文冒号、括号与较长译名（如「专注射击：蓄锐（崇高）」）
_SKILL_NAME_RE = re.compile(
    r"^[\u4e00-\u9fa5A-Za-z0-9·\-\(\)（）'：\s]{1,80}$"
)


def extract_exclusive_support_skills(
    html: str, allowed_tags: set[str]
) -> list[dict[str, object]]:
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
        if not name or not _SKILL_NAME_RE.fullmatch(name):
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


def cache_skill_icons(
    skills: list[dict[str, object]], icon_dir: Path, public_prefix: str
) -> tuple[int, int, int]:
    icon_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0

    for skill in skills:
        skill_id = str(skill.get("id", "")).strip()
        remote_url = str(skill.get("iconUrl", "")).strip()
        if not skill_id or not remote_url:
            continue

        parsed = urlparse(remote_url)
        ext = Path(parsed.path).suffix or ".webp"
        filename = f"{safe_filename(skill_id)}{ext}"
        local_file = icon_dir / filename
        local_public_url = f"{public_prefix}/{filename}"

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


def run(source_url: str, out_file: Path, icon_cache_dir: Path, icon_public_prefix: str) -> None:
    req = Request(
        source_url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    tags = extract_exclusive_support_tags(html)
    support_skills = extract_exclusive_support_skills(html, set(tags))

    payload = {
        "source": source_url,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(tags),
        "tags": tags,
        "supportSkillCount": len(support_skills),
        "supportSkills": support_skills,
    }

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"已写入列表（尚未缓存图标）: 标签 {payload['count']} 个，技能 {payload['supportSkillCount']} 个 -> {out_file}",
        flush=True,
    )

    downloaded_count, skipped_count, failed_count = cache_skill_icons(
        support_skills, icon_cache_dir, icon_public_prefix
    )

    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"图标下载: {downloaded_count}，缓存复用: {skipped_count}，失败: {failed_count}；已更新 localIconUrl",
        flush=True,
    )
