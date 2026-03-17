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
FRONTEND_DATA_DIR = os.path.join(ROOT_DIR, "torchlight-builder", "src", "data")

PROFESSION_INDEX_FILE = os.path.join(DATA_DIR, "profession_index.json")
ALL_TREES_OUTPUT = os.path.join(FRONTEND_DATA_DIR, "profession_trees.json")


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


def _extract_svg_from_html(html: str) -> str:
    m = re.search(r"<svg[^>]*>.*?</svg>", html, re.S)
    if not m:
        raise ValueError("在页面 HTML 中未找到 SVG 段落（Profession Tree）")
    return m.group(0)


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

    core_required_points = extract_core_required_points_from_content(html_text)
    core_talents_from_page = extract_core_talents_from_content(
        html_text, core_required_points
    )

    talents = extract_talents_from_content(content_text)
    grouped = group_by_required_points(talents)
    print(f"{entry['name']} - 提取到天赋条目: {len(talents)} 个")
    for pts in sorted(grouped.keys()):
        print(f"  {pts:2d} pts: {len(grouped[pts])} 个")

    svg_text = _extract_svg_from_html(html_text)
    svg_nodes, connections, _core_svg_nodes = parse_svg_to_nodes_and_connections(svg_text)

    tree_payload = build_tree_payload(
        talents,
        svg_nodes,
        connections,
        core_required_points,
        core_talents_from_page,
    )

    # 覆盖顶层的职业元信息，使其与索引保持一致
    tree_payload["id"] = entry["id"]
    tree_payload["name"] = entry["name"]
    tree_payload["godType"] = entry["godType"]

    return tree_payload


def main() -> None:
    index = _load_profession_index()

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

        all_trees.append(tree)

        # 同时输出单独的 *_tree.json，便于单职业调试
        out_path = os.path.join(FRONTEND_DATA_DIR, f"{entry['id']}_tree.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"已生成天赋树: {out_path}")

    with open(ALL_TREES_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_trees, f, ensure_ascii=False, indent=2)

    print(f"\n共生成 {len(all_trees)} 份职业天赋树，已汇总到: {ALL_TREES_OUTPUT}")


if __name__ == "__main__":
    main()

