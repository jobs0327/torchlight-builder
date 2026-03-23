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


url = "https://tlidb.com/cn/One-Handed_Sword"
h = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode(
    "utf-8", "replace"
)
start = h.find('<div id="词缀"')
if start < 0:
    start = h.find('<div id="Affix"')
item = h.find('<div id="Item"', start)
sub = h[start:item]
kinds: dict[str, int] = {}
for m in ROW_RE.finditer(sub):
    if "data-modifier-id" not in m.group(1):
        continue
    k = strip_html(m.group(3))
    kinds[k] = kinds.get(k, 0) + 1
for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
    if "塔" in k or "Tower" in k or "tower" in k.lower():
        print("TOWER?", v, k)
print("--- all types ---")
for k, v in sorted(kinds.items(), key=lambda x: (-x[1], x[0])):
    print(v, k)
