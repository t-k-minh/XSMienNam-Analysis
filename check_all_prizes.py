"""Check all prizes for leading zeros."""
import json
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

print('=== Kiem tra so 0 cho tat ca cac giai ===')
print()

# Check all prizes for 2026-07-16
day_data = [d for d in data if d['date'] == '2026-07-16']
for d in day_data[:3]:
    prov = d['province']
    print(f'{prov}:')
    print(f"  prize8 (2 so):  {d.get('prize8')} -> {len(str(d.get('prize8','')))} ky tu")
    print(f"  prize7 (3 so):  {d.get('prize7')} -> {len(str(d.get('prize7','')))} ky tu")
    print(f"  prize5 (4 so):  {d.get('prize5')} -> {len(str(d.get('prize5','')))} ky tu")
    print(f"  prize2 (5 so):  {d.get('prize2')} -> {len(str(d.get('prize2','')))} ky tu")
    print(f"  prize1 (5 so):  {d.get('prize1')} -> {len(str(d.get('prize1','')))} ky tu")
    print(f"  special (6 so): {d.get('special')} -> {len(str(d.get('special','')))} ky tu")
    print()
