import json
import math
import os
import re
import html
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List, Tuple

"""
从已经抓取好的 TLIDB 天赋页面（如 data/The_Brave.json）中，
抽取两类结构化数据：

1. 文本天赋列表（the_brave_talents_parsed.json）
2. 完整的天赋树结构（the_brave_tree.json），包含：
   - 每个节点的坐标、类型、小/中/传奇
   - 每个节点的需求点数（0/3/6/9/12/15/18）
   - 节点之间的连接关系（connections）

后续前端可以用 the_brave_tree.json 去生成 professionTalentData.ts。
"""


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
SOURCE_FILE = os.path.join(DATA_DIR, "The_Brave.json")
TALENTS_OUTPUT_FILE = os.path.join(DATA_DIR, "the_brave_talents_parsed.json")
# 统一唯一数据源：直接输出到前端项目的 JSON 文件中
TREE_OUTPUT_FILE = os.path.join(
    ROOT_DIR, "torchlight-builder", "src", "data", "the_brave_tree.json"
)


def load_content() -> str:
    """读取抓取好的 The_Brave 页面内容（由 full_scraper.py 生成）"""
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("The_Brave.json 内容格式不符合预期（应为非空列表）")

    # full_scraper 保存的数据结构中，content 字段是整页的可读文本
    return data[0].get("content", "")


def load_html() -> str:
    """读取抓取好的 The_Brave 页面原始 HTML（包含 SVG、核心天赋卡片等结构）"""
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("The_Brave.json 内容格式不符合预期（应为非空列表）")

    return data[0].get("html", "")


def extract_talents_from_content(content: str) -> List[Dict]:
    """
    从页面纯文本 content 中抽取普通天赋条目。

    文本结构在不同页面里存在几种变体：
    - 0 点（第一列）通常没有 "0pts" 行：
        小型天赋
        0/3
        +9% 攻击伤害
    - 非 0 点会有 "3pts/6pts..."：
        中型天赋
        3pts
        0/3
        +18% 攻击伤害
    - 描述可能 1 行或多行（直到下一个“类型标记行”开始）

    早期用正则一次性抓取会出现“把下一条的类型行当成当前描述第二行”的吞行问题，
    进而造成后续条目缺失与整体错位，因此这里改成逐行状态机解析。
    """
    talent_type_map = {
        "小型天赋": "small",
        "中型天赋": "notable",
        "传奇中型天赋": "legendary",
    }

    talents: List[Dict] = []

    lines = [ln.strip() for ln in content.splitlines()]
    type_tokens = set(talent_type_map.keys())

    def _is_points_line(s: str) -> bool:
        return bool(s) and s.endswith("pts") and s[:-3].strip().isdigit()

    def _parse_points_line(s: str) -> int:
        try:
            return int(s.replace("pts", "").strip())
        except Exception:
            return 0

    def _is_count_line(s: str) -> bool:
        return bool(re.match(r"^0\s*/\s*\d+\s*$", s))

    def _parse_max_points(s: str) -> int:
        m = re.match(r"^0\s*/\s*(\d+)\s*$", s)
        return int(m.group(1)) if m else 3

    i = 0
    tid = 0
    while i < len(lines):
        ttype_cn = lines[i]
        if ttype_cn not in type_tokens:
            i += 1
            continue

        ttype = talent_type_map.get(ttype_cn, "small")
        i += 1

        req_points = 0
        # 可选 points 行
        if i < len(lines) and _is_points_line(lines[i]):
            req_points = _parse_points_line(lines[i])
            i += 1

        # 必须有 count 行
        if i >= len(lines) or not _is_count_line(lines[i]):
            continue
        max_points = _parse_max_points(lines[i])
        i += 1

        # 描述：读到下一个类型标记行（或结束）
        desc_lines: List[str] = []
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue
            if s in type_tokens:
                break
            # 防止极端情况下把 pts/count 行吞进描述（结构错乱）
            if _is_points_line(s) or _is_count_line(s):
                break
            desc_lines.append(s)
            i += 1

        clean_desc = "\n".join(desc_lines).strip()
        clean_desc = (
            clean_desc.replace(" （神格生效上限：1）", "")
            .replace("(神格生效上限：1)", "")
            .strip()
        )

        first_line = clean_desc.split("\n", 1)[0] if clean_desc else ""

        talents.append(
            {
                "id": f"talent_{tid}",
                "type": ttype,
                "requiredPoints": req_points,
                "maxPoints": max_points,
                "description": clean_desc,
                "name": (first_line[:60] if first_line else ""),
            }
        )
        tid += 1

    return talents


def group_by_required_points(talents: List[Dict]) -> Dict[int, List[Dict]]:
    """按 requiredPoints 分组，方便你检查层数 / 分布是否合理"""
    by_points: Dict[int, List[Dict]] = defaultdict(list)
    for t in talents:
        by_points[t["requiredPoints"]].append(t)
    return by_points


def save_result(talents: List[Dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "professionId": "the_brave",
        "professionName": "勇者",
        "talents": talents,
    }
    with open(TALENTS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


# ========= 解析 SVG，生成完整天赋树结构 =========

def load_svg() -> str:
    """从 The_Brave.html 片段中提取 SVG 段落"""
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = data[0].get("html", "")
    m = re.search(r"<svg[^>]*>.*?</svg>", html, re.S)
    if not m:
        raise ValueError("在 The_Brave.html 中未找到 SVG 段落")
    return m.group(0)


def _strip_tag(tag: str) -> str:
    """去掉 XML namespace 前缀"""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_tooltip_name(raw: str) -> str:
    """
    data-bs-title 里的 tooltip HTML 里，名字放在
    <div class="fw-bold">名字</div> 里，这里简单用正则抠一下。
    """
    if not raw:
        return ""
    m = re.search(r"<div[^>]*fw-bold[^>]*>([^<]+)</div>", raw)
    if m:
        return m.group(1).strip()
    return re.sub(r"<[^>]+>", "", raw).strip()


def parse_svg_to_nodes_and_connections(svg_text: str) -> Tuple[List[Dict], List[Tuple[int, int]], List[Dict]]:
    """
    解析 ProfessionTree SVG：
    - <g class="nodes"> 下的一组 circle + image + text 组合 → 一个节点
    - <g class="connections"> 下的 line → 两个节点之间的连线
    """
    root = ET.fromstring(svg_text)

    nodes_group = None
    connections_group = None
    for g in root.iter():
        if g.attrib.get("class") == "nodes":
            nodes_group = g
        elif g.attrib.get("class") == "connections":
            connections_group = g

    if nodes_group is None or connections_group is None:
        raise ValueError("SVG 中未找到 nodes / connections 分组")

    # 解析普通节点和核心天赋节点
    nodes: List[Dict] = []
    core_nodes: List[Dict] = []
    current_node: Dict | None = None
    level_texts: List[Tuple[float, float, int]] = []

    # 注意：神格页的 SVG 结构里，circle/image/text 往往嵌套在 <g> 内，
    # 不能只遍历 nodes_group 的直接子元素，否则会漏掉 0/3/6/9/12/15/18 的层级文本。
    for elem in nodes_group.iter():
        if elem is nodes_group:
            continue
        tag = _strip_tag(elem.tag)
        cls = elem.attrib.get("class", "")

        if tag == "circle":
            cx = float(elem.attrib.get("cx", "0"))
            cy = float(elem.attrib.get("cy", "0"))
            r = float(elem.attrib.get("r", "32"))

            # talent_type1: 小型，3: 中型，4: 传奇中型
            node_type = "small"
            if "talent_type3" in cls:
                node_type = "notable"
            elif "talent_type4" in cls:
                node_type = "legendary"

            is_core = "CoreTalentIcon" in (elem.attrib.get("class", "") + cls)

            current_node = {
                "id": len(nodes),  # 暂用 index，后面再转成字符串 id
                "type": node_type,
                "cx": cx,
                "cy": cy,
                "r": r,
                "requiredPoints": 0,
                "icon": "",
                "name": "",
                "tooltip": "",
            }
            if is_core:
                core_nodes.append(current_node)
            else:
                nodes.append(current_node)

        elif tag == "image" and current_node is not None:
            # 补充 icon & tooltip
            href = (
                elem.attrib.get("{http://www.w3.org/1999/xlink}href")
                or elem.attrib.get("xlink:href")
                or elem.attrib.get("href", "")
            )
            tooltip_raw = elem.attrib.get("data-bs-title", "")
            name = _parse_tooltip_name(tooltip_raw)

            current_node["icon"] = href
            if name:
                current_node["name"] = name
            if tooltip_raw:
                current_node["tooltip"] = tooltip_raw

        elif tag == "text" and "level_up_time" in cls:
            # 神格页/部分职业页中，level_up_time 的 <text> 位置不一定紧跟对应节点，
            # 不能简单写入 nodes[-1]，改为记录坐标并在后面做最近邻匹配。
            text_value = (elem.text or "").strip()
            if not text_value.isdigit():
                continue
            x_raw = elem.attrib.get("x")
            y_raw = elem.attrib.get("y")
            if x_raw is None or y_raw is None:
                continue
            try:
                x = float(x_raw)
                y = float(y_raw)
                val = int(text_value)
            except ValueError:
                continue
            # 只接受层级点数（0/3/6/9/12/15/18），避免把其他数字（如 1）误当作层级
            if val < 0 or val > 18 or val % 3 != 0:
                continue
            level_texts.append((x, y, val))

    # 将 level_up_time 文本按坐标就近匹配到节点，补齐 requiredPoints（0/3/6/9/12/15/18）
    if level_texts and nodes:
        def _nearest_node_obj(x: float, y: float) -> Dict:
            best = nodes[0]
            best_dist = float("inf")
            for n in nodes:
                dx = n["cx"] - x
                dy = n["cy"] - y
                d2 = dx * dx + dy * dy
                if d2 < best_dist:
                    best_dist = d2
                    best = n
            return best

        for x, y, val in level_texts:
            _nearest_node_obj(x, y)["requiredPoints"] = val

    # 解析连接线：用 line 两端点分别匹配最近的节点
    def nearest_node(x: float, y: float) -> int:
        best_idx = 0
        best_dist = float("inf")
        for n in nodes:
            dx = n["cx"] - x
            dy = n["cy"] - y
            d2 = dx * dx + dy * dy
            if d2 < best_dist:
                best_dist = d2
                best_idx = n["id"]
        return best_idx

    connections: List[Tuple[int, int]] = []
    for elem in list(connections_group):
        if _strip_tag(elem.tag) != "line":
            continue
        x1 = float(elem.attrib.get("x1", "0"))
        y1 = float(elem.attrib.get("y1", "0"))
        x2 = float(elem.attrib.get("x2", "0"))
        y2 = float(elem.attrib.get("y2", "0"))

        a = nearest_node(x1, y1)
        b = nearest_node(x2, y2)
        if a != b:
            pair = tuple(sorted((a, b)))
            if pair not in connections:
                connections.append(pair)

    return nodes, connections, core_nodes


def enrich_nodes_with_grid(nodes: List[Dict]) -> None:
    """
    根据节点的 cx/cy 推导 row/col，用于前端 GRID_CONFIG 布局。
    """
    unique_x = sorted({round(n["cx"]) for n in nodes})
    unique_y = sorted({round(n["cy"]) for n in nodes})

    def nearest_index(val: float, arr: List[int]) -> int:
        return min(range(len(arr)), key=lambda i: abs(arr[i] - val))

    for n in nodes:
        n["row"] = nearest_index(n["cy"], unique_y)
        n["col"] = nearest_index(n["cx"], unique_x)


def _html_to_text(raw: str) -> str:
    """
    将 tooltip / HTML 片段转换为纯文本：
    - <br> / <br /> 转为换行
    - 其他标签全部去掉
    """
    if not raw:
        return ""

    # 统一处理换行标签
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    # 去掉其他所有 HTML 标签
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _strip_generic_prefix(text: str) -> str:
    """
    去掉描述前缀里的「小型天赋 / 中型天赋 / 传奇中型天赋」字样，
    避免在 effects 里重复出现。
    """
    if not text:
        return ""
    return re.sub(
        r"^(小型天赋|中型天赋|传奇中型天赋)[:：]?\s*",
        "",
        text,
    ).strip()


def _extract_required_points_from_html(raw: str, default: int = 18) -> int:
    """
    从 tooltip HTML 中解析核心天赋的需求点数。
    网站结构大致为：
      <div class="card text-center">
        ...
        <div class="card-body">需要 18 点</div>
        ...
      </div>
    实际的数值就存储在 card-body 里。
    """
    if not raw:
        return default

    # 优先从 card-body 里提取文本，避免误匹配其他位置的数字
    m_block = re.search(
        r'<div[^>]*class="[^"]*card-body[^"]*"[^>]*>(.*?)</div>',
        raw,
        flags=re.IGNORECASE | re.DOTALL,
    )
    target = m_block.group(1) if m_block else raw

    # 先做一次简单的 HTML → 文本转换
    target_text = _html_to_text(target)

    # 优先匹配「需要 18 点」「达到 18 点」
    m = re.search(r"(?:需要|达到)\s*(\d+)\s*点", target_text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    # 兜底：匹配第一个「数字+点」
    m2 = re.search(r"(\d+)\s*点", target_text)
    if m2:
        try:
            return int(m2.group(1))
        except ValueError:
            pass

    return default


def extract_core_required_points_from_content(content: str, default: int = 24) -> int:
    """
    从整个页面内容中提取核心天赋所需点数。
    对应结构类似：
      <div class="card text-center">
        ...
        <div class="card-body">
          <div>24</div>
          ...
        </div>
      </div>
    """
    if not content:
        return default

    m = re.search(
        r'<div[^>]*class="[^"]*card-body[^"]*"[^>]*>.*?<div>\s*(\d+)\s*</div>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return default
    return default


def extract_core_talents_from_content(
    content: str, core_required_points: int
) -> List[Dict]:
    """
    从页面上的 card text-center 区块中提取核心天赋：
    - card-body 里的第一个 <div> 是需求点数（已在上面解析）
    - 同一 card-body 里的若干 <img> 对应 4 个核心天赋图标
    - 每个 <img> 的 data-bs-title 是 tooltip HTML，包含名字和效果
    """
    if not content:
        return []

    # 优先在 card-body 内查找带 CoreTalentIcon 的 <img>，
    # 若未找到，则在整页 HTML 内兜底查找。
    img_html_list: List[str] = []

    m = re.search(
        r'<div[^>]*class="[^"]*card-body[^"]*"[^>]*>(.*?)</div>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        block = html.unescape(m.group(1))
        img_html_list = re.findall(
            r'<img[^>]+CoreTalentIcon[^>]*>',
            block,
            flags=re.IGNORECASE,
        )

    if not img_html_list:
        # 兜底：直接在整页 HTML 内找 CoreTalentIcon 图标
        img_html_list = re.findall(
            r'<img[^>]+CoreTalentIcon[^>]*>',
            content,
            flags=re.IGNORECASE,
        )

    if not img_html_list:
        return []
    core_talents: List[Dict] = []

    for i, img_html in enumerate(img_html_list):
        src_match = re.search(r'src="([^"]+)"', img_html)
        icon = src_match.group(1) if src_match else ""

        title_match = re.search(r'data-bs-title="([^"]+)"', img_html)
        raw_title = html.unescape(title_match.group(1)) if title_match else ""

        name = _parse_tooltip_name(raw_title) or f"核心天赋{i+1}"
        desc = _html_to_text(raw_title) or name
        # 同样对核心天赋的效果做前缀清理与空行过滤
        effects: List[str] = []
        for line in desc.split("\n"):
            raw = line.strip()
            if not raw:
                continue
            cleaned = _strip_generic_prefix(raw)
            if cleaned:
                effects.append(cleaned)
        if not effects:
            effects = [name]

        core_talents.append(
            {
                "id": f"core_{i}",
                "name": name,
                "type": "legendary",
                "description": desc,
                "effects": effects,
                "requiredPoints": core_required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                # 位置对前端已经不重要，这里给一个简单的布局占位
                "position": {
                    "row": 0,
                    "col": i,
                    "x": 150 + i * 200,
                    "y": 30,
                },
                "connections": [],
                "icon": icon,
            }
        )

    return core_talents


def build_tree_payload(
    talents: List[Dict],
    svg_nodes: List[Dict],
    connections: List[Tuple[int, int]],
    core_required_points: int,
    core_talents_from_page: List[Dict],
    tree_id: str | None = None,
) -> Dict:
    """
    组合文本天赋信息 + SVG 节点信息，生成一个接近前端 ProfessionTalentTree 的结构。
    这里只做基础字段映射，具体 effects/description 可以按需要再细化。
    """
    enrich_nodes_with_grid(svg_nodes)

    # 先过滤 SVG 中的“空占位 circle”：
    # 这类节点通常没有 image（icon 为空），也没有 tooltip/name。
    # 如果不提前过滤，后续的文本映射会把真实天赋条目错误地分配给这些占位点，造成全局错位。
    svg_nodes = [
        n
        for n in svg_nodes
        if (n.get("icon") or n.get("tooltip") or n.get("name"))
    ]

    # SVG 中层级（0/3/6/9/12/15/18）文本在不同页面里可能缺失或错位，
    # 这里用网格列（col）推导每个节点的 requiredPoints，保证层级稳定。
    unique_cols = sorted({n["col"] for n in svg_nodes})
    col_to_points: Dict[int, int] = {}
    for idx, col in enumerate(unique_cols):
        col_to_points[col] = idx * 3
    for n in svg_nodes:
        n["requiredPoints"] = col_to_points.get(n["col"], n.get("requiredPoints", 0))

    def _norm(s: str) -> str:
        if not s:
            return ""
        s = _html_to_text(s)
        s = s.replace("\u3000", " ").strip()
        # 统一常见空白/标点差异，尽量提高匹配命中率
        s = re.sub(r"\s+", " ", s)
        s = s.replace("：", ":")
        s = s.replace("（", "(").replace("）", ")")
        s = s.replace("％", "%")
        return s.strip()

    def _desc_key(t: Dict) -> str:
        # talents 来自纯文本，description 可能含 1~2 行
        return _norm(t.get("description", ""))

    def _name_key(t: Dict) -> str:
        return _norm(t.get("name", ""))

    # 构建多级索引：优先按 tooltip/名称匹配，其次按 (req,type/name) 精准匹配，再按顺序兜底。
    # 注意：同一个 talent 会被放入多个 bucket，因此必须用 used 集合避免重复分配。
    bucket_req_type_name: Dict[Tuple[int, str, str], List[Dict]] = defaultdict(list)
    bucket_req_name: Dict[Tuple[int, str], List[Dict]] = defaultdict(list)
    bucket_req_type: Dict[Tuple[int, str], List[Dict]] = defaultdict(list)
    bucket_req: Dict[int, List[Dict]] = defaultdict(list)

    for t in talents:
        req = int(t.get("requiredPoints", 0) or 0)
        ttype = t.get("type", "small") or "small"
        nk = _name_key(t)
        bucket_req_type_name[(req, ttype, nk)].append(t)
        if nk:
            bucket_req_name[(req, nk)].append(t)
        bucket_req_type[(req, ttype)].append(t)
        bucket_req[req].append(t)

    used_talent_ids: set[str] = set()

    def _pop_from_list(arr: List[Dict] | None) -> Dict | None:
        if not arr:
            return None
        while arr:
            t = arr.pop(0)
            tid = str(t.get("id", ""))
            if tid and tid in used_talent_ids:
                continue
            if tid:
                used_talent_ids.add(tid)
            return t
        return None

    def _score_by_description(tooltip_text: str, talent: Dict) -> int:
        """
        用“描述行命中数”做一个轻量评分：
        - tooltip_text 来自 SVG 的 data-bs-title，经 _norm 归一
        - talent description 来自 content 抓取（通常 1~2 行）
        """
        if not tooltip_text:
            return 0
        desc = talent.get("description", "") or ""
        parts = [p.strip() for p in desc.splitlines() if p.strip()]
        if not parts:
            return 0
        score = 0
        for p in parts:
            np = _norm(p)
            if np and np in tooltip_text:
                score += 1
        return score

    generic_node_names = {"小型天赋", "中型天赋", "传奇中型天赋"}

    def pop_matching_talent_for_node(n: Dict) -> Dict | None:
        req = int(n.get("requiredPoints", 0) or 0)
        ttype = n.get("type", "small") or "small"

        # node name 优先使用 SVG tooltip 里的 fw-bold 名称（parse_svg 已填充），否则退回空
        node_name = _norm(n.get("name", ""))
        if node_name in generic_node_names:
            node_name = ""
        node_tooltip = _norm(n.get("tooltip", ""))

        # 0) 若 tooltip 里包含具体效果文本，优先用“描述相似度”在同 req 内挑最佳匹配，
        # 这样即使 SVG 的 type 识别有误，也能更稳地对齐到正确的文本条目。
        if node_tooltip:
            candidates = bucket_req.get(req, []) or []
            best = None
            best_score = 0
            best_idx = -1
            for idx, cand in enumerate(candidates):
                tid = str(cand.get("id", ""))
                if tid and tid in used_talent_ids:
                    continue
                sc = _score_by_description(node_tooltip, cand)
                if sc > best_score:
                    best_score = sc
                    best = cand
                    best_idx = idx
                    # 2 行全命中基本就足够确定
                    if best_score >= 2:
                        break
            if best and best_score > 0:
                # 从候选列表里移除该元素，避免再次命中
                try:
                    candidates.pop(best_idx)
                except Exception:
                    pass
                tid = str(best.get("id", ""))
                if tid:
                    used_talent_ids.add(tid)
                return best

        # 1) (req,type,name) 精准匹配
        if node_name:
            hit = _pop_from_list(bucket_req_type_name.get((req, ttype, node_name)))
            if hit:
                return hit

        # 2) (req,name) 次优匹配（同一层可能有跨 type 的描述变体）
        if node_name:
            hit = _pop_from_list(bucket_req_name.get((req, node_name)))
            if hit:
                return hit

        # 3) (req,type) 顺序兜底
        hit = _pop_from_list(bucket_req_type.get((req, ttype)))
        if hit:
            return hit

        # 4) 只按 req 兜底
        hit = _pop_from_list(bucket_req.get(req))
        if hit:
            return hit

        return None

    tree_nodes = []
    # 为了让“顺序兜底”更稳定，先把 svg_nodes 做一个确定性排序（从左到右、从上到下）
    # 这样即使某页的 SVG 遍历顺序变化，也不至于导致大规模错位。
    svg_nodes_sorted = sorted(
        svg_nodes,
        key=lambda x: (
            int(x.get("requiredPoints", 0) or 0),
            str(x.get("type", "")),
            int(x.get("row", 0) or 0),
            float(x.get("cy", 0) or 0),
            float(x.get("cx", 0) or 0),
        ),
    )

    for n in svg_nodes_sorted:
        talent = pop_matching_talent_for_node(n)
        # 当 SVG 给的是泛化名（小型/中型/传奇中型天赋）时，优先用文本天赋第一行作为展示名
        base_name = n.get("name", "")
        name = talent["name"] if talent else base_name
        if _norm(base_name) in generic_node_names and talent:
            name = talent.get("name") or name
        raw_desc = talent["description"] if talent else n.get("tooltip", "")
        desc = _html_to_text(raw_desc)

        effects: List[str] = []
        if desc:
            # 简单按换行拆成多条效果：
            # 1) 先去掉空行
            # 2) 去掉「小型天赋 / 中型天赋 / 传奇中型天赋」前缀
            # 3) 再过滤掉清理后变成空的行，避免 effects 出现空字符串
            effects = []
            for line in desc.split("\n"):
                raw = line.strip()
                if not raw:
                    continue
                cleaned = _strip_generic_prefix(raw)
                if cleaned:
                    effects.append(cleaned)

        # 过滤掉 SVG 中的空占位节点：
        # - 没有名称
        # - 没有效果文本
        # - 没有图标
        # 这些通常是最上方那一排没有实际含义的圆点
        if not name and not effects and not n.get("icon"):
            continue

        # 如果 name 仍是泛化名，但 effects 有内容，则用 effects[0] 作为 name（避免前端显示“中型天赋”）
        if _norm(name) in generic_node_names and effects:
            name = effects[0]

        tree_nodes.append(
            {
                "id": f"node_{n['id']}",
                "name": name or "",
                "type": n["type"],
                "effects": effects,
                # 优先使用文本解析出来的 requiredPoints（更稳定），避免 SVG 层级文本缺失/错位导致 0-18 层级错乱
                "requiredPoints": talent["requiredPoints"] if talent else n["requiredPoints"],
                "maxPoints": talent["maxPoints"] if talent else 3,
                "currentPoints": 0,
                "position": {
                    "row": n["row"],
                    "col": n["col"],
                    "x": n["cx"],
                    "y": n["cy"],
                },
                "connections": [],  # 先留空，后面统一填充
                "icon": n["icon"],
            }
        )

    # 说明：如仍有个别页面 tooltip 缺失导致的错位，可在此处添加 tree_id 级别特例修正。

    # 根据 connections 数组填充每个节点的 connections 字段（存对方 id）
    id_to_idx = {tn["id"]: idx for idx, tn in enumerate(tree_nodes)}
    idx_to_id = {idx: tn["id"] for idx, tn in enumerate(tree_nodes)}

    for a_idx, b_idx in connections:
        a_id = f"node_{a_idx}"
        b_id = f"node_{b_idx}"
        if a_id in id_to_idx and b_id in id_to_idx:
            tree_nodes[id_to_idx[a_id]]["connections"].append(b_id)
            tree_nodes[id_to_idx[b_id]]["connections"].append(a_id)

    # 核心天赋：从页面 card-body 区块提取（不再依赖 SVG）
    core_talents = core_talents_from_page

    payload = {
        "id": "the_brave",
        "name": "勇者",
        "godType": "strength",
        "description": "巨力之神的传承，攻守均衡的战斗大师",
        "tags": ["单手武器", "护甲"],
        "totalPoints": 36,
        "allocatedPoints": 0,
        # 解锁核心天赋所需的总点数（来自页面 card-body 中的数值，例如 24）
        "coreRequiredPoints": core_required_points,
        "coreTalents": core_talents,
        "nodes": tree_nodes,
    }

    return payload


def main() -> None:
    # 1. 文本天赋条目（基于纯文本） & 核心天赋（基于原始 HTML）
    content_text = load_content()
    html_text = load_html()

    core_required_points = extract_core_required_points_from_content(html_text)
    core_talents_from_page = extract_core_talents_from_content(
        html_text, core_required_points
    )

    # 如果基于 HTML 没能成功解析出核心天赋（结构变化等原因），
    # 使用一份基于当前网站数据的兜底配置，避免 coreTalents 为空。
    if not core_talents_from_page:
        core_talents_from_page = [
            {
                "id": "core_0",
                "name": "入静",
                "type": "legendary",
                "description": (
                    "静止时，每 0.25 秒，额外 +12% 伤害，至多额外 +48% 伤害；"
                    "失去静止状态时，移除该效果"
                ),
                "effects": [
                    "静止时，每 0.25 秒，额外 +12% 伤害，至多额外 +48% 伤害",
                    "失去静止状态时，移除该效果",
                ],
                "requiredPoints": core_required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                "position": {"row": 0, "col": 0, "x": 150, "y": 30},
                "connections": [],
                "icon": "https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_rujing_Icon_128.webp",
            },
            {
                "id": "core_1",
                "name": "大象无形",
                "type": "legendary",
                "description": "战吼技能的影响上限变为 2 倍，+66% 战吼技能范围",
                "effects": ["战吼技能的影响上限变为 2 倍", "+66% 战吼技能范围"],
                "requiredPoints": core_required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                "position": {"row": 0, "col": 1, "x": 350, "y": 30},
                "connections": [],
                "icon": "https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_daxiangwuxing_Icon_128.webp",
            },
            {
                "id": "core_2",
                "name": "坚毅",
                "type": "legendary",
                "description": "每有 1 层坚韧祝福，额外 +4% 护甲值",
                "effects": ["每有 1 层坚韧祝福，额外 +4% 护甲值"],
                "requiredPoints": core_required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                "position": {"row": 0, "col": 2, "x": 550, "y": 30},
                "connections": [],
                "icon": "https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_jianyi_Icon_128.webp",
            },
            {
                "id": "core_3",
                "name": "灰烬装甲",
                "type": "legendary",
                "description": "对非物理伤害，+25% 护甲有效率",
                "effects": ["对非物理伤害，+25% 护甲有效率"],
                "requiredPoints": core_required_points,
                "maxPoints": 1,
                "currentPoints": 0,
                "position": {"row": 0, "col": 3, "x": 750, "y": 30},
                "connections": [],
                "icon": "https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_huijinzhuangjia_Icon_128.webp",
            },
        ]
    talents = extract_talents_from_content(content_text)

    print(f"提取到天赋条目: {len(talents)} 个")

    grouped = group_by_required_points(talents)
    print("按 requiredPoints 分布：")
    for pts in sorted(grouped.keys()):
        print(f"  {pts:2d} pts: {len(grouped[pts])} 个")

    print("\n示例：")
    for t in talents[:8]:
        print(f"- [{t['type']}] {t['requiredPoints']}pts 0/{t['maxPoints']}  {t['name']}")

    save_result(talents)
    print(f"\n已保存文本解析结果到: {TALENTS_OUTPUT_FILE}")

    # 2. SVG → 完整天赋树
    svg_text = load_svg()
    svg_nodes, connections, core_svg_nodes = parse_svg_to_nodes_and_connections(svg_text)
    tree_payload = build_tree_payload(
        talents,
        svg_nodes,
        connections,
        core_required_points,
        core_talents_from_page,
        tree_id="the_brave",
    )

    with open(TREE_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(tree_payload, f, ensure_ascii=False, indent=2)

    print(f"已生成天赋树结构到: {TREE_OUTPUT_FILE}")


if __name__ == "__main__":
    main()

