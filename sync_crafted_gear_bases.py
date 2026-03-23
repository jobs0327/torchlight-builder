#!/usr/bin/env python3
"""
从 TLIDB 各装备子类页的「Item」分栏抓取打造用基底装备（白字底子），与词缀页同源子类 slug。

示例：https://tlidb.com/cn/STR_Helmet#Item 中 Item /12 卡片内的基底列表（图标、href、中文名、需求等级）。

输出目录：
  torchlight-builder/src/data/equipment/craftedGearBases/<slug>.json
  以及 index.json

用法（仓库根目录）：
  python sync_crafted_gear_bases.py
  python sync_crafted_gear_bases.py --dry-run
  python sync_crafted_gear_bases.py --only STR_Helmet
  python sync_crafted_gear_bases.py --cache-icons   # 与完整抓取同时进行：下载图标并写入本地路径
  python sync_crafted_gear_bases.py --icons-only    # 仅根据已有 JSON 下载图标并更新 iconUrl（不抓网页）
  python sync_crafted_gear_bases.py --attach-local-icons  # 不联网：磁盘已有图标则写入 JSON
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen

BASE = "https://tlidb.com/cn"
INDEX_URL = f"{BASE}/Legendary_Gear"
OUT_DIR = Path("torchlight-builder/src/data/equipment/craftedGearBases")
ICON_DIR = Path("torchlight-builder/public/assets/equipment/crafted-bases")
ICON_PREFIX = "/assets/equipment/crafted-bases"
REQUEST_DELAY_SEC = 0.85

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SKIP_CATEGORY_EXACT = frozenset(
    {"Hero_Memories", "Divinity_Slate", "Destiny", "Ethereal_Prism"}
)

# 基底行：图标无 <a> 包裹，与暗金列表 DOM 不同
BASE_ITEM_ROW_RE = re.compile(
    r'<div class="d-flex border-top rounded"><div class="flex-shrink-0">\s*'
    r'<img\s+src="([^"]+)"[^>]*alt="([^"]+)"[^>]*/?>\s*</div>\s*'
    r'<div class="flex-grow-1[^"]*"><a[^>]*href="([^"]+)">([^<]+)</a>\s*'
    r'<div>([^<]*)</div>',
    re.S | re.I,
)

REQ_LEVEL_RE = re.compile(r"需求等级\s*(\d+)")


def safe_filename(raw: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
    return normalized or "base_icon"


def download_icon(url: str, output: Path) -> None:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://tlidb.com/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        },
    )
    with urlopen(req, timeout=45) as resp:
        output.write_bytes(resp.read())


def remote_url_for_base_icon(it: dict[str, object]) -> str:
    cdn = str(it.get("cdnIconUrl") or "").strip()
    if cdn.startswith("http"):
        return cdn
    u = str(it.get("iconUrl") or "").strip()
    return u if u.startswith("http") else ""


def localize_bases_icons(bases: list[dict[str, object]]) -> tuple[int, int, int]:
    """下载远程图标到 public，并把 iconUrl 改为 /assets/...，原链写入 cdnIconUrl。"""
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = skipped = failed = 0
    for it in bases:
        bid = str(it.get("id", "")).strip()
        remote = remote_url_for_base_icon(it)
        if not bid or not remote:
            continue
        ext = Path(urlparse(remote).path).suffix or ".webp"
        fname = f"{safe_filename(bid)}{ext}"
        local = ICON_DIR / fname
        public = f"{ICON_PREFIX}/{fname}"
        if local.exists():
            skipped += 1
        else:
            try:
                download_icon(remote, local)
                downloaded += 1
            except Exception:
                failed += 1
        if local.exists():
            cur = str(it.get("iconUrl", "")).strip()
            if cur.startswith("http") and not str(it.get("cdnIconUrl") or "").startswith("http"):
                it["cdnIconUrl"] = cur
            it["iconUrl"] = public
    return downloaded, skipped, failed


def attach_local_icons_to_bases(bases: list[dict[str, object]]) -> int:
    """public 目录已有与基底 id 对应的文件时，写入本地 iconUrl。"""
    if not ICON_DIR.is_dir():
        return 0
    known = {p.name for p in ICON_DIR.iterdir() if p.is_file()}
    updated = 0
    for it in bases:
        bid = str(it.get("id", "")).strip()
        if not bid:
            continue
        base = safe_filename(bid)
        hit: str | None = None
        for ext in (".webp", ".png", ".jpg", ".jpeg"):
            fname = f"{base}{ext}"
            if fname in known:
                hit = fname
                break
        if not hit:
            continue
        cur = str(it.get("iconUrl", "")).strip()
        if cur.startswith("http") and not str(it.get("cdnIconUrl") or "").startswith("http"):
            it["cdnIconUrl"] = cur
        it["iconUrl"] = f"{ICON_PREFIX}/{hit}"
        updated += 1
    return updated


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


def slice_item_tab_html(page_html: str) -> str | None:
    start = page_html.find('<div id="Item"')
    if start < 0:
        return None
    markers = [
        '<div id="传奇装备"',
        '<div id="传奇装备已侵蚀"',
    ]
    end = -1
    for m in markers:
        j = page_html.find(m, start + 20)
        if j >= 0 and (end < 0 or j < end):
            end = j
    if end < 0:
        end = len(page_html)
    return page_html[start:end]


def strip_inline_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<script[^>]*>.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_slot_kind_after_row(row_end: int, item_html: str) -> str | None:
    """取该基底卡片后续片段中最后一个短纯文本 div，一般为「头部」「单手」等。"""
    tail = item_html[row_end : row_end + 900]
    texts = [strip_inline_html(x) for x in re.findall(r"<div>([^<]*)</div>", tail)]
    for t in reversed(texts):
        if not t or len(t) > 16:
            continue
        if "需求" in t or re.search(r"\d", t):
            continue
        return t
    return None


def parse_base_items(item_html: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for m in BASE_ITEM_ROW_RE.finditer(item_html):
        icon_url = m.group(1).strip()
        icon_alt = unescape(m.group(2).strip())
        href_raw = m.group(3).strip()
        name = unescape(m.group(4).strip())
        req_raw = m.group(5)
        item_id = unquote(href_raw)
        if not item_id or not name:
            continue

        req_m = REQ_LEVEL_RE.search(req_raw)
        if not req_m:
            num_m = re.search(r"(\d+)", strip_inline_html(req_raw))
            req_level = int(num_m.group(1)) if num_m else None
        else:
            req_level = int(req_m.group(1))

        slot_kind = parse_slot_kind_after_row(m.end(), item_html)

        rows.append(
            {
                "id": item_id,
                "name": name,
                "iconUrl": icon_url,
                "iconAlt": icon_alt,
                "requiredLevel": req_level,
                **({"slotKind": slot_kind} if slot_kind else {}),
            }
        )
    return rows


def sync_one_category(slug: str, label: str) -> dict[str, object]:
    url = f"{BASE}/{quote(slug, safe='/-._~%')}"
    html = fetch_html(url)
    tab = slice_item_tab_html(html)
    bases: list[dict[str, object]] = []
    err: str | None = None
    if not tab:
        err = "no_item_tab"
    else:
        bases = parse_base_items(tab)

    return {
        "kind": "craftedGearBases",
        "categorySlug": slug,
        "categoryLabel": label,
        "sourceUrl": url,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "baseCount": len(bases),
        "bases": bases,
        **({"error": err} if err else {}),
    }


def icons_only_main() -> int:
    """扫描已有 JSON，下载图标并回写 iconUrl。"""
    if not OUT_DIR.is_dir():
        print(f"[err] 缺少目录 {OUT_DIR}", flush=True)
        return 1
    total_d = total_s = total_f = 0
    files = sorted(p for p in OUT_DIR.glob("*.json") if p.name != "index.json")
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[warn] 跳过 {path.name}: {e}", flush=True)
            continue
        bases = payload.get("bases")
        if not isinstance(bases, list):
            continue
        dict_bases = [x for x in bases if isinstance(x, dict)]
        d, s, f = localize_bases_icons(dict_bases)
        total_d += d
        total_s += s
        total_f += f
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[icons] {path.name} downloaded={d} skipped={s} failed={f}", flush=True)
    print(
        f"[icons] total downloaded={total_d} skipped={total_s} failed={total_f}",
        flush=True,
    )
    return 1 if total_f > 0 else 0


def attach_local_icons_main() -> int:
    if not OUT_DIR.is_dir():
        print(f"[err] 缺少目录 {OUT_DIR}", flush=True)
        return 1
    n = 0
    for path in sorted(p for p in OUT_DIR.glob("*.json") if p.name != "index.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        bases = payload.get("bases")
        if not isinstance(bases, list):
            continue
        dict_bases = [x for x in bases if isinstance(x, dict)]
        n += attach_local_icons_to_bases(dict_bases)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"[attach] 已根据磁盘更新 {n} 条 iconUrl", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 TLIDB 打造基底装备（Item 分栏）")
    parser.add_argument("--dry-run", action="store_true", help="只拉首页子类列表，不写文件")
    parser.add_argument("--only", metavar="SLUG", help="只抓取指定子类 slug")
    parser.add_argument(
        "--cache-icons",
        action="store_true",
        help="抓取每个子类后下载基底图标到 public 并本地化 JSON 中的 iconUrl",
    )
    parser.add_argument(
        "--icons-only",
        action="store_true",
        help="不抓网页：仅根据现有 JSON 下载图标并更新文件",
    )
    parser.add_argument(
        "--attach-local-icons",
        action="store_true",
        help="不联网：若 public 已有图标文件则写入 JSON",
    )
    args = parser.parse_args()

    if args.icons_only:
        return icons_only_main()
    if args.attach_local_icons:
        return attach_local_icons_main()

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

        if args.cache_icons:
            bases = payload.get("bases")
            if isinstance(bases, list):
                dict_bases = [x for x in bases if isinstance(x, dict)]
                d, s, f = localize_bases_icons(dict_bases)
                print(f"  [icons] downloaded={d} skipped={s} failed={f}", flush=True)

        out_path = OUT_DIR / f"{slug}.json"
        out_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"  [write] {out_path.name} bases={payload.get('baseCount')}", flush=True)
        index_entries.append(
            {
                "slug": slug,
                "label": label,
                "file": f"craftedGearBases/{slug}.json",
                "baseCount": payload.get("baseCount", 0),
                **({"error": payload["error"]} if payload.get("error") else {}),
            }
        )
        time.sleep(REQUEST_DELAY_SEC)

    index_payload = {
        "kind": "craftedGearBasesIndex",
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
