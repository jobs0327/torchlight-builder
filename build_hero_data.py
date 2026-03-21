import json
import os
import re
from typing import Dict, List, Tuple

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
FRONTEND_DATA_DIR = os.path.join(ROOT_DIR, "torchlight-builder", "src", "data")

HERO_INDEX_FILE = os.path.join(DATA_DIR, "Hero.json")
OUT_FILE = os.path.join(FRONTEND_DATA_DIR, "heroes", "heroes.json")


def _clean_lines(text: str) -> List[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def _parse_hero_index() -> List[Dict]:
    """
    从 data/Hero.json 的 html 里抽取英雄列表：
    - slug
    - portrait
    - displayName: 形如「狂人 雷恩|怒火」
    - shortDesc
    """
    data = json.load(open(HERO_INDEX_FILE, "r", encoding="utf-8"))[0]
    html = data.get("html", "") or ""

    # 每个 hero 卡片结构：
    # <a href="Anger"><img src="..." class="size128"></a>
    # <a href="Anger">狂人 雷恩|怒火</a> ... 描述文本
    # 描述可能含 <br> 等标签，用 (.*?) 匹配到第一个 </div>，避免吞掉下一张卡片（如寻仇之刺）
    cards = re.findall(
        r'<a href="([^"]+)"><img[^>]+src="([^"]+)"[^>]*class="size128"[^>]*></a>.*?'
        r'<a href="\1">([^<]+)</a>.*?<hr[^>]*>\s*(.*?)</div>',
        html,
        flags=re.S,
    )

    heroes: List[Dict] = []
    for href, portrait, display, desc in cards:
        slug = href.strip()
        portrait = portrait.strip()
        display = re.sub(r"\s+", " ", display).strip()
        desc = re.sub(r"\s+", " ", re.sub(r"<br\\s*/?>", "\n", desc)).strip()
        heroes.append(
            {
                "id": slug,
                "slug": slug,
                "portrait": portrait,
                "displayName": display,
                "shortDesc": desc,
            }
        )

    # 去重保持顺序
    seen = set()
    out: List[Dict] = []
    for h in heroes:
        if h["id"] in seen:
            continue
        seen.add(h["id"])
        out.append(h)
    return out


def _parse_trait_page(slug: str) -> Dict:
    """
    从 data/<slug>.json 的 content 里抽取英雄特性详情（参考 Anger 页面）。
    """
    path = os.path.join(DATA_DIR, f"{slug}.json")
    data = json.load(open(path, "r", encoding="utf-8"))[0]
    content = data.get("content", "") or ""
    images: List[Dict] = data.get("images") or []
    # 该页面内所有英雄特性图标（按出现顺序）
    trait_icons: List[str] = [
        (img.get("src") or "").strip()
        for img in images
        if "/HeroTraits/" in (img.get("src") or "")
    ]
    lines = _clean_lines(content)

    # 例：
    # 怒火 - 英雄特性 /8
    # 狂人|雷恩
    # <简介若干行>
    # Reset
    # <特性名>
    # 需求等级 1
    # ---
    # <若干行效果>
    title = ""
    hero_name = ""
    hero_desc_lines: List[str] = []

    # 找 " - 英雄特性"
    for ln in lines[:40]:
        if " - 英雄特性" in ln:
            title = ln.split(" - 英雄特性", 1)[0].strip()
            break

    try:
        reset_idx = lines.index("Reset")
    except ValueError:
        reset_idx = -1

    if reset_idx > 0:
        # hero name 通常在 Reset 前 1~5 行内
        for j in range(max(0, reset_idx - 6), reset_idx):
            if "|" in lines[j]:
                hero_name = lines[j].strip()
                # hero desc 在 hero_name 后到 Reset 前
                start = j + 1
                for k in range(start, reset_idx):
                    hero_desc_lines.append(lines[k])
                break

    hero_desc = "\n".join([x for x in hero_desc_lines if x]).strip()

    traits: List[Dict] = []
    if reset_idx >= 0:
        i = reset_idx + 1
        while i < len(lines):
            name = lines[i].strip()
            if not name:
                i += 1
                continue

            # 特性名后面一般是「需求等级 xx」
            level = None
            if i + 1 < len(lines) and lines[i + 1].startswith("需求等级"):
                m = re.search(r"(\d+)", lines[i + 1])
                if m:
                    level = int(m.group(1))
                i += 2
            else:
                # 不是特性块，继续
                i += 1
                continue

            # 跳过分隔线 ---
            if i < len(lines) and lines[i].strip() == "---":
                i += 1

            eff: List[str] = []
            while i < len(lines):
                ln = lines[i].strip()
                if not ln:
                    i += 1
                    continue
                # 下一个特性块开头
                if i + 1 < len(lines) and lines[i + 1].startswith("需求等级"):
                    break
                # 结束条件：技能商店/其他模块
                if ln.endswith(" /263") or ln.startswith("技能商店"):
                    i = len(lines)
                    break
                eff.append(ln)
                i += 1

            icon = trait_icons[len(traits)] if len(traits) < len(trait_icons) else ""
            traits.append(
                {
                    "name": name,
                    "requiredLevel": level or 1,
                    "effects": eff,
                    "icon": icon or None,
                }
            )

    return {
        "traitTitle": title or slug,
        "heroName": hero_name,
        "heroDescription": hero_desc,
        "traits": traits,
        "sourceUrl": f"https://tlidb.com/cn/{slug}",
    }


def main() -> None:
    heroes = _parse_hero_index()
    os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)

    for h in heroes:
        detail = _parse_trait_page(h["slug"])
        h.update(detail)

    # 头像与特性图标使用本地 public/assets/heroes（需配合 sync_hero_assets.py 拉取文件）
    try:
        from sync_hero_assets import apply_local_paths_to_heroes

        apply_local_paths_to_heroes(heroes)
    except ImportError:
        pass

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(heroes, f, ensure_ascii=False, indent=2)

    print(f"已生成英雄数据到: {OUT_FILE}（{len(heroes)} 个）")


if __name__ == "__main__":
    main()

