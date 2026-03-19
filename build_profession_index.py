import json
import os
from typing import Dict, List

"""
从 data/Talent.json 中推导出所有神格与大天赋面板的索引。
输出: data/profession_index.json

结构示例:
[
  {
    "slug": "God_of_Might",
    "id": "god_of_might",
    "name": "巨力之神",
    "type": "god",
    "godType": "strength",
    "sourceFile": "God_of_Might.json"
  },
  {
    "slug": "The_Brave",
    "id": "the_brave",
    "name": "勇者",
    "type": "panel",
    "godType": "strength",
    "sourceFile": "The_Brave.json"
  },
  ...
]
"""

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
TALENT_PAGE_FILE = os.path.join(DATA_DIR, "Talent.json")
OUTPUT_INDEX_FILE = os.path.join(DATA_DIR, "profession_index.json")


def load_talent_page() -> Dict:
  with open(TALENT_PAGE_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)
  if not isinstance(data, list) or not data:
    raise ValueError("Talent.json 内容格式不符合预期（应为非空列表）")
  return data[0]


def build_slug_to_name(links: List[Dict]) -> Dict[str, str]:
  slug_to_name: Dict[str, str] = {}
  for link in links:
    href = link.get("href") or ""
    text = (link.get("text") or "").strip()
    if not href.startswith("https://tlidb.com/cn/"):
      continue
    if not text:
      continue
    slug = href.split("/")[-1]
    # 过滤掉分类和导航链接，只保留具体页面
    if slug in {"Talent", "Hero", "Inventory", "Active_Skill", "Support_Skill", "Passive_Skill"}:
      continue
    slug_to_name[slug] = text
  return slug_to_name


def build_profession_index() -> None:
  page = load_talent_page()
  links = page.get("links", [])
  content = page.get("content", "") or ""

  slug_to_name = build_slug_to_name(links)
  name_to_slugs: Dict[str, List[str]] = {}
  for slug, name in slug_to_name.items():
    name_to_slugs.setdefault(name, []).append(slug)

  # 通过标题/描述反推出每个职业面板所属的神格
GOD_CN_TO_TYPE: Dict[str, str] = {
    "巨力之神": "strength",
    "狩猎之神": "dexterity",
    "知识之神": "intelligence",
    "征战之神": "war",
    "欺诈之神": "trickery",
    "机械之神": "machine",
  }

GOD_TYPE_ORDER: Dict[str, int] = {
  "strength": 0,
  "dexterity": 1,
  "intelligence": 2,
  "war": 3,
  "trickery": 4,
  "machine": 5,
}

  lines = [ln.strip() for ln in content.splitlines()]
  slug_god_type: Dict[str, str] = {}

  # 先直接把「巨力之神 / 狩猎之神 ...」这些神格本体映射到自身 godType
  for god_cn, god_type in GOD_CN_TO_TYPE.items():
    if god_cn in name_to_slugs:
      for slug in name_to_slugs[god_cn]:
        slug_god_type[slug] = god_type

  # 再通过「勇者 / 巨力之神的传承」这类描述，反推出其余面板的 godType
  for idx, line in enumerate(lines):
    if not line or line not in name_to_slugs:
      continue

    next_line = ""
    for j in range(idx + 1, len(lines)):
      if lines[j]:
        next_line = lines[j]
        break

    if not next_line:
      continue

    # 优先根据描述中首次出现的神格名识别所属神格：
    # 若描述中同时出现多个神格（例如「征战之神的侍者，融合巨力之神力」），
    # 以文本中首次出现的那个视为所属神格（这里是征战之神）。
    candidates: list[tuple[int, str]] = []
    for god_cn in GOD_CN_TO_TYPE.keys():
      idx_pos = next_line.find(god_cn)
      if idx_pos != -1:
        candidates.append((idx_pos, god_cn))

    if candidates:
      candidates.sort(key=lambda t: t[0])
      main_god_name = candidates[0][1]
      god_type = GOD_CN_TO_TYPE[main_god_name]
      for slug in name_to_slugs[line]:
        slug_god_type[slug] = god_type
      continue

  index: List[Dict] = []

  for slug, name in slug_to_name.items():
    god_type = slug_god_type.get(slug)
    # 未能从正文中归类的，先跳过，避免弄错分组
    if not god_type:
      continue

    is_god_root = slug.startswith("God_of_") or slug.startswith("Goddess_of_")
    entry_type = "panel"  # 统一按面板处理，是否神格根节点由 isGodRoot 标记

    index.append(
      {
        "slug": slug,
        "id": slug.lower(),
        "name": name,
        "type": entry_type,
        "godType": god_type,
        "sourceFile": f"{slug}.json",
        "isGodRoot": is_god_root,
      }
    )

  # 根据正文出现顺序为每个 godType 建立面板顺序
  god_orders: Dict[str, list[str]] = {gt: [] for gt in GOD_TYPE_ORDER.keys()}
  for line in lines:
    if not line or line not in name_to_slugs:
      continue
    for slug in name_to_slugs[line]:
      god_type = slug_god_type.get(slug)
      if not god_type:
        continue
      arr = god_orders.setdefault(god_type, [])
      if slug not in arr:
        arr.append(slug)

  # 写回 order 字段
  for e in index:
    gt = e["godType"]
    order_list = god_orders.get(gt, [])
    try:
      e["order"] = order_list.index(e["slug"])
    except ValueError:
      e["order"] = len(order_list)

  # 按神格顺序 + 面板顺序排序，使前端渲染顺序与官网一致
  index.sort(
    key=lambda e: (
      GOD_TYPE_ORDER.get(e["godType"], 99),
      e.get("order", 0),
    )
  )

  with open(OUTPUT_INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

  print(f"已生成职业/神格索引: {OUTPUT_INDEX_FILE}（共 {len(index)} 条）")


if __name__ == "__main__":
  build_profession_index()

