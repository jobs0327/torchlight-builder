#!/usr/bin/env python3
"""
从 TLIDB 各「装备子类」页面抓取「词缀」标签下的自制 / 稀有装备词缀数据。

每个子类页（与传奇装备相同的 slug，如 STR_Helmet、One-Handed_Sword）在「词缀 / Affix」分栏中
提供表格：词缀效果、来源、类型（基础词缀、初阶前缀、进阶后缀等）。效果格内含
data-modifier-id 与 tooltip「Tier, Level, Weight」，其中 Tier 即游戏内 T 阶（0 常为最高档）。

英文站类型列为 Basic Pre-fix、Advanced Suffix 等时，会规范化为与中文站一致的 affixType，便于前端识别前后缀槽位。
默认抓取地址为 BASE（中文 /cn）。

输出：按部位（子类 slug）分文件写入
  torchlight-builder/src/data/equipment/craftedAffixes/<slug>.json
并生成 index.json 汇总。

每条词缀记录包含：
  - modifierId, tier, itemLevel, weight（来自 tooltip）
  - affixType（类型列）, source（来源列）
  - effectPlain（去标签后的展示文本）, valueSpans（text-mod 内的数值区间原文列表）

相关脚本：打造用「Item」基底列表见 sync_crafted_gear_bases.py（输出 craftedGearBases/）。
武器 / 盾牌「高塔序列」（中阶、高阶）为独立页面表格，见 sync_tower_sequence_affixes.py（输出 towerSequenceAffixes.json）。

用法（仓库根目录）：
  python sync_crafted_gear_affixes.py
  python sync_crafted_gear_affixes.py --dry-run
  python sync_crafted_gear_affixes.py --only STR_Helmet
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://tlidb.com/cn"
INDEX_URL = f"{BASE}/Legendary_Gear"
OUT_DIR = Path("torchlight-builder/src/data/equipment/craftedAffixes")
REQUEST_DELAY_SEC = 0.85

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SKIP_CATEGORY_EXACT = frozenset(
    {"Hero_Memories", "Divinity_Slate", "Destiny", "Ethereal_Prism"}
)

TOOLTIP_RE = re.compile(
    r'data-bs-title="Tier:\s*(\d+)\s*,\s*Level:\s*(\d+)\s*,\s*Weight:\s*(\d+)"'
)
MODIFIER_ID_RE = re.compile(r'data-modifier-id="(\d+)"')
TEXT_MOD_RE = re.compile(
    r'<span class="text-mod">(.*?)</span>', re.S | re.I
)
ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
    re.S | re.I,
)


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
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def extract_gear_category_block(html: str) -> str:
    marker = 'data-i18n="TextTable_GameFunc|value|Func_FilterType_Type1">Gear</div>'
    start = html.find(marker)
    if start < 0:
        start = html.find(">Gear</div>")
        if start < 0:
            raise RuntimeError("未找到 Gear 筛选卡片（页面结构可能已变）")
        start = html.find(">", start) + 1
    else:
        start = html.find(">", start) + 1
    end = html.find('<ul class="nav nav-tabs d-flex flex-wrap"', start)
    if end < 0:
        raise RuntimeError("未找到 Gear 区块结束边界（nav-tabs）")
    return html[start:end]


def should_skip_category(slug: str) -> bool:
    if slug.endswith("_Season"):
        return True
    if slug in SKIP_CATEGORY_EXACT:
        return True
    if slug.startswith("Vorax_"):
        return True
    return False


def extract_categories(html: str) -> list[dict[str, str]]:
    block = extract_gear_category_block(html)
    pairs = re.findall(r'<a href="([^"]+)"[^>]*class="p-2">([^<]+)</a>', block)
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for slug, label in pairs:
        slug = slug.strip()
        label = unescape(label).strip()
        if not slug or slug in seen or should_skip_category(slug):
            continue
        seen.add(slug)
        out.append({"slug": slug, "label": label})
    return out


# TLIDB 英文页「类型」列 → 与中文 JSON 一致的 affixType（与 Equipment.vue 逻辑对齐）
AFFIX_TYPE_EN_TO_ZH: dict[str, str] = {
    "base affix": "基础词缀",
    "sweet dream affix": "美梦词缀",
    "corrosion base": "侵蚀基底",
    "basic pre-fix": "初阶前缀",
    "advanced pre-fix": "进阶前缀",
    "ultimate pre-fix": "至臻前缀",
    "basic suffix": "初阶后缀",
    "advanced suffix": "进阶后缀",
    "ultimate suffix": "至臻后缀",
    # 若站点改为无前缀连字符的写法
    "basic prefix": "初阶前缀",
    "advanced prefix": "进阶前缀",
    "ultimate prefix": "至臻前缀",
}


def normalize_affix_type(kind: str) -> str:
    if not kind:
        return kind
    k = kind.strip()
    return AFFIX_TYPE_EN_TO_ZH.get(k.lower(), k)


def strip_inline_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<script[^>]*>.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def slice_affix_tab_html(page_html: str) -> str | None:
    """截取「词缀 / Affix」主 tab 的 HTML（至下一个顶层 tab-pane 的 id 分栏）。"""
    start = page_html.find('<div id="词缀"')
    if start < 0:
        start = page_html.find('<div id="Affix"')
    if start < 0:
        return None
    # 常见顺序：词缀 → Item → 传奇装备 …（英文站无中文 id）
    markers = [
        '<div id="Item"',
        '<div id="传奇装备"',
        '<div id="传奇装备已侵蚀"',
        '<div id="Legendary"',
    ]
    end = -1
    for m in markers:
        j = page_html.find(m, start + 20)
        if j >= 0 and (end < 0 or j < end):
            end = j
    if end < 0:
        end = len(page_html)
    return page_html[start:end]


def parse_affix_rows(affix_html: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for m in ROW_RE.finditer(affix_html):
        effect_cell, source_raw, kind_raw = m.group(1), m.group(2), m.group(3)
        if "data-modifier-id" not in effect_cell:
            continue

        source_cell = strip_inline_html(source_raw)
        kind_cell = normalize_affix_type(strip_inline_html(kind_raw))

        mid_m = MODIFIER_ID_RE.search(effect_cell)
        if not mid_m:
            continue
        modifier_id = mid_m.group(1)

        tt = TOOLTIP_RE.search(effect_cell)
        tier = int(tt.group(1)) if tt else None
        item_level = int(tt.group(2)) if tt else None
        weight = int(tt.group(3)) if tt else None

        value_spans = []
        for vm in TEXT_MOD_RE.finditer(effect_cell):
            raw = vm.group(1)
            raw = raw.replace("&ndash;", "–").replace("–", "–")
            value_spans.append(strip_inline_html(raw))

        rows.append(
            {
                "modifierId": modifier_id,
                "tier": tier,
                "itemLevel": item_level,
                "weight": weight,
                "affixType": kind_cell,
                "source": source_cell,
                "effectPlain": strip_inline_html(effect_cell),
                "valueSpans": value_spans,
            }
        )
    return rows


def build_tier_roll_index(rows: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    """
    按「去掉数值后的效果骨架」粗分组，便于查看同一词条不同 T 阶的数值。
    骨架：将 valueSpans 中的片段从 effectPlain 中依次替换为占位符后归一化空格。
    """
    groups: dict[str, list[dict[str, object]]] = {}

    def skeleton(plain: str, spans: list[str]) -> str:
        s = plain
        for sp in spans:
            if sp and sp in s:
                s = s.replace(sp, "{#}", 1)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    for r in rows:
        plain = str(r.get("effectPlain") or "")
        spans = r.get("valueSpans")
        if not isinstance(spans, list):
            spans = []
        sk = skeleton(plain, [str(x) for x in spans])
        groups.setdefault(sk, []).append(r)

    # 只保留至少 2 条的组（同一骨架下多档 tier / 数值）
    merged: dict[str, list[dict[str, object]]] = {}
    for k, lst in groups.items():
        if len(lst) >= 2:
            merged[k] = sorted(
                lst,
                key=lambda x: (
                    x.get("tier") is None,
                    x.get("tier") if x.get("tier") is not None else 999,
                    str(x.get("modifierId")),
                ),
            )
    return merged


def sync_one_category(slug: str, label: str) -> dict[str, object] | None:
    url = f"{BASE}/{quote(slug, safe='/-._~%')}"
    html = fetch_html(url)
    affix = slice_affix_tab_html(html)
    if not affix:
        return {
            "slug": slug,
            "label": label,
            "sourceUrl": url,
            "error": "no_affix_tab",
            "modifiers": [],
            "modifierCount": 0,
            "tierVariantGroups": [],
            "tierVariantGroupCount": 0,
        }
    rows = parse_affix_rows(affix)
    tier_groups = build_tier_roll_index(rows)
    return {
        "slug": slug,
        "label": label,
        "sourceUrl": url,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "modifierCount": len(rows),
        "modifiers": rows,
        "tierVariantGroups": [
            {
                "skeleton": sk,
                "rolls": [
                    {
                        "modifierId": x["modifierId"],
                        "tier": x["tier"],
                        "itemLevel": x["itemLevel"],
                        "weight": x["weight"],
                        "affixType": x["affixType"],
                        "valueSpans": x["valueSpans"],
                        "effectPlain": x["effectPlain"],
                    }
                    for x in grp
                ],
            }
            for sk, grp in sorted(tier_groups.items(), key=lambda kv: kv[0])
        ],
        "tierVariantGroupCount": len(tier_groups),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 TLIDB 自制/稀有装备词缀（按装备子类分文件）")
    parser.add_argument("--dry-run", action="store_true", help="只拉首页子类列表，不写文件")
    parser.add_argument("--only", metavar="SLUG", help="只抓取指定子类 slug")
    args = parser.parse_args()

    print(f"[index] {INDEX_URL}", flush=True)
    index_html = fetch_html(INDEX_URL)
    categories = extract_categories(index_html)
    if args.only:
        categories = [c for c in categories if c["slug"] == args.only]
        if not categories:
            print(f"[err] 未找到子类: {args.only}", flush=True)
            return 1

    print(f"[categories] {len(categories)}", flush=True)
    if args.dry_run:
        for c in categories:
            print(f"  {c['slug']}\t{c['label']}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index_entries: list[dict[str, object]] = []

    for i, cat in enumerate(categories):
        slug = cat["slug"]
        label = cat["label"]
        print(f"[{i + 1}/{len(categories)}] {slug} …", flush=True)
        try:
            payload = sync_one_category(slug, label)
        except Exception as e:
            print(f"  [warn] {e}", flush=True)
            time.sleep(REQUEST_DELAY_SEC)
            continue
        if not payload:
            time.sleep(REQUEST_DELAY_SEC)
            continue

        out_path = OUT_DIR / f"{slug}.json"
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"  [write] {out_path.name} count={payload.get('modifierCount')}",
            flush=True,
        )
        entry: dict[str, object] = {
            "slug": slug,
            "label": label,
            "file": f"craftedAffixes/{slug}.json",
            "modifierCount": payload.get("modifierCount", 0),
            "tierVariantGroupCount": payload.get("tierVariantGroupCount", 0),
        }
        if payload.get("error"):
            entry["error"] = payload["error"]
        index_entries.append(entry)
        time.sleep(REQUEST_DELAY_SEC)

    index_payload = {
        "kind": "craftedAffixIndex",
        "sourceIndexUrl": INDEX_URL,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categoryCount": len(index_entries),
        "categories": sorted(index_entries, key=lambda x: str(x["slug"])),
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[write] {OUT_DIR / 'index.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
