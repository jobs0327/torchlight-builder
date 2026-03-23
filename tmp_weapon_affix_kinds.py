"""List unique affixType on weapon craftedAffix JSON files."""
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path("torchlight-builder/src/data/equipment/craftedAffixes")
weaponish = re.compile(
    r"Sword|Axe|Hammer|Claw|Dagger|Wand|Rod|Scepter|Cane|Staff|Bow|Crossbow|Musket|Pistol|Cannon|Shield|Fire_Cannon|Tin_Staff|Cudgel",
    re.I,
)
seen: set[str] = set()
for p in sorted(root.glob("*.json")):
    if p.name == "index.json":
        continue
    if not weaponish.search(p.stem):
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    for m in data.get("modifiers") or []:
        t = m.get("affixType")
        if isinstance(t, str):
            seen.add(t)

for t in sorted(seen):
    if "塔" in t or "Tower" in t or "tower" in t.lower():
        print(">>>", t)
    elif "高" in t:
        print("...", t)

print("--- total unique types", len(seen))
