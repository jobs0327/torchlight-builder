#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Hero_Memories 抓取英雄追忆汇总页数据：
- 三种追忆物品（图标、名称、详情路径）
- 词缀：自「基础属性 / 固有词缀 / 随机词缀」子页签五列表格抓取（含各 Tier 档位，与 TLIDB 分表一致）

输出：torchlight-builder/src/data/hero_memories.json
图标：torchlight-builder/public/assets/hero_memories（可选 --cache-icons）

用法（仓库根目录）：
  python sync_hero_memories.py
  python sync_hero_memories.py --dry-run
  python sync_hero_memories.py --cache-icons
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PAGE_URL = "https://tlidb.com/cn/Hero_Memories"
OUT_FILE = Path("torchlight-builder/src/data/hero_memories.json")
ICON_DIR = Path("torchlight-builder/public/assets/hero_memories")
ICON_PREFIX = "/assets/hero_memories"
DETAIL_BASE = "https://tlidb.com/cn"
REQUEST_DELAY_SEC = 0.2

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# Item 卡片（与契灵列表类似）
ITEM_CARD_RE = re.compile(
    r'<div class="d-flex border-top rounded">'
    r'<div class="flex-shrink-0">'
    r'<img src="([^"]+)"[^>]*>'
    r"</div>"
    r'<div class="flex-grow-1[^"]*">'
    r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
    re.S,
)

MODIFIER_ID_RE = re.compile(r'data-modifier-id="(\d+)"')

# 子页签「基础属性 / 固有词缀 / 随机词缀」中的五列表格：Tier | Modifier | Level | Weight | 来源
# 同一词条的 T1/T2/T3 为不同 modifierId，与 TLIDB 页 [#固有词缀](https://tlidb.com/cn/Hero_Memories#%E5%9B%BA%E6%9C%89%E8%AF%8D%E7%BC%80) 一致。
TIER5_ROW_RE = re.compile(
    r'<tr><td>(\d+)</td><td>(.*?)</td><td>(\d+)</td><td>(\d+)</td><td><a[^>]*href="([^"]+)"[^>]*>([^<]+)</a></td></tr>',
    re.S,
)

TAB_PANE_ORDER = (
    ("基础属性", "固有词缀", "基础属性"),
    ("固有词缀", "随机词缀", "固有词缀"),
    ("随机词缀", "英雄追忆-成长之路", "随机词缀"),
)


def memory_rarity_from_tier(tier: int | None) -> str:
    # 当前追忆词缀口径：T3=魔法，T2=稀有，T1=卓越，T0=至臻；缺省归类普通。
    if tier == 3:
        return "魔法"
    if tier == 2:
        return "稀有"
    if tier == 1:
        return "卓越"
    if tier == 0:
        return "至臻"
    return "普通"


def fetch_html(url: str, *, timeout_sec: int = 90) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://tlidb.com/",
        },
    )
    with urlopen(req, timeout=timeout_sec) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_inline_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<script[^>]*>.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", t).strip()


def safe_filename(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s)
    return s.strip("_") or "icon"


def download_icon(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://tlidb.com/"})
    try:
        with urlopen(req, timeout=45) as resp:
            dest.write_bytes(resp.read())
        return True
    except Exception:
        return False


def parse_items(html: str) -> list[dict[str, object]]:
    """Item 标签页中的追忆物品卡片。"""
    block_start = html.find('id="Item"')
    if block_start < 0:
        return []
    block = html[block_start : block_start + 8000]
    items: list[dict[str, object]] = []
    for m in ITEM_CARD_RE.finditer(block):
        cdn_url, href, name = m.group(1), m.group(2), strip_inline_html(m.group(3))
        slug = href.strip()
        detail_path = f"/cn/{slug}" if not href.startswith("/") else href
        items.append(
            {
                "id": slug,
                "name": name,
                "detailPath": detail_path if detail_path.startswith("/") else f"/cn/{detail_path}",
                "cdnIconUrl": cdn_url,
                "iconUrl": cdn_url,
            }
        )
    return items


def slice_tab_pane(html: str, start_id: str, end_id: str) -> str:
    """截取 Bootstrap tab-pane：从 `<div id="{start_id}"` 到下一个 `<div id="{end_id}"`。"""
    start = html.find(f'<div id="{start_id}"')
    if start < 0:
        return ""
    end = html.find(f'<div id="{end_id}"', start + 1)
    return html[start:end] if end >= 0 else html[start:]


def parse_tier5_table(html_chunk: str, category: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for m in TIER5_ROW_RE.finditer(html_chunk):
        tier_s, raw_mod, level_s, weight_s, href, source_name = m.groups()
        tier = int(tier_s)
        level = int(level_s)
        weight = int(weight_s)
        mid_m = MODIFIER_ID_RE.search(raw_mod)
        mid = mid_m.group(1) if mid_m else None
        effect_text = strip_inline_html(raw_mod)
        slug = href.strip()
        detail_path = f"/cn/{slug}" if not href.startswith("/") else href
        rows.append(
            {
                "modifierId": mid,
                "effectText": effect_text,
                "sourceId": slug,
                "sourceName": strip_inline_html(source_name),
                "sourcePath": detail_path if detail_path.startswith("/") else f"/cn/{detail_path}",
                "category": category,
                "tier": tier,
                "tierLabel": f"T{tier}",
                "level": level,
                "weight": weight,
                "memoryRarity": memory_rarity_from_tier(tier),
            }
        )
    return rows


def parse_affixes(html: str) -> list[dict[str, object]]:
    """从「基础属性」「固有词缀」「随机词缀」三个子页签的五列表格抓取（含各 Tier 档位）。"""
    rows: list[dict[str, object]] = []
    for start_id, end_id, category in TAB_PANE_ORDER:
        chunk = slice_tab_pane(html, start_id, end_id)
        rows.extend(parse_tier5_table(chunk, category))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="不写入 JSON")
    ap.add_argument("--cache-icons", action="store_true", help="下载物品图标到本地")
    args = ap.parse_args()

    print(f"[hero-memories] fetch {PAGE_URL}")
    html = fetch_html(PAGE_URL)
    items = parse_items(html)
    affixes = parse_affixes(html)
    print(f"[hero-memories] items={len(items)} affixes={len(affixes)}")

    if args.cache_icons and items:
        ICON_DIR.mkdir(parents=True, exist_ok=True)
        for it in items:
            cid = str(it["id"])
            ext = Path(urlparse(str(it["cdnIconUrl"])).path).suffix or ".webp"
            local = ICON_DIR / f"{cid}{ext}"
            if download_icon(str(it["cdnIconUrl"]), local):
                it["iconUrl"] = f"{ICON_PREFIX}/{local.name}"
            time.sleep(REQUEST_DELAY_SEC)

    payload = {
        "sourceUrl": PAGE_URL,
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "affixes": affixes,
    }

    if args.dry_run:
        print(json.dumps({**payload, "affixes": f"<{len(affixes)} rows>"}, ensure_ascii=False, indent=2))
        return

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[hero-memories] wrote {OUT_FILE}")


if __name__ == "__main__":
    main()
