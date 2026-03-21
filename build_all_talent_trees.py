import json
import os
import re
from typing import Dict, List

from extract_talent_structure import (
    extract_talents_from_content,
    group_by_required_points,
    parse_svg_to_nodes_and_connections,
    extract_core_required_points_from_content,
    extract_core_talents_from_content,
    build_tree_payload,
)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
FRONTEND_DATA_DIR = os.path.join(ROOT_DIR, "torchlight-builder", "src", "data", "talents")

PROFESSION_INDEX_FILE = os.path.join(DATA_DIR, "profession_index.json")
ALL_TREES_OUTPUT = os.path.join(FRONTEND_DATA_DIR, "profession_trees.json")

try:
    from sync_talent_assets import apply_local_paths_to_talent_tree
except ImportError:
    apply_local_paths_to_talent_tree = None


def _maybe_localize_talent_icons(tree: Dict) -> None:
    """图标使用 /assets/talents/...；资源需配合 sync_talent_assets.py 拉取。"""
    if apply_local_paths_to_talent_tree:
        apply_local_paths_to_talent_tree(tree)


def _load_profession_index() -> List[Dict]:
    with open(PROFESSION_INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_profession_page(source_file: str) -> Dict:
    path = os.path.join(DATA_DIR, source_file)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError(f"{source_file} 内容格式不符合预期（应为非空列表）")
    return data[0]


def _enrich_panel_core_from_god(
    panel_core_list: List[Dict], god_core_list: List[Dict]
) -> None:
    """
    用神格页的核心天赋（名、描述、效果）按 icon 匹配补全职业页的 4 个核心天赋。
    原地修改 panel_core_list，不改变长度与顺序。
    """
    by_icon: Dict[str, Dict] = {
        (g.get("icon") or "").strip(): g for g in god_core_list if g.get("icon")
    }
    for p in panel_core_list:
        icon = (p.get("icon") or "").strip()
        if not icon:
            continue
        g = by_icon.get(icon)
        if not g:
            continue
        p["name"] = g.get("name", p.get("name", ""))
        p["description"] = g.get("description", p.get("description", ""))
        p["effects"] = g.get("effects", p.get("effects", []))


def _merge_core_talents_with_text(
    html_core: List[Dict], text_core: Dict
) -> List[Dict]:
    """
    将 HTML 解析出的核心天赋（有 icon）与文本解析出的核心天赋（有 name/description/effects）
    按顺序合并：优先保留 HTML 的 icon，用文本的名、描述、效果覆盖占位内容。
    """
    text_list = text_core.get("coreTalents") or []
    merged: List[Dict] = []
    for i, h in enumerate(html_core):
        item = json.loads(json.dumps(h, ensure_ascii=False))
        if i < len(text_list):
            t = text_list[i]
            item["name"] = t.get("name", item.get("name", ""))
            item["description"] = t.get("description", item.get("description", ""))
            item["effects"] = t.get("effects", item.get("effects", []))
            item["requiredPoints"] = t.get("requiredPoints", item.get("requiredPoints"))
        merged.append(item)
    return merged


def _build_core_by_god_type(index: List[Dict]) -> Dict[str, Dict]:
    """
    以 6 个神格本体页面为基准，为每个 godType 解析一份核心天赋配置（含正确名称、描述、icon）。
    同一神格下的所有面板共用这份配置，实现「按神格拆分」的核心天赋展示。
    """
    core_by_god: Dict[str, Dict] = {}

    god_root_entries = [e for e in index if e.get("isGodRoot")]

    for entry in god_root_entries:
        page = _load_profession_page(entry["sourceFile"])
        html_text = page.get("html", "") or ""
        content_text = page.get("content", "") or ""

        # 文本侧：必有名称、描述、效果（用于补全/兜底）
        text_core = _extract_core_from_text(content_text)
        core_required_points = extract_core_required_points_from_content(
            html_text
        ) or text_core.get("coreRequiredPoints") or 24

        # HTML 侧：拿 icon（及可能存在的 data-bs-title）
        html_core = extract_core_talents_from_content(
            html_text, core_required_points
        )

        if html_core and text_core.get("coreTalents"):
            # 合并：同一神格下用文本的名/描述/效果，HTML 的 icon
            core_talents = _merge_core_talents_with_text(html_core, text_core)
        elif text_core.get("coreTalents"):
            core_talents = text_core["coreTalents"]
            core_required_points = core_required_points or text_core.get(
                "coreRequiredPoints", 24
            )
        elif html_core:
            core_talents = html_core
        else:
            continue

        # 神格页只保留 6 个核心天赋（官网为 6）
        core_talents = core_talents[:6]
        core_by_god[entry["godType"]] = {
            "coreRequiredPoints": core_required_points,
            "coreTalents": core_talents,
        }

    return core_by_god


def _extract_core_from_text(content_text: str) -> Dict:
    """
    从页面的纯文本 content 中解析核心天赋列表。
    通用结构示例（所有职业/神格页面基本一致）：

      Reset
      入静
      24pts
      0/1
      <若干行描述>
      大象无形
      24pts
      0/1
      <若干行描述>
      ...
      小型天赋
      0/3
      +9% 攻击伤害

    这里不依赖 HTML，只用文本，尽量适配所有职业页面。
    """
    lines = [ln.strip() for ln in content_text.splitlines()]
    core_talents: List[Dict] = []
    core_required_points = 0

    try:
        reset_idx = lines.index("Reset")
    except ValueError:
        return {"coreRequiredPoints": 0, "coreTalents": []}

    i = reset_idx + 1
    talent_idx = 0
    stop_tokens = {"小型天赋", "中型天赋", "传奇中型天赋"}

    while i + 2 < len(lines):
        name = lines[i]
        if not name or name in stop_tokens:
            break

        pts_line = lines[i + 1]
        count_line = lines[i + 2]

        if not pts_line.endswith("pts") or "0/1" not in count_line:
            break

        try:
            required_points = int(pts_line.replace("pts", "").strip())
        except ValueError:
            required_points = 24

        if core_required_points == 0:
            core_required_points = required_points

        desc_lines: List[str] = []
        j = i + 3
        while j < len(lines):
            line = lines[j]
            if not line:
                j += 1
                continue
            # 如果后面三行构成「名称 / XXpts / 0/1」，说明遇到下一个核心天赋块，当前描述结束
            if (
                j + 2 < len(lines)
                and lines[j + 1].strip().endswith("pts")
                and "0/1" in lines[j + 2]
            ):
                break
            # 遇到普通天赋块的起始标记也停止
            if line in stop_tokens:
                break
            desc_lines.append(line)
            j += 1

        full_desc = "\n".join(desc_lines).strip()
        effect_lines = [ln for ln in desc_lines if ln.strip()]

        core_talents.append(
            {
                "id": f"core_{talent_idx}",
                "name": name,
                "type": "legendary",
                "description": full_desc or name,
                "effects": effect_lines or [name],
                "requiredPoints": required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                "position": {
                    "row": 0,
                    "col": talent_idx,
                    "x": 150 + talent_idx * 200,
                    "y": 30,
                },
                "connections": [],
                "icon": "",
            }
        )

        talent_idx += 1
        i = j

    return {"coreRequiredPoints": core_required_points, "coreTalents": core_talents}


def _extract_svg_from_html(html: str) -> str:
    m = re.search(r"<svg[^>]*>.*?</svg>", html, re.S)
    if not m:
        raise ValueError("在页面 HTML 中未找到 SVG 段落（Profession Tree）")
    return m.group(0)


def _extract_meta_from_text(content_text: str, fallback_name: str) -> Dict:
    """
    从页面纯文本 content 中提取树的元信息：
    - totalPoints: 形如「勇者 /36」「巨力之神 /32」
    - tags: 形如「标签：单手武器、护甲」或「标签：攻击」
    - description: tags 行之后到 Reset 之前的若干行（跳过主要属性等固定行）
    """
    lines = [ln.strip() for ln in (content_text or "").splitlines() if ln.strip()]

    total_points = 0
    # 1) totalPoints：优先匹配「<name> /xx」
    for ln in lines[:20]:
        m = re.match(rf"^{re.escape(fallback_name)}\s*/\s*(\d+)$", ln)
        if m:
            try:
                total_points = int(m.group(1))
            except ValueError:
                total_points = 0
            break
    # 兜底：匹配首个「xxx /nn」的 nn
    if total_points == 0:
        for ln in lines[:20]:
            m = re.search(r"/\s*(\d+)$", ln)
            if m:
                try:
                    total_points = int(m.group(1))
                    break
                except ValueError:
                    pass

    # 2) tags
    tags: List[str] = []
    tag_idx = -1
    for idx, ln in enumerate(lines):
        if ln.startswith("标签："):
            tag_idx = idx
            raw = ln.replace("标签：", "").strip()
            # 常见分隔符：、 ， , 空格
            parts = re.split(r"[、，,\s]+", raw)
            tags = [p.strip() for p in parts if p.strip()]
            break

    # 3) description：从 tags 后面开始，到 Reset 之前
    description_lines: List[str] = []
    if tag_idx >= 0:
        for ln in lines[tag_idx + 1 :]:
            if ln == "Reset":
                break
            # 跳过固定字段
            if ln.startswith("主要属性："):
                continue
            if ln.startswith("标签："):
                continue
            # 有些页面会把神格英文头衔/称号放在这里，也保留
            description_lines.append(ln)
    # 取前 2 行，避免把过多无关文本带进去
    description_lines = [x for x in description_lines if x][:2]
    description = "\n".join(description_lines).strip()

    return {
        "totalPoints": total_points,
        "tags": tags,
        "description": description,
    }


def build_tree_for_entry(entry: Dict) -> Dict | None:
    """
    针对单个职业面板，生成完整的天赋树结构。
    复用 extract_talent_structure.py 中已经验证过的解析逻辑。
    """
    page = _load_profession_page(entry["sourceFile"])
    content_text = page.get("content", "") or ""
    html_text = page.get("html", "") or ""

    if not content_text or not html_text:
        print(f"[跳过] {entry['name']} ({entry['slug']}) 缺少 content/html")
        return None
    talents = extract_talents_from_content(content_text)
    grouped = group_by_required_points(talents)
    print(f"{entry['name']} - 提取到天赋条目: {len(talents)} 个")
    for pts in sorted(grouped.keys()):
        print(f"  {pts:2d} pts: {len(grouped[pts])} 个")

    svg_text = _extract_svg_from_html(html_text)
    svg_nodes, connections, _core_svg_nodes = parse_svg_to_nodes_and_connections(svg_text)

    # 从当前页 HTML 解析核心天赋（含 icon）；失败时用纯文本兜底
    core_required_points = extract_core_required_points_from_content(html_text)
    core_talents_from_page = extract_core_talents_from_content(
        html_text, core_required_points
    )
    if not core_talents_from_page:
        fallback = _extract_core_from_text(content_text)
        core_required_points = fallback["coreRequiredPoints"]
        core_talents_from_page = fallback["coreTalents"]
    else:
        # HTML 解析到图标但多为占位名时，用本页文本补全前 4 个的名称/描述
        text_fallback = _extract_core_from_text(content_text)
        text_list = text_fallback.get("coreTalents") or []
        for i in range(min(4, len(core_talents_from_page), len(text_list))):
            if (core_talents_from_page[i].get("name") or "").startswith("核心天赋"):
                t = text_list[i]
                core_talents_from_page[i]["name"] = t.get("name", "")
                core_talents_from_page[i]["description"] = t.get("description", "")
                core_talents_from_page[i]["effects"] = t.get("effects", [])
                core_talents_from_page[i]["requiredPoints"] = t.get(
                    "requiredPoints", core_talents_from_page[i]["requiredPoints"]
                )

    tree_payload = build_tree_payload(
        talents,
        svg_nodes,
        connections,
        core_required_points=core_required_points,
        core_talents_from_page=core_talents_from_page,
        tree_id=entry["id"],
    )

    # 覆盖顶层的职业元信息，使其与索引保持一致
    tree_payload["id"] = entry["id"]
    tree_payload["name"] = entry["name"]
    tree_payload["godType"] = entry["godType"]

    # 同步元信息：totalPoints / tags / description（避免被 build_tree_payload 的默认值污染）
    meta = _extract_meta_from_text(content_text, fallback_name=entry["name"])
    if meta.get("totalPoints"):
        tree_payload["totalPoints"] = meta["totalPoints"]
    if isinstance(meta.get("tags"), list) and meta["tags"]:
        tree_payload["tags"] = meta["tags"]
    if isinstance(meta.get("description"), str) and meta["description"]:
        tree_payload["description"] = meta["description"]

    return tree_payload


def main() -> None:
    index = _load_profession_index()

    # 先从 6 个神格本体页面构建 godType -> 核心天赋映射（带 icon）
    core_by_god = _build_core_by_god_type(index)

    os.makedirs(FRONTEND_DATA_DIR, exist_ok=True)

    all_trees: List[Dict] = []

    for entry in index:
        if entry.get("type") != "panel":
            continue

        try:
            tree = build_tree_for_entry(entry)
        except Exception as e:
            print(f"[错误] 生成 {entry['name']} ({entry['slug']}) 失败: {e}")
            continue

        if not tree:
            continue

        # 神格页：用该神格完整 6 个核心天赋；职业页：只保留本页 4 个核心天赋，并用神格数据补全名称/描述
        core_pack = core_by_god.get(entry["godType"])
        if core_pack and core_pack.get("coreTalents"):
            if entry.get("isGodRoot"):
                tree["coreRequiredPoints"] = core_pack["coreRequiredPoints"]
                tree["coreTalents"] = json.loads(
                    json.dumps(core_pack["coreTalents"], ensure_ascii=False)
                )
            else:
                tree["coreTalents"] = tree["coreTalents"][:4]
                _enrich_panel_core_from_god(
                    tree["coreTalents"], core_pack["coreTalents"]
                )

        tree["isGodRoot"] = entry.get("isGodRoot", False)
        all_trees.append(tree)

        _maybe_localize_talent_icons(tree)

        # 同时输出单独的 *_tree.json，便于单职业调试
        out_path = os.path.join(FRONTEND_DATA_DIR, f"{entry["id"]}_tree.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"已生成天赋树: {out_path}")

    # 总览里每列按神格分组时，把与神格同名的面板（isGodRoot）排在该列第一个
    GOD_TYPE_ORDER = [
        "strength",
        "dexterity",
        "intelligence",
        "war",
        "trickery",
        "machine",
    ]

    def _tree_sort_key(t: Dict):
        gt = t.get("godType", "")
        try:
            order = GOD_TYPE_ORDER.index(gt)
        except ValueError:
            order = 99
        return (order, -int(t.get("isGodRoot", False)))

    all_trees.sort(key=_tree_sort_key)

    with open(ALL_TREES_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_trees, f, ensure_ascii=False, indent=2)

    print(f"\n共生成 {len(all_trees)} 份职业天赋树，已汇总到: {ALL_TREES_OUTPUT}")


if __name__ == "__main__":
    main()

