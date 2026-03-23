from urllib.request import Request, urlopen
import re

h = urlopen(
    Request("https://tlidb.com/cn/Pactspirit", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=90,
).read().decode("utf-8")
print(sorted(set(re.findall(r"item_rarity[0-9]+", h))))
