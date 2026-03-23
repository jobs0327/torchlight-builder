#!/usr/bin/env python3
"""
从 TLIDB「高塔序列」页抓取武器 / 盾牌可研发的序列词缀（中阶序列、高阶序列）。

页面为两列表格：Affix、来源（武器类型中文），效果格内含 data-modifier-id、text-mod 数值、
data-chip 芯片颜色档位（如 1|2|6）。与装备子类页「词缀」表结构不同，故单独脚本输出。

输出：torchlight-builder/src/data/equipment/towerSequenceAffixes.json

用法（仓库根目录）：
  python sync_tower_sequence_affixes.py
  python sync_tower_sequence_affixes.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen

PAGE_CN = "https://tlidb.com/cn/TOWER_Sequence"
OUT_PATH = Path("torchlight-builder/src/data/equipment/towerSequenceAffixes.json")

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
    re.S | re.I,
)
MODIFIER_ID_RE = re.compile(r'data-modifier-id="(\d+)"')
TEXT_MOD_RE = re.compile(r'<span class="text-mod">(.*?)</span>', re.S | re.I)
CHIP_RE = re.compile(r'data-chip="([^"]+)"')

# 来源列中文 → 与 craftedAffixes / 装备子类 slug 一致
SOURCE_ZH_TO_SLUG: dict[str, str] = {
    "爪": "Claw",
    "匕首": "Dagger",
    "单手剑": "One-Handed_Sword",
    "单手斧": "One-Handed_Axe",
    "单手锤": "One-Handed_Hammer",
    "手枪": "Pistol",
    "手杖": "Cane",
    "弓": "Bow",
    "弩": "Crossbow",
    "火枪": "Musket",
    "火炮": "Fire_Cannon",
    "双手剑": "Two-Handed_Sword",
    "双手斧": "Two-Handed_Axe",
    "双手锤": "Two-Handed_Hammer",
    "武杖": "Tin_Staff",
    "锡杖": "Tin_Staff",
    "法杖": "Rod",
    "魔杖": "Wand",
    "灵杖": "Scepter",
    "力量盾牌": "STR_Shield",
    "敏捷盾牌": "DEX_Shield",
    "智慧盾牌": "INT_Shield",
}


def fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://tlidb.com/",
        },
    )
    with urlopen(req, timeout=90) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_inline_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<script[^>]*>.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_chip(effect_cell: str) -> str | None:
    m = CHIP_RE.search(effect_cell)
    return m.group(1).strip() if m else None


def effect_plain_cleanup(plain: str, affix_type: str | None) -> str:
    """去掉效果末尾「中阶序列 1|2|6」等与芯片展示重复片段，便于与装备子类页文案接近。"""
    s = plain
    if affix_type == "中阶序列":
        s = re.sub(r"\s*中阶序列\s*[\d|]+\s*$", "", s)
    elif affix_type == "高阶序列":
        s = re.sub(r"\s*高阶序列\s*[\d|]+\s*$", "", s)
    return re.sub(r"\s+", " ", s).strip()


def detect_sequence_type(effect_cell_plain: str) -> str | None:
    if "高阶序列" in effect_cell_plain:
        return "高阶序列"
    if "中阶序列" in effect_cell_plain:
        return "中阶序列"
    return None


def parse_table(html: str) -> tuple[list[dict[str, object]], list[str]]:
    start = html.find("<tbody>")
    end = html.find("</tbody>", start)
    if start < 0 or end < 0:
        raise RuntimeError("未找到高塔序列表格 tbody")
    sub = html[start:end]
    rows: list[dict[str, object]] = []
    unknown_sources: list[str] = []
    seen_unknown: set[str] = set()

    for m in ROW_RE.finditer(sub):
        effect_cell, source_cell_raw = m.group(1), m.group(2)
        if "data-modifier-id" not in effect_cell:
            continue
        mid_m = MODIFIER_ID_RE.search(effect_cell)
        if not mid_m:
            continue
        modifier_id = mid_m.group(1)
        source_zh = strip_inline_html(source_cell_raw)
        category_slug = SOURCE_ZH_TO_SLUG.get(source_zh)
        if not category_slug:
            if source_zh and source_zh not in seen_unknown:
                seen_unknown.add(source_zh)
                unknown_sources.append(source_zh)
            continue

        raw_plain = strip_inline_html(effect_cell)
        affix_type = detect_sequence_type(raw_plain)
        if not affix_type:
            affix_type = "中阶序列"

        plain = effect_plain_cleanup(raw_plain, affix_type)
        chip = extract_chip(effect_cell)

        value_spans: list[str] = []
        for vm in TEXT_MOD_RE.finditer(effect_cell):
            raw = vm.group(1)
            raw = raw.replace("&ndash;", "–")
            value_spans.append(strip_inline_html(raw))

        rows.append(
            {
                "modifierId": modifier_id,
                "tier": None,
                "itemLevel": None,
                "weight": None,
                "affixType": affix_type,
                "source": source_zh,
                "categorySlug": category_slug,
                "effectPlain": plain,
                "valueSpans": value_spans,
                "chipPattern": chip,
            }
        )

    return rows, unknown_sources


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 TLIDB 高塔序列词缀")
    parser.add_argument("--dry-run", action="store_true", help="只抓取并打印统计，不写文件")
    args = parser.parse_args()

    print(f"[fetch] {PAGE_CN}", flush=True)
    html = fetch_html(PAGE_CN)
    rows, unknown = parse_table(html)
    if unknown:
        print(f"[warn] 未映射的来源列（已跳过相关行）: {unknown}", flush=True)

    payload = {
        "kind": "towerSequenceAffixes",
        "sourceUrl": PAGE_CN,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modifierCount": len(rows),
        "modifiers": rows,
    }
    print(f"[parsed] modifiers={len(rows)}", flush=True)
    if args.dry_run:
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[write] {OUT_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
