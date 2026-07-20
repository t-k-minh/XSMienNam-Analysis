"""Check data for specific dates."""
import json
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

# Check data for 2026-07-11
print('Data for 2026-07-11:')
day_data = [d for d in data if d['date'] == '2026-07-11']
for d in day_data:
    print(f"  {d['province']}: special={d.get('special')}")
    print(f"    prize1={d.get('prize1')}, prize2={d.get('prize2')}")
    print(f"    prize3_1={d.get('prize3_1')}, prize3_2={d.get('prize3_2')}")
    print(f"    prize4_1={d.get('prize4_1')}, prize4_2={d.get('prize4_2')}")
    print()

# Check schedule for 11/07/2026
from datetime import date
d = date(2026, 7, 11)
print(f"11/07/2026 is: {['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'][d.weekday()]}")
print()

# Check what provinces should be on that day
SCHEDULE = {
    0: ['TGI', 'KG', 'DL'],       # Sunday
    1: ['TTP', 'DT', 'CM'],        # Monday
    2: ['BTR', 'VT', 'BL'],        # Tuesday
    3: ['DNA', 'CT', 'ST'],        # Wednesday
    4: ['TNI', 'AG', 'BTH'],       # Thursday
    5: ['VL', 'BD', 'TV'],         # Friday
    6: ['HCM', 'LA', 'BP', 'HGG']  # Saturday
}

print(f"Expected provinces for Saturday: {SCHEDULE[6]}")
print(f"Actual provinces: {[d['province'] for d in day_data]}")
