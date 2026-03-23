from html import unescape
import re
from urllib.request import Request, urlopen

ROW_RE = re.compile(
    r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
    re.S | re.I,
)


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", unescape(fragment)).strip()


def probe(url: str) -> None:
    h = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode(
        "utf-8", "replace"
    )
    for s in ["\u9ad8\u5854\u8bcd\u7f00", "Tower", "tower"]:  # 高塔词缀 / Tower
        print(url, repr(s), h.count(s))
    start = h.find('<div id="\u8bcd\u7f00"')  # 词缀
    if start < 0:
        start = h.find('<div id="Affix"')
    end = -1
    for m in [
        '<div id="Item"',
        '<div id="\u4f20\u5947\u88c5\u5907"',  # 传奇装备
        '<div id="Legendary"',
    ]:
        j = h.find(m, start + 20)
        if j >= 0 and (end < 0 or j < end):
            end = j
    if end < 0:
        end = len(h)
    sub = h[start:end]
    n = 0
    kinds: dict[str, int] = {}
    for row in ROW_RE.finditer(sub):
        if "data-modifier-id" not in row.group(1):
            continue
        n += 1
        k = strip_html(row.group(3))
        kinds[k] = kinds.get(k, 0) + 1
    print("rows_with_modifier", n, "unique_types", len(kinds))
    for k, v in sorted(kinds.items(), key=lambda x: (-x[1], x[0])):
        if "\u5854" in k or "Tower" in k or "tower" in k.lower():
            print("TOWER_MATCH", v, k)
    print("--- all types ---")
    for k, v in sorted(kinds.items(), key=lambda x: (-x[1], x[0])):
        print(v, k.encode("unicode_escape").decode("ascii"))


urls = [
    "https://tlidb.com/cn/One-Handed_Sword",
    "https://tlidb.com/cn/Staff",
    "https://tlidb.com/cn/Bow",
    "https://tlidb.com/cn/Wand",
    "https://tlidb.com/cn/Two-Handed_Sword",
    "https://tlidb.com/cn/Pistol",
]
for u in urls:
    probe(u)
