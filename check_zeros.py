"""Check leading zeros in data."""
import json
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

print('Data for 2026-07-16 (Tây Ninh):')
day_data = [d for d in data if d['date'] == '2026-07-16' and d['province'] == 'TNI']
if day_data:
    d = day_data[0]
    print(f"  prize8: {d.get('prize8')}")
    print(f"  prize7: {d.get('prize7')}")
    print(f"  prize6_1: {d.get('prize6_1')}")
    print(f"  prize5: {d.get('prize5')}")
    print(f"  prize2: {d.get('prize2')}")
    print(f"  prize1: {d.get('prize1')}")
    print(f"  special: {d.get('special')}")

print()
print('Data for 2026-07-16 (An Giang):')
day_data = [d for d in data if d['date'] == '2026-07-16' and d['province'] == 'AG']
if day_data:
    d = day_data[0]
    print(f"  prize2: {d.get('prize2')}")
    print(f"  prize1: {d.get('prize1')}")
    print(f"  special: {d.get('special')}")
