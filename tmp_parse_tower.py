from html import unescape
import re
from urllib.request import Request, urlopen

url = "https://tlidb.com/cn/TOWER_Sequence"
h = urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read().decode(
    "utf-8", "replace"
)
# first table tbody in active tab
start = h.find("<tbody>")
end = h.find("</tbody>", start)
sub = h[start:end]
ROW = re.compile(r"<tr[^>]*>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>", re.S | re.I)
MOD = re.compile(r'data-modifier-id="(\d+)"')
TOOLTIP_RE = re.compile(
    r'data-bs-title="Tier:\s*(\d+)\s*,\s*Level:\s*(\d+)\s*,\s*Weight:\s*(\d+)"'
)


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    t = unescape(fragment)
    t = t.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", t).strip()


n = 0
samples = []
for m in ROW.finditer(sub):
    eff, src = m.group(1), m.group(2)
    if "data-modifier-id" not in eff:
        continue
    mid = MOD.search(eff)
    if not mid:
        continue
    plain = strip_html(eff)
    src_plain = strip_html(src)
    tt = TOOLTIP_RE.search(eff)
    tier = int(tt.group(1)) if tt else None
    seq = None
    if "\u9ad8\u9636\u5e8f\u5217" in plain:  # 高阶序列
        seq = "\u9ad8\u9636\u5e8f\u5217"
    elif "\u4e2d\u9636\u5e8f\u5217" in plain:  # 中阶序列
        seq = "\u4e2d\u9636\u5e8f\u5217"
    n += 1
    if len(samples) < 5:
        samples.append((mid.group(1), tier, seq, src_plain[:20], plain[:100]))

print("rows", n)
for s in samples:
    print(s)
