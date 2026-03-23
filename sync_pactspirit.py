#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Pactspirit 抓取契灵列表（名称、图标、稀有度类、标签行、词条 modifier 文本）。

输出：torchlight-builder/src/data/pactspirit.json
图标：torchlight-builder/public/assets/pactspirit（与暗金装备脚本逻辑一致）

用法（仓库根目录）：
  python sync_pactspirit.py
  python sync_pactspirit.py --dry-run
  python sync_pactspirit.py --cache-icons      # 完整同步并下载图标
  python sync_pactspirit.py --icons-only       # 只读 JSON：补下缺失图标并本地化 iconUrl
  python sync_pactspirit.py --finalize-local-icons  # 仅根据已有文件重写 iconUrl
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

PAGE_URL = "https://tlidb.com/cn/Pactspirit"
OUT_FILE = Path("torchlight-builder/src/data/pactspirit.json")
ICON_DIR = Path("torchlight-builder/public/assets/pactspirit")
ICON_PREFIX = "/assets/pactspirit"
DETAIL_BASE_URL = "https://tlidb.com"
REQUEST_DELAY_SEC = 0.25

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

# 列表卡片：图标 + 链接 + 名称 + 稀有度 class + 正文（至 flex-grow 闭合前）
CARD_RE = re.compile(
    r'<div class="d-flex border-top rounded">'
    r'<div class="flex-shrink-0">'
    r'<img src="([^"]+)"[^>]*>'
    r"</div>"
    r'<div class="flex-grow-1[^"]*">'
    r'<a[^>]*href="([^"]+)"[^>]*class="([^"]*)"[^>]*>([^<]+)</a>'
    r"(.*?)</div>\s*</div>\s*</div>",
    re.S,
)

MODIFIER_RE = re.compile(r'<div class="modifier">(.*?)</div>', re.S)
DETAIL_CARD_RE = re.compile(r'<div class="d-flex border rounded">(.*?)</div>\s*</div>', re.S)
TAIL_TIER_RE = re.compile(r"\s*(?:([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+)|([IVX]+)|(\d+))\s*$")
ROMAN_MAP = {
    "Ⅰ": 1,
    "Ⅱ": 2,
    "Ⅲ": 3,
    "Ⅳ": 4,
    "Ⅴ": 5,
    "Ⅵ": 6,
    "Ⅶ": 7,
    "Ⅷ": 8,
    "Ⅸ": 9,
    "Ⅹ": 10,
}
VALUE_TOKEN_RE = re.compile(r"([+\-])?\s*(\d+(?:\.\d+)?)\s*(%)?")


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


def rarity_label(rarity_class: str) -> str | None:
    return {
        "item_rarity2": "魔法",
        "item_rarity3": "稀有",
        "item_rarity100": "传奇",
    }.get(rarity_class)


def rarity_label_from_tag_lines(tag_lines: list[str]) -> str | None:
    """首行形如「攻击 稀有」「掉落 传奇」时取最后一词为稀有度，与列表展示一致（优于仅信 CSS class）。"""
    if not tag_lines:
        return None
    parts = tag_lines[0].strip().split()
    if not parts:
        return None
    tail = parts[-1]
    return tail if tail in ("魔法", "稀有", "传奇") else None


def parse_body(body: str) -> tuple[list[str], list[str]]:
    """返回 (标签行列表, 词条行列表)。"""
    parts = re.split(r'<div class="border-top">\s*', body, maxsplit=1)
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    tag_lines: list[str] = []
    for inner in re.findall(r"<div>(.*?)</div>", head, re.S):
        t = strip_inline_html(inner)
        if t:
            tag_lines.append(t)
    effect_lines = [strip_inline_html(x) for x in MODIFIER_RE.findall(tail)]
    return tag_lines, effect_lines


def parse_page(html: str) -> list[dict[str, object]]:
    seen: set[str] = set()
    items: list[dict[str, object]] = []
    for m in CARD_RE.finditer(html):
        icon_url, pid, rarity_class, raw_name, body = (
            m.group(1).strip(),
            m.group(2).strip(),
            m.group(3).strip(),
            m.group(4),
            m.group(5),
        )
        name = unescape(raw_name).strip()
        if not pid or not name or pid in seen:
            continue
        seen.add(pid)
        tag_lines, effect_lines = parse_body(body)
        rarity_label_val = rarity_label_from_tag_lines(tag_lines) or rarity_label(rarity_class)
        items.append(
            {
                "id": pid,
                "name": name,
                "detailPath": f"/cn/{pid}",
                "iconUrl": icon_url,
                "rarityClass": rarity_class,
                "rarityLabel": rarity_label_val,
                "tagLines": tag_lines,
                "effectLines": effect_lines,
            }
        )
    return items


def parse_effect_lines_from_detail_html(html: str) -> list[str]:
    """
    从详情页右侧技能卡片抓取数值行（通常在每张卡片第 2 行），用于补全列表页不完整词条。
    """
    lines: list[str] = []
    for block in DETAIL_CARD_RE.findall(html):
        # 卡片内一般是 <div>名称</div><div>数值描述</div><div>来源</div>
        inner = re.findall(r"<div>(.*?)</div>", block, re.S)
        if len(inner) < 2:
            continue
        effect = strip_inline_html(inner[1])
        if not effect or len(effect) < 3:
            continue
        lines.append(effect)
    # 去重并保持顺序
    dedup: list[str] = []
    seen: set[str] = set()
    for x in lines:
        if x in seen:
            continue
        seen.add(x)
        dedup.append(x)
    return dedup


def _roman_to_int(text: str) -> int | None:
    if not text:
        return None
    if all(ch in ROMAN_MAP for ch in text):
        return sum(ROMAN_MAP[ch] for ch in text)
    # 支持 ASCII 罗马数字（常见 I/II/III/IV/V）
    vals = {"I": 1, "V": 5, "X": 10}
    prev = total = 0
    for ch in reversed(text):
        if ch not in vals:
            return None
        cur = vals[ch]
        if cur < prev:
            total -= cur
        else:
            total += cur
            prev = cur
    return total if total > 0 else None


def split_effect_name_and_tier(name: str) -> tuple[str, int | None]:
    t = name.strip()
    m = TAIL_TIER_RE.search(t)
    if not m:
        return t, None
    raw = m.group(1) or m.group(2) or m.group(3)
    if not raw:
        return t, None
    tier: int | None = None
    if raw.isdigit():
        tier = int(raw)
    else:
        tier = _roman_to_int(raw)
    base = t[: m.start()].strip()
    return (base or t), tier


def effect_key_from_name(base_name: str) -> str:
    # 用于后续计算的稳定 key：移除空格，保留中文语义
    key = re.sub(r"\s+", "", base_name.strip())
    # TLIDB 同一词条存在命名差异：未定宿命槽位 与 命运槽位 视为同一 key
    if key == "未定宿命槽位":
        return "命运槽位"
    return key


def parse_value_parts(value_text: str) -> list[dict[str, object]]:
    """
    将 valueText 拆成可计算的数值片段：
    - operator: + / - / =（无显式符号时为 =）
    - valueNum: 数字（float）
    - valueUnit: % / flat
    """
    parts: list[dict[str, object]] = []
    for m in VALUE_TOKEN_RE.finditer(value_text):
        op = m.group(1) or "="
        num_raw = m.group(2)
        unit = "%" if m.group(3) else "flat"
        try:
            num = float(num_raw)
        except Exception:
            continue
        parts.append(
            {
                "operator": op,
                "valueNum": num,
                "valueUnit": unit,
            }
        )
    return parts


def parse_effect_entries_from_detail_html(html: str) -> list[dict[str, object]]:
    """
    解析详情页卡片为结构化词条：
    - name: 原始词条名（可能含 I/II）
    - baseName: 去档位后的词条名（如 攻击伤害）
    - tier: 档位（1/2/3...，无法识别则为 null）
    - effectKey: 计算用 key（基于 baseName）
    - valueText: 数值文本
    - sourceText: 来源文本（如 内环影响）
    """
    entries: list[dict[str, object]] = []
    for block in DETAIL_CARD_RE.findall(html):
        inner = re.findall(r"<div>(.*?)</div>", block, re.S)
        if len(inner) < 2:
            continue
        name = strip_inline_html(inner[0])
        value = strip_inline_html(inner[1])
        source = strip_inline_html(inner[2]) if len(inner) > 2 else ""
        if not name or not value:
            continue
        base_name, tier = split_effect_name_and_tier(name)
        value_parts = parse_value_parts(value)
        first_part = value_parts[0] if value_parts else None
        entries.append(
            {
                "name": name,
                "baseName": base_name,
                "tier": tier,
                "effectKey": effect_key_from_name(base_name),
                "valueText": value,
                "sourceText": source,
                # 便于前端和计算逻辑直接使用
                "operator": first_part["operator"] if first_part else None,
                "valueNum": first_part["valueNum"] if first_part else None,
                "valueUnit": first_part["valueUnit"] if first_part else None,
                "valueParts": value_parts,
            }
        )
    # 去重（同 key+tier+value）
    out: list[dict[str, object]] = []
    seen: set[tuple[str, int | None, str]] = set()
    for e in entries:
        k = (str(e["effectKey"]), e["tier"] if isinstance(e.get("tier"), int) else None, str(e["valueText"]))
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


def enrich_effect_lines_from_detail(items: list[dict[str, object]]) -> tuple[int, int]:
    """
    用详情页词条补全 effectLines：
    - 若原词条为空，直接写入详情词条
    - 若原词条全部无数字而详情含数字，则用详情覆盖
    - 其他情况做并集合并（原词条优先）
    """
    updated = failed = 0
    for i, it in enumerate(items):
        pid = str(it.get("id", "")).strip()
        if not pid:
            continue
        detail_path = str(it.get("detailPath") or f"/cn/{pid}")
        if not detail_path.startswith("/"):
            detail_path = f"/{detail_path}"
        url = f"{DETAIL_BASE_URL}{detail_path}"
        try:
            html = fetch_html(url, timeout_sec=20)
            detail_entries = parse_effect_entries_from_detail_html(html)
            detail_lines = parse_effect_lines_from_detail_html(html)
            if detail_entries:
                it["effectEntries"] = detail_entries
            if detail_lines:
                current = [str(x).strip() for x in (it.get("effectLines") or []) if str(x).strip()]
                cur_has_num = any(re.search(r"\d", x) for x in current)
                det_has_num = any(re.search(r"\d", x) for x in detail_lines)
                if not current:
                    it["effectLines"] = detail_lines
                    updated += 1
                elif (not cur_has_num) and det_has_num:
                    it["effectLines"] = detail_lines
                    updated += 1
                else:
                    merged = current + [x for x in detail_lines if x not in set(current)]
                    if merged != current:
                        it["effectLines"] = merged
                        updated += 1
        except Exception:
            failed += 1
        if (i + 1) % 20 == 0:
            print(f"[enrich-detail-effects] progress={i + 1}/{len(items)}", flush=True)
        if i < len(items) - 1:
            time.sleep(REQUEST_DELAY_SEC)
    return updated, failed


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
        if local.exists():
            skipped += 1
        else:
            try:
                download_icon(remote, local)
                downloaded += 1
            except Exception:
                failed += 1
        if local.exists():
            it["localIconUrl"] = f"{ICON_PREFIX}/{fname}"
    return downloaded, skipped, failed


def finalize_local_icons(items: list[dict[str, object]]) -> None:
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


def merge_localized_icons_from_previous(
    merged: list[dict[str, object]], prev_path: Path
) -> None:
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


def main() -> int:
    parser = argparse.ArgumentParser(description="同步 TLIDB 契灵列表")
    parser.add_argument("--dry-run", action="store_true", help="只抓取并打印数量，不写文件")
    parser.add_argument(
        "--cache-icons",
        action="store_true",
        help="下载图标到 public/assets/pactspirit",
    )
    parser.add_argument(
        "--icons-only",
        action="store_true",
        help="不抓取页面：读取 JSON，补下缺失图标并本地化 iconUrl",
    )
    parser.add_argument(
        "--finalize-local-icons",
        action="store_true",
        help="仅根据磁盘已有图标重写 iconUrl（CDN 迁至 cdnIconUrl）",
    )
    parser.add_argument(
        "--skip-detail-effects",
        action="store_true",
        help="跳过详情页词条补全（默认会补全以获得更完整数值）",
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

    print(f"[fetch] {PAGE_URL}", flush=True)
    html = fetch_html(PAGE_URL)
    items = parse_page(html)
    print(f"[parsed] unique items={len(items)}", flush=True)
    if args.dry_run:
        return 0

    if not args.skip_detail_effects and items:
        u, f = enrich_effect_lines_from_detail(items)
        print(f"[enrich-detail-effects] updated={u} failed={f}", flush=True)

    merge_localized_icons_from_previous(items, OUT_FILE)

    if args.cache_icons and items:
        d, s, f = cache_icons(items)
        print(f"[icons] downloaded={d} skipped={s} failed={f}", flush=True)

    ensure_local_icon_urls(items)
    finalize_local_icons(items)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "pactspiritIndex",
        "sourceUrl": PAGE_URL,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "itemCount": len(items),
        "items": items,
    }
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[write] {OUT_FILE}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
