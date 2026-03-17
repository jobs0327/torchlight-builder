import json
import re

# 读取抓取的数据
with open('/Users/huangqian/Desktop/project/torchlight/data/The_Brave.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

content = data[0]['content']

# 提取天赋信息
talents = []

# 匹配天赋条目
# 格式: 天赋名称\n点数\n0/最大点数\n描述
pattern = r'(小型天赋|中型天赋|传奇中型天赋)\s+(\d+)pts\s+0/(\d+)\s+([^\n]+(?:\n[^\n]+)?)'

matches = re.findall(pattern, content)
print(f"找到 {len(matches)} 个天赋")

for i, (talent_type, points, max_points, description) in enumerate(matches):
    talent_type_map = {
        '小型天赋': 'small',
        '中型天赋': 'notable',
        '传奇中型天赋': 'legendary'
    }
    
    talents.append({
        'id': f'talent_{i}',
        'type': talent_type_map.get(talent_type, 'small'),
        'requiredPoints': int(points),
        'maxPoints': int(max_points),
        'description': description.strip().replace(' （神格生效上限：1）', ''),
        'name': description.strip().split('\n')[0][:30]  # 取描述的前30字符作为名称
    })

# 打印前10个天赋
for t in talents[:10]:
    print(f"{t['type']:10} | {t['requiredPoints']:2}pts | {t['name']}")

# 按requiredPoints分组
from collections import defaultdict
by_points = defaultdict(list)
for t in talents:
    by_points[t['requiredPoints']].append(t)

print("\n按点数分组:")
for points in sorted(by_points.keys()):
    print(f"  {points}pts: {len(by_points[points])} 个天赋")
