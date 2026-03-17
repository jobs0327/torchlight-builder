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

  # 通过「勇者 / 巨力之神的传承」这类描述，反推出每个职业面板所属的神格
  GOD_CN_TO_TYPE: Dict[str, str] = {
    "巨力之神": "strength",
    "狩猎之神": "dexterity",
    "知识之神": "intelligence",
    "征战之神": "war",
    "欺诈之神": "trickery",
    "机械之神": "machine",
  }

  lines = [ln.strip() for ln in content.splitlines()]
  slug_god_type: Dict[str, str] = {}

  for idx, line in enumerate(lines):
    if not line or line not in name_to_slugs:
      continue

    # 向后寻找下一条非空行，通常是「巨力之神的传承」之类的描述
    next_line = ""
    for j in range(idx + 1, len(lines)):
      if lines[j]:
        next_line = lines[j]
        break

    if not next_line:
      continue

    for god_cn, god_type in GOD_CN_TO_TYPE.items():
      if god_cn in next_line:
        for slug in name_to_slugs[line]:
          slug_god_type[slug] = god_type
        break

  # 将 data 目录下已抓取的页面作为「可用的职业/神格」
  available_files = {
    os.path.splitext(fname)[0]: fname
    for fname in os.listdir(DATA_DIR)
    if fname.endswith(".json")
  }

  index: List[Dict] = []

  for slug, name in slug_to_name.items():
    if slug not in available_files:
      # 尚未抓取到对应页面，暂不纳入索引
      continue

    god_type = slug_god_type.get(slug)
    # 未能从正文中归类的，先跳过，避免弄错分组
    if not god_type:
      continue

    entry_type = "god" if slug.startswith("God_of_") or slug.startswith("Goddess_of_") else "panel"

    index.append(
      {
        "slug": slug,
        "id": slug.lower(),
        "name": name,
        "type": entry_type,
        "godType": god_type,
        "sourceFile": available_files[slug],
      }
    )

  # 按 godType + type + name 排序，方便阅读
  index.sort(key=lambda e: (e["godType"], e["type"], e["name"]))

  with open(OUTPUT_INDEX_FILE, "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

  print(f"已生成职业/神格索引: {OUTPUT_INDEX_FILE}（共 {len(index)} 条）")


if __name__ == "__main__":
  build_profession_index()

