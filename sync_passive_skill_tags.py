#!/usr/bin/env python3
"""
从 https://tlidb.com/cn/Passive_Skill 抓取被动技能标签与技能列表，
写入 torchlight-builder/src/data/skills/passiveSkillTags.json
（含 growthDescriptionByLevel / parsedBonusesByLevel；不再写入 supportDamageBonusByLevel），
并缓存图标到 public/assets/skills/passive/。

用法：在仓库根目录执行
  python sync_passive_skill_tags.py
  python sync_passive_skill_tags.py --skip-icons   # 仅更新 JSON，不下载图标（更快）
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

SOURCE_URL = "https://tlidb.com/cn/Passive_Skill"
OUT_FILE = Path("torchlight-builder/src/data/skills/passiveSkillTags.json")
ICON_CACHE_DIR = Path("torchlight-builder/public/assets/skills/passive")
ICON_PUBLIC_PREFIX = "/assets/skills/passive"


def strip_html(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"<[^>]*>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_passive_skill_tags(html: str) -> list[str]:
    plain_text = strip_html(html)
    matches = re.findall(r"被动技能 Tag /\d+\s+(.+?)\s+Reset", plain_text)
    if not matches:
        raise RuntimeError("页面中未找到「被动技能 Tag」区块")

    content = matches[-1].strip()
    if not content:
        raise RuntimeError("标签区块为空，未提取到标签")

    excluded = {"技能等级", "技能", "帮助手册", "主动技能", "被动技能"}
    tokens = content.split()

    seen: set[str] = set()
    tags: list[str] = []
    for token in tokens:
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


def extract_passive_skills(html: str, allowed_tags: set[str]) -> list[dict[str, object]]:
    pattern = re.compile(
        r'<div class="d-flex border-top rounded">.*?'
        r'<a[^>]*data-hover="([^"]+)"[^>]*href="([^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*>\s*</a>.*?'
        r'<a[^>]*href="[^"]+"[^>]*>\s*([^<]+?)\s*</a>\s*'
        r'<div>\s*((?:<span[^>]*>[^<]+</span>\s*,?\s*)+)</div>.*?</div>\s*</div>',
        re.S,
    )
    tag_pattern = re.compile(r"<span[^>]*>([^<]+)</span>")

    skills: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for hover_url, href, icon_url, raw_name, tags_html in pattern.findall(html):
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
        skills.append(
            {
                "id": skill_id,
                "name": name,
                "iconUrl": icon_url.strip(),
                "tags": tags,
                "hoverUrl": hover_url.strip(),
            }
        )

    return skills


def fetch_text(url: str, *, referer: str | None = None) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            **({"Referer": referer} if referer else {}),
        },
    )
    with urlopen(req, timeout=30) as resp:
        raw = resp.read()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("gb18030", errors="ignore")


def skill_page_url(skill_id: str) -> str:
    return f"https://tlidb.com/cn/{quote(skill_id, safe='-._~%')}"


def parse_growth_rows_from_skill_page(page_html: str) -> list[dict[str, object]]:
    """
    解析技能详情页中的成长表（level / description）。
    返回形如: [{"level": 1, "description": "..."}]
    """
    rows: list[dict[str, object]] = []
    # 宽松匹配表格行，避免页面结构微调导致失效
    tr_pat = re.compile(r"<tr[^>]*>\s*(.*?)\s*</tr>", re.S | re.I)
    td_pat = re.compile(r"<t[dh][^>]*>\s*(.*?)\s*</t[dh]>", re.S | re.I)
    for tr in tr_pat.findall(page_html):
        cols = td_pat.findall(tr)
        if len(cols) < 2:
            continue
        lv_txt = strip_html(cols[0])
        if not re.fullmatch(r"\d{1,2}", lv_txt):
            continue
        level = int(lv_txt)
        if level < 1 or level > 40:
            continue
        desc = strip_html(cols[1])
        if not desc:
            continue
        rows.append({"level": level, "description": desc})
    # 去重并按等级排序
    dedup: dict[int, str] = {}
    for r in rows:
        dedup[int(r["level"])] = str(r["description"])
    return [{"level": lv, "description": dedup[lv]} for lv in sorted(dedup)]


def parse_level_bonus_from_description(desc: str) -> dict[str, float]:
    """
    从单级描述里提取常用增益数值。
    与前端 SkillLinkCard 的百分比词条拆分思路一致：逐段解析「数值% + 词条名」。
    """
    out: dict[str, float] = {}
    if not desc or not str(desc).strip():
        return out
    text = re.sub(r"\s+", " ", str(desc).replace("，", " ").replace(",", " ")).strip()
    # 在下一段「数字%」或标点处截断，避免两段合成一条
    chunk_pat = re.compile(
        r"([+-]?\d+(?:\.\d+)?)\s*%\s*([^，。；：\n]*?)(?=(?:[+-]?\d+(?:\.\d+)?\s*%)|[，。；：\n]|$)"
    )
    damage_vals: list[float] = []
    for m in chunk_pat.finditer(text):
        try:
            pct = float(m.group(1))
        except ValueError:
            continue
        raw_label = (m.group(2) or "").strip()
        if not raw_label:
            continue
        label = re.sub(r"^(额外|获得|提高|增加)\s*", "", raw_label).strip()
        if not label:
            continue
        if "暴击值" in label:
            out["critValuePct"] = pct
        elif "攻击速度" in label or label in ("攻速",):
            out["attackSpeedPct"] = pct
        elif "施法速度" in label or label in ("施法",):
            out["castSpeedPct"] = pct
        elif "伤害" in label or "增伤" in label:
            damage_vals.append(pct)
    if damage_vals:
        out["damageExtraPct"] = damage_vals[0]
    # 兼容旧文案（无分段匹配时）
    if "damageExtraPct" not in out:
        m_old = re.search(r"额外\s*\+?(-?\d+(?:\.\d+)?)\s*%\s*伤害", text, re.I)
        if m_old:
            try:
                out["damageExtraPct"] = float(m_old.group(1))
            except ValueError:
                pass
    return out


def _extract_explicit_mod_inner_html(hover_html: str) -> list[str]:
    return re.findall(r'<div class="explicitMod"[^>]*>(.*?)</div>', hover_html, re.S | re.I)


def build_growth_rows_from_hover(hover_html: str) -> list[dict[str, object]] | None:
    """
    部分被动详情页无 <tr> 成长表（多为客户端渲染）。hover 中 Simple / Details 两段 explicitMod
    常给出低档与高档数值，在此按 1–40 级线性插值生成描述，供 parsedBonusesByLevel 使用。
    """
    blocks = _extract_explicit_mod_inner_html(hover_html)
    if not blocks:
        return None
    texts = [strip_html(b) for b in blocks]
    texts = [t for t in texts if t]
    if not texts:
        return None

    texts_with_pct = [t for t in texts if "%" in t]

    if len(texts_with_pct) >= 2:
        first_t, last_t = texts_with_pct[0], texts_with_pct[-1]
        first_ms = list(re.finditer(r"([+-]?\d+(?:\.\d+)?)\s*%", first_t))
        last_ms = list(re.finditer(r"([+-]?\d+(?:\.\d+)?)\s*%", last_t))
        if first_ms and last_ms:
            try:
                start_val = float(first_ms[0].group(1))
                end_val = float(last_ms[-1].group(1))
            except ValueError:
                pass
            else:
                last_m = last_ms[-1]
                prefix = last_t[: last_m.start()]
                suffix = last_t[last_m.end() :]
                rows_int: list[dict[str, object]] = []
                for lv in range(1, 41):
                    v = start_val + (end_val - start_val) * (lv - 1) / 39.0
                    vs = f"{abs(v):.4f}".rstrip("0").rstrip(".")
                    pct_str = (
                        f"+{vs}%"
                        if v > 0
                        else (f"-{vs}%" if v < 0 else "0%")
                    )
                    desc = f"{prefix}{pct_str}{suffix}".strip()
                    rows_int.append({"level": lv, "description": desc})
                return rows_int

    if len(texts_with_pct) == 1:
        single = texts_with_pct[0]
        return [{"level": lv, "description": single} for lv in range(1, 41)]

    # 非百分比：如「每 X 秒回复 Y 点魔力」两段为简单数值线性成长
    if len(texts) >= 2:
        first_t, last_t = texts[0], texts[-1]
        num_pat = re.compile(r"([+-]?\d+(?:\.\d+)?)\s+")
        first_ms = list(num_pat.finditer(first_t))
        last_ms = list(num_pat.finditer(last_t))
        if first_ms and last_ms:
            try:
                start_val = float(first_ms[-1].group(1))
                end_val = float(last_ms[-1].group(1))
            except ValueError:
                pass
            else:
                last_m = last_ms[-1]
                prefix = last_t[: last_m.start()]
                suffix = last_t[last_m.end() :].strip()
                rows_flat: list[dict[str, object]] = []
                for lv in range(1, 41):
                    v = start_val + (end_val - start_val) * (lv - 1) / 39.0
                    vi: float | int = int(round(v)) if abs(v - round(v)) < 1e-4 else round(v, 2)
                    desc = (
                        f"{prefix}{vi} {suffix}".strip()
                        if suffix
                        else f"{prefix}{vi}".strip()
                    )
                    rows_flat.append({"level": lv, "description": desc})
                return rows_flat

    return None


def enrich_passive_skills_from_hover_when_no_table(passive_skills: list[dict[str, object]]) -> int:
    filled = 0
    for skill in passive_skills:
        if skill.get("parsedBonusesByLevel"):
            continue
        hover = str(skill.get("hoverUrl") or "").strip()
        if not hover:
            continue
        url = hover if hover.startswith("http") else f"https://tlidb.com{hover}"
        try:
            h = fetch_text(url, referer=SOURCE_URL)
        except Exception:
            continue
        rows = build_growth_rows_from_hover(h)
        if not rows:
            continue
        skill["growthDescriptionByLevel"] = rows
        parsed: list[dict[str, object]] = []
        for r in rows:
            desc = str(r["description"])
            bonus = parse_level_bonus_from_description(desc)
            row_obj: dict[str, object] = {"level": int(r["level"]), "description": desc}
            row_obj.update(bonus)
            parsed.append(row_obj)
        skill["parsedBonusesByLevel"] = parsed
        skill.pop("supportDamageBonusByLevel", None)
        filled += 1
    return filled


def enrich_passive_skills_with_growth(passive_skills: list[dict[str, object]]) -> int:
    enriched = 0
    for skill in passive_skills:
        sid = str(skill.get("id") or "").strip()
        if not sid:
            continue
        url = skill_page_url(sid)
        try:
            page = fetch_text(url, referer=SOURCE_URL)
        except Exception:
            continue
        rows = parse_growth_rows_from_skill_page(page)
        if not rows:
            continue
        # 1-40 描述明细
        skill["growthDescriptionByLevel"] = rows

        # 结构化解析（暴击值/额外伤害等）；展示与计算以 parsedBonusesByLevel + description 为准
        parsed: list[dict[str, object]] = []
        for r in rows:
            desc = str(r["description"])
            bonus = parse_level_bonus_from_description(desc)
            row_obj: dict[str, object] = {"level": int(r["level"]), "description": desc}
            row_obj.update(bonus)
            parsed.append(row_obj)
        skill["parsedBonusesByLevel"] = parsed
        skill.pop("supportDamageBonusByLevel", None)
        enriched += 1
    return enriched


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


def cache_passive_skill_icons(passive_skills: list[dict[str, object]]) -> tuple[int, int, int]:
    ICON_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    skipped = 0
    failed = 0

    for skill in passive_skills:
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


def run(*, skip_icons: bool) -> None:
    req = Request(
        SOURCE_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
        },
    )
    with urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    tags = extract_passive_skill_tags(html)
    passive_skills = extract_passive_skills(html, set(tags))
    growth_count = enrich_passive_skills_with_growth(passive_skills)
    hover_fill = enrich_passive_skills_from_hover_when_no_table(passive_skills)
    for skill in passive_skills:
        skill.pop("supportDamageBonusByLevel", None)
    if skip_icons:
        downloaded_count, skipped_count, failed_count = 0, 0, 0
    else:
        downloaded_count, skipped_count, failed_count = cache_passive_skill_icons(passive_skills)

    payload = {
        "source": SOURCE_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "count": len(tags),
        "tags": tags,
        "passiveSkillCount": len(passive_skills),
        "passiveSkills": passive_skills,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    msg = (
        f"被动技能标签已更新: {payload['count']} 个，被动技能: {payload['passiveSkillCount']} 个 -> {OUT_FILE}"
    )
    msg += f"，详情页成长表: {growth_count}，hover 插值补全: {hover_fill}"
    if not skip_icons:
        msg += f"，图标下载: {downloaded_count}，复用缓存: {skipped_count}，失败: {failed_count}"
    print(msg)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--skip-icons",
        action="store_true",
        help="不下载图标，仅写入 JSON（适合先打通构建或网络较慢时）",
    )
    args = p.parse_args()
    run(skip_icons=args.skip_icons)
