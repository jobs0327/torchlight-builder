from html import unescape
import re
from urllib.request import Request, urlopen

url = "https://tlidb.com/cn/TOWER_Sequence"
h = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode(
    "utf-8", "replace"
)
start = h.find("<tbody>")
end = h.find("</tbody>", start)
sub = h[start:end]
ROW = re.compile(r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", re.S | re.I)


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", t).strip()


seen: set[str] = set()
for m in ROW.finditer(sub):
    eff, src = m.group(1), m.group(2)
    if "data-modifier-id" not in eff:
        continue
    seen.add(strip_html(src))

for s in sorted(seen):
    print(s.encode("unicode_escape").decode("ascii"))
