"""Check data for 16/07/2026."""
import json
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

# Check data for 2026-07-16
print('Data for 2026-07-16:')
day_data = [d for d in data if d['date'] == '2026-07-16']
for d in day_data:
    print(f"\n{d['province']}:")
    print(f"  prize8 (Tam): {d.get('prize8')}")
    print(f"  prize7 (Bay): {d.get('prize7')}")
    print(f"  prize6_1 (Sau 1): {d.get('prize6_1')}")
    print(f"  prize6_2 (Sau 2): {d.get('prize6_2')}")
    print(f"  prize6_3 (Sau 3): {d.get('prize6_3')}")
    print(f"  prize5 (Nam): {d.get('prize5')}")
    print(f"  prize4_1 (Tu 1): {d.get('prize4_1')}")
    print(f"  prize4_2 (Tu 2): {d.get('prize4_2')}")
    print(f"  prize4_3 (Tu 3): {d.get('prize4_3')}")
    print(f"  prize4_4 (Tu 4): {d.get('prize4_4')}")
    print(f"  prize3_1 (Ba 1): {d.get('prize3_1')}")
    print(f"  prize3_2 (Ba 2): {d.get('prize3_2')}")
    print(f"  prize2 (Nhi): {d.get('prize2')}")
    print(f"  prize1 (Nhat): {d.get('prize1')}")
    print(f"  special (Dac biet): {d.get('special')}")
