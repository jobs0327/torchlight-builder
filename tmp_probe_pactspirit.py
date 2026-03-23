from html import unescape
import re
from urllib.request import Request, urlopen

h = urlopen(
    Request("https://tlidb.com/cn/Pactspirit", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=90,
).read().decode("utf-8", "replace")

card_re = re.compile(
    r'<div class="d-flex border-top rounded">'
    r'<div class="flex-shrink-0">'
    r'<img src="([^"]+)"[^>]*>'
    r'</div>'
    r'<div class="flex-grow-1[^"]*">'
    r'<a[^>]*href="([^"]+)"[^>]*class="([^"]*)"[^>]*>([^<]+)</a>'
    r"(.*?)</div>\s*</div>\s*</div>",
    re.S,
)

def strip_tags(s: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", unescape(s)).strip()


for i, m in enumerate(card_re.finditer(h)):
    if i >= 1:
        break
    icon, pid, rcls, name, body = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    mods = re.findall(r'<div class="modifier">(.*?)</div>', body, re.S)
    lines = [strip_tags(x) for x in mods]
    print(pid, unescape(name).strip(), rcls, len(lines), lines[:2])
print("total cards", len(card_re.findall(h)))
