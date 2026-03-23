import json
import re
from pathlib import Path

root = Path("torchlight-builder/src/data/equipment/craftedAffixes")
pat = re.compile(
    r"Sword|Axe|Hammer|Claw|Dagger|Wand|Rod|Scepter|Cane|Staff|Bow|Crossbow|Musket|Pistol|Cannon|Shield|Fire_Cannon|Tin_Staff|Cudgel",
    re.I,
)
seen: set[str] = set()
for p in sorted(root.glob("*.json")):
    if p.name == "index.json" or not pat.search(p.stem):
        continue
    for m in json.loads(p.read_text(encoding="utf-8")).get("modifiers") or []:
        t = m.get("affixType")
        if isinstance(t, str):
            seen.add(t)

out = Path("tmp_weapon_affix_types.txt")
out.write_text("\n".join(sorted(seen)), encoding="utf-8")
for t in sorted(seen):
    if "\u5854" in t or "\u9ad8\u5854" in t:
        print("TOWERish:", t.encode("unicode_escape").decode("ascii"))
