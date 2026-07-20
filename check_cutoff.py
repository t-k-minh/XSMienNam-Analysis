"""Check cutoff logic."""
import json
from pathlib import Path

data = json.loads(Path('data/xsmn.json').read_text())

# Check TP.HCM data around 13/07 and 20/07
hcm_data = [d for d in data if d['province'] == 'HCM']
hcm_data.sort(key=lambda x: x['date'])

print('TP.HCM data around 13/07:')
for d in hcm_data:
    if '2026-07-10' <= d['date'] <= '2026-07-15':
        print(f"  {d['date']}: special={d.get('special')}")

print()
print('TP.HCM data around 20/07:')
for d in hcm_data:
    if '2026-07-17' <= d['date'] <= '2026-07-22':
        print(f"  {d['date']}: special={d.get('special')}")

# Simulate cutoff logic
print()
print('Simulating cutoff for 13/07:')
cutoff = '2026-07-13'
filtered = [d for d in hcm_data if d['date'] < cutoff]
print(f"  Records before {cutoff}: {len(filtered)}")

print()
print('Simulating cutoff for 20/07:')
cutoff = '2026-07-20'
filtered = [d for d in hcm_data if d['date'] < cutoff]
print(f"  Records before {cutoff}: {len(filtered)}")
