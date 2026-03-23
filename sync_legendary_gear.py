#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Legendary_Gear 抓取「暗金 / 传奇装备」分类与列表。

逻辑：
1. 拉取 Legendary_Gear 首页，解析 Gear 卡片内带 class="p-2" 的子类链接（力量头盔、单手剑等）。
2. 排除赛季入口、神格石板、星图等非装备子类。
3. 逐个请求 https://tlidb.com/cn/{子类 slug}，用与技能页相同的列表 DOM 正则解析：id、中文名、图标、需求等级。

用法（仓库根目录）：
  python sync_legendary_gear.py
  python sync_legendary_gear.py --dry-run          # 只拉首页并打印子类数量
  python sync_legendary_gear.py --only STR_Helmet  # 只同步单个子类（调试）
  python sync_legendary_gear.py --cache-icons      # 与完整同步一起：下载图标到 public/assets/equipment/legendary
  python sync_legendary_gear.py --icons-only       # 不抓网页：下载缺失图标并本地化 iconUrl（CDN 写入 cdnIconUrl）
  python sync_legendary_gear.py --attach-local-icons # 不联网：扫描 public 图标并本地化 iconUrl
  python sync_legendary_gear.py --finalize-local-icons # 仅根据磁盘 + JSON 重写 iconUrl 为本地路径
  python sync_legendary_gear.py --enrich-effects   # 按装备 id 抓取详情页，写入 effectLines（词条文本，取当前赛季首卡）
  python sync_legendary_gear.py --enrich-effects --enrich-force  # 覆盖已有 effectLines
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

BASE = "https://tlidb.com/cn"
INDEX_URL = f"{BASE}/Legendary_Gear"
OUT_FILE = Path("torchlight-builder/src/data/equipment/legendaryGear.json")
ICON_DIR = Path("torchlight-builder/public/assets/equipment/legendary")
ICON_PREFIX = "/assets/equipment/legendary"

REQUEST_DELAY_SEC = 0.85
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SKIP_CATEGORY_EXACT = frozenset(
    {"Hero_Memories", "Divinity_Slate", "Destiny", "Ethereal_Prism"}
)

ITEM_ROW_RE = re.compile(
    r'<div class="d-flex border-top rounded"><div class="flex-shrink-0">'
    r'<a href="([^"]+)"><img src="([^"]+)"[^>]*></a></div>'
    r'<div class="flex-grow-1[^"]*"><a[^>]*href="([^"]+)">([^<]+)</a><br/>([^<]*)',
    re.S,
)

REQ_LEVEL_RE = re.compile(r"需求等级\s*(\d+)")


def fetch_html(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        },
    )
    with urlopen(req, timeout=60) as resp:
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


def parse_items_from_category_page(html: str, category: dict[str, str]) -> list[dict[str, object]]:
    """子类页常含两套 tab（在线 / 缓存），同一条目会出现两次，按 id 去重保留首次。"""
    items: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for href_icon, icon_url, href_name, raw_name, after_br in ITEM_ROW_RE.findall(html):
        item_id = href_icon.strip()
        if not item_id or item_id != href_name.strip() or item_id in seen_ids:
            continue
        name = unescape(raw_name).strip()
        if not name:
            continue
        seen_ids.add(item_id)
        m = REQ_LEVEL_RE.search(after_br)
        req_level: int | None = int(m.group(1)) if m else None
        items.append(
            {
                "id": item_id,
                "name": name,
                "iconUrl": icon_url.strip(),
                "requiredLevel": req_level,
                "category": {"slug": category["slug"], "label": category["label"]},
            }
        )
    return items


def safe_filename(raw: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", raw).strip("_")
    return normalized or "item_icon"


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


def icon_remote_download_url(it: dict[str, object]) -> str:
    """优先使用 cdnIconUrl（iconUrl 已本地化后），否则使用 http(s) 的 iconUrl。"""
    cdn = str(it.get("cdnIconUrl") or "").strip()
    if cdn.startswith("http"):
        return cdn
    u = str(it.get("iconUrl") or "").strip()
    return u if u.startswith("http") else ""


def cache_icons(items: list[dict[str, object]]) -> tuple[int, int, int]:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = skipped = failed = 0
    for it in items:
        iid = str(it.get("id", "")).strip()
        remote = icon_remote_download_url(it)
        if not iid or not remote:
            continue
        ext = Path(urlparse(remote).path).suffix or ".webp"
        fname = f"{safe_filename(iid)}{ext}"
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
            it["localIconUrl"] = public
    return downloaded, skipped, failed


def finalize_local_icons(items: list[dict[str, object]]) -> None:
    """将 iconUrl 改为本地 public 路径，原 CDN 写入 cdnIconUrl，并删除 localIconUrl。"""
    known: set[str] = set()
    if ICON_DIR.is_dir():
        known = {p.name for p in ICON_DIR.iterdir() if p.is_file()}
    for it in items:
        iid = str(it.get("id", "")).strip()
        if not iid:
            continue
        public: str | None = None
        loc = it.get("localIconUrl")
        if isinstance(loc, str) and loc.strip().startswith("/"):
            public = loc.strip()
        if not public:
            base = safe_filename(iid)
            for ext in (".webp", ".png", ".jpg", ".jpeg"):
                fname = f"{base}{ext}"
                if fname in known:
                    public = f"{ICON_PREFIX}/{fname}"
                    break
        if not public:
            continue
        cur = str(it.get("iconUrl", "")).strip()
        if cur.startswith("http") and not it.get("cdnIconUrl"):
            it["cdnIconUrl"] = cur
        it["iconUrl"] = public
        it.pop("localIconUrl", None)


def ensure_local_icon_urls(items: list[dict[str, object]]) -> None:
    """若 public 目录已有对应文件，则写入 localIconUrl（无需 --cache-icons 也能保留本地化路径）。"""
    if not ICON_DIR.is_dir():
        return
    known = {p.name for p in ICON_DIR.iterdir() if p.is_file()}
    for it in items:
        if it.get("localIconUrl"):
            continue
        iid = str(it.get("id", "")).strip()
        if not iid:
            continue
        base = safe_filename(iid)
        for ext in (".webp", ".png", ".jpg", ".jpeg"):
            fname = f"{base}{ext}"
            if fname in known:
                it["localIconUrl"] = f"{ICON_PREFIX}/{fname}"
                break


def strip_inline_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<script[^>]*>.*?</script>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def slice_first_popup_item_card(html: str) -> str | None:
    """详情页首列「当前赛季」popupItem 卡片 HTML（不含 SS10 previousItem）。"""
    marker = '<div class="card ui_item popupItem">'
    start = html.find(marker)
    if start < 0:
        return None
    prev = html.find('<div class="card ui_item popupItem previousItem">', start + 20)
    if prev > start:
        return html[start:prev]
    info = html.find(
        '<div class="card ui_item">\n    <div class="card-header"',
        start + len(marker) + 20,
    )
    if info > start:
        return html[start:info]
    return html[start : start + 15000]


def parse_item_effect_lines_from_page(html: str) -> list[str]:
    """从详情页 HTML 解析基础属性 + 传奇词条（t1…）+ 风味描述。"""
    card = slice_first_popup_item_card(html)
    if not card:
        return []
    lines: list[str] = []
    i = card.find('data-block="attrs2"')
    if i >= 0:
        sub = card[i:]
        hrp = sub.find('<hr class="my-1"/>')
        if hrp < 0:
            hrp = sub.find("<hr ")
        block = sub[:hrp] if hrp > 0 else sub[:800]
        gt = block.find(">")
        inner = block[gt + 1 :].strip()
        if re.search(r"<br\s*/?>", inner, re.I) and inner.count("<div") <= 2:
            for seg in re.split(r"<br\s*/?>", inner, flags=re.I):
                t = strip_inline_html(seg)
                if t:
                    lines.append(t)
        else:
            for m in re.finditer(r"<div[^>]*>(.*?)</div>", inner, re.S):
                t = strip_inline_html(m.group(1))
                if t:
                    lines.append(t)
    for m in re.finditer(r'<div class="t[0-9]">\s*(.*?)\s*</div>', card, re.S):
        t = strip_inline_html(m.group(1))
        if t:
            lines.append(t)
    fm = re.search(r'class="fst-italic"[^>]*>([^<]+)</div>', card)
    if fm:
        fl = strip_inline_html(fm.group(1))
        if fl:
            lines.append(f"「{fl}」")
    return lines


def merge_effect_lines_from_previous(
    merged: list[dict[str, object]], prev_path: Path
) -> None:
    """完整同步后保留旧 JSON 里已抓取的词条。"""
    if not prev_path.is_file():
        return
    try:
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
        prev_items = prev.get("items")
        if not isinstance(prev_items, list):
            return
        by_id = {str(x.get("id", "")): x for x in prev_items if isinstance(x, dict)}
        for it in merged:
            iid = str(it.get("id", ""))
            if it.get("effectLines"):
                continue
            old = by_id.get(iid)
            if old and isinstance(old.get("effectLines"), list) and old["effectLines"]:
                it["effectLines"] = old["effectLines"]
    except Exception:
        pass


def merge_localized_icons_from_previous(
    merged: list[dict[str, object]], prev_path: Path
) -> None:
    """完整同步后保留旧 JSON 里已本地化的 iconUrl / cdnIconUrl。"""
    if not prev_path.is_file():
        return
    try:
        prev = json.loads(prev_path.read_text(encoding="utf-8"))
        prev_items = prev.get("items")
        if not isinstance(prev_items, list):
            return
        by_id = {str(x.get("id", "")): x for x in prev_items if isinstance(x, dict)}
        for it in merged:
            iid = str(it.get("id", ""))
            old = by_id.get(iid)
            if not old:
                continue
            oicon = str(old.get("iconUrl", "")).strip()
            cur = str(it.get("iconUrl", "")).strip()
            if oicon.startswith("/"):
                it["iconUrl"] = oicon
                if old.get("cdnIconUrl"):
                    it["cdnIconUrl"] = old["cdnIconUrl"]
                elif cur.startswith("http"):
                    it["cdnIconUrl"] = cur
    except Exception:
        pass


def enrich_items_effect_lines(
    items: list[dict[str, object]],
    *,
    force: bool,
    limit: int | None,
    delay_sec: float,
) -> tuple[int, int, int]:
    """抓取每件装备详情页，写入 effectLines。"""
    updated = skipped = failed = 0
    for idx, it in enumerate(items):
        if limit is not None and idx >= limit:
            break
        iid = str(it.get("id", "")).strip()
        if not iid:
            continue
        if not force and isinstance(it.get("effectLines"), list) and it["effectLines"]:
            skipped += 1
            continue
        url = f"{BASE}/{iid}"
        try:
            page = fetch_html(url)
            lines = parse_item_effect_lines_from_page(page)
        except Exception:
            failed += 1
            time.sleep(delay_sec)
            continue
        if lines:
            it["effectLines"] = lines
            updated += 1
        else:
            failed += 1
        time.sleep(delay_sec)
    return updated, skipped, failed


def merge_items_by_id(
    all_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], int]:
    """同一 id 若出现在多分类（极少见）则合并 categories 列表。"""
    by_id: dict[str, dict[str, object]] = {}
    dup = 0
    for row in all_rows:
        iid = str(row["id"])
        cat = row["category"]
        assert isinstance(cat, dict)
        if iid not in by_id:
            entry: dict[str, object] = {
                "id": iid,
                "name": row["name"],
                "iconUrl": row["iconUrl"],
                "requiredLevel": row.get("requiredLevel"),
                "categories": [cat],
            }
            if row.get("effectLines"):
                entry["effectLines"] = row["effectLines"]
            by_id[iid] = entry
            continue
        dup += 1
        existing = by_id[iid]
        cats = existing.setdefault("categories", [])
        if not any(c.get("slug") == cat.get("slug") for c in cats):
            cats.append(cat)
        if not existing.get("effectLines") and row.get("effectLines"):
            existing["effectLines"] = row["effectLines"]
        row_icon = str(row.get("iconUrl", "")).strip()
        ex_icon = str(existing.get("iconUrl", "")).strip()
        if ex_icon.startswith("/") and row_icon.startswith("http"):
            if not existing.get("cdnIconUrl"):
                existing["cdnIconUrl"] = row_icon
        elif not ex_icon.startswith("/"):
            existing["iconUrl"] = row["iconUrl"]
    return list(by_id.values()), dup


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 tlidb 传奇（暗金）装备数据")
    parser.add_argument("--dry-run", action="store_true", help="只解析首页子类，不写文件")
    parser.add_argument(
        "--only",
        metavar="SLUG",
        help="只抓取指定子类 slug（如 STR_Helmet）",
    )
    parser.add_argument(
        "--cache-icons",
        action="store_true",
        help="下载图标到 public/assets/equipment/legendary",
    )
    parser.add_argument(
        "--icons-only",
        action="store_true",
        help="不抓取 tlidb 页面：只读取已生成的 JSON，按 iconUrl 拉取图标并更新 localIconUrl",
    )
    parser.add_argument(
        "--attach-local-icons",
        action="store_true",
        help="不联网：扫描 public 下已下载的图标，为对应装备写入 localIconUrl",
    )
    parser.add_argument(
        "--enrich-effects",
        action="store_true",
        help="读取 JSON，逐件请求详情页并写入 effectLines（词条）",
    )
    parser.add_argument(
        "--enrich-force",
        action="store_true",
        help="与 --enrich-effects 合用：覆盖已有 effectLines",
    )
    parser.add_argument(
        "--enrich-limit",
        type=int,
        default=0,
        metavar="N",
        help="仅处理前 N 件（0 表示全部）",
    )
    parser.add_argument(
        "--finalize-local-icons",
        action="store_true",
        help="读取 JSON：将已有本地文件的图标写入 iconUrl（/assets/...），CDN 迁至 cdnIconUrl，去掉 localIconUrl",
    )
    args = parser.parse_args()

    if args.finalize_local_icons:
        if not OUT_FILE.is_file():
            print(f"[error] 缺少 {OUT_FILE}", flush=True)
            return 1
        payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            print("[error] JSON 中 items 无效", flush=True)
            return 1
        fin: list[dict[str, object]] = [dict(x) for x in raw_items if isinstance(x, dict)]
        ensure_local_icon_urls(fin)
        finalize_local_icons(fin)
        n_local = sum(1 for x in fin if str(x.get("iconUrl", "")).strip().startswith("/"))
        payload["items"] = fin
        OUT_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(
            f"[write] {OUT_FILE} (--finalize-local-icons, {n_local}/{len(fin)} 条 iconUrl 为本地路径)",
            flush=True,
        )
        return 0

    if args.enrich_effects:
        if not OUT_FILE.is_file():
            print(f"[error] 缺少 {OUT_FILE}", flush=True)
            return 1
        payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            print("[error] JSON 中 items 无效", flush=True)
            return 1
        items_enrich: list[dict[str, object]] = [dict(x) for x in raw_items if isinstance(x, dict)]
        lim = args.enrich_limit if args.enrich_limit > 0 else None
        u, s, f = enrich_items_effect_lines(
            items_enrich,
            force=args.enrich_force,
            limit=lim,
            delay_sec=REQUEST_DELAY_SEC,
        )
        print(f"[enrich-effects] updated={u} skipped={s} failed={f}", flush=True)
        ensure_local_icon_urls(items_enrich)
        finalize_local_icons(items_enrich)
        payload["items"] = items_enrich
        payload["effectsEnrichedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        OUT_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[write] {OUT_FILE} (--enrich-effects)", flush=True)
        return 0

    if args.attach_local_icons:
        if not OUT_FILE.is_file():
            print(f"[error] 缺少 {OUT_FILE}，请先执行完整同步", flush=True)
            return 1
        payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            print("[error] JSON 中 items 无效", flush=True)
            return 1
        merged_attach: list[dict[str, object]] = [dict(x) for x in raw_items if isinstance(x, dict)]
        ensure_local_icon_urls(merged_attach)
        finalize_local_icons(merged_attach)
        n = sum(1 for x in merged_attach if str(x.get("iconUrl", "")).strip().startswith("/"))
        payload["items"] = merged_attach
        OUT_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[write] {OUT_FILE} (--attach-local-icons, {n}/{len(merged_attach)} 条 iconUrl 已本地化)", flush=True)
        return 0

    if args.icons_only:
        if not OUT_FILE.is_file():
            print(f"[error] 缺少 {OUT_FILE}，请先执行完整同步", flush=True)
            return 1
        payload = json.loads(OUT_FILE.read_text(encoding="utf-8"))
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            print("[error] JSON 中 items 无效", flush=True)
            return 1
        merged_icons: list[dict[str, object]] = [dict(x) for x in raw_items if isinstance(x, dict)]
        d, s, f = cache_icons(merged_icons)
        print(f"[icons] downloaded={d} skipped={s} failed={f}", flush=True)
        ensure_local_icon_urls(merged_icons)
        finalize_local_icons(merged_icons)
        payload["items"] = merged_icons
        OUT_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[write] {OUT_FILE} (--icons-only)", flush=True)
        return 0

    print(f"[fetch] {INDEX_URL}", flush=True)
    index_html = fetch_html(INDEX_URL)
    categories = extract_categories(index_html)
    print(
        f"[info] 装备子类: {len(categories)} 个（已过滤赛季/神格/星图等）",
        flush=True,
    )

    if args.dry_run:
        for c in categories:
            print(f"  - {c['slug']}: {c['label']}", flush=True)
        return 0

    if args.only:
        slug = args.only.strip()
        categories = [c for c in categories if c["slug"] == slug]
        if not categories:
            print(f"[error] 未找到子类: {slug}", flush=True)
            return 1

    all_items: list[dict[str, object]] = []
    per_cat_counts: list[dict[str, object]] = []

    for i, cat in enumerate(categories):
        slug = cat["slug"]
        url = f"{BASE}/{quote(slug, safe='/-._~%')}"
        print(f"[{i + 1}/{len(categories)}] {slug} …", flush=True)
        try:
            sub_html = fetch_html(url)
        except Exception as e:
            print(f"  [warn] 失败: {e}", flush=True)
            per_cat_counts.append({**cat, "itemCount": 0, "error": str(e)})
            time.sleep(REQUEST_DELAY_SEC)
            continue
        rows = parse_items_from_category_page(sub_html, cat)
        all_items.extend(rows)
        per_cat_counts.append({**cat, "itemCount": len(rows)})
        time.sleep(REQUEST_DELAY_SEC)

    merged, merge_dup = merge_items_by_id(all_items)
    merged.sort(key=lambda x: (x.get("requiredLevel") is None, x.get("requiredLevel") or 0, x["name"]))
    merge_localized_icons_from_previous(merged, OUT_FILE)

    payload: dict[str, object] = {
        "kind": "legendary",
        "sourceUrl": INDEX_URL,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "categoryCount": len(categories),
        "rawRowCount": len(all_items),
        "itemCount": len(merged),
        "mergedDuplicateRows": merge_dup,
        "categories": per_cat_counts,
        "items": merged,
    }

    if args.cache_icons and merged:
        d, s, f = cache_icons(merged)
        print(f"[icons] downloaded={d} skipped={s} failed={f}", flush=True)

    ensure_local_icon_urls(merged)
    finalize_local_icons(merged)
    merge_effect_lines_from_previous(merged, OUT_FILE)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[write] {OUT_FILE} ({len(merged)} items)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
