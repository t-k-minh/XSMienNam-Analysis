"""Verify HTML file."""
from pathlib import Path
import json
import re

html = Path('readme.html').read_text(encoding='utf-8')

print(f'HTML size: {len(html)} bytes')

# Check structure
checks = [
    ('<html', 'HTML tag'),
    ('</html>', 'HTML close'),
    ('<script>', 'Script tag'),
    ('</script>', 'Script close'),
    ('const DATA', 'DATA array'),
]

for pattern, name in checks:
    found = pattern in html
    print(f'{name}: {"OK" if found else "MISSING"}')

# Try to parse DATA
match = re.search(r'const DATA = (\[.*?\]);', html, re.DOTALL)
if match:
    data_str = match.group(1)
    print(f'\nDATA array: {len(data_str)} chars')
    try:
        data = json.loads(data_str)
        print(f'Valid JSON: {len(data)} records')
        print(f'First record: {data[0]}')
    except json.JSONDecodeError as e:
        print(f'JSON ERROR: {e}')
else:
    print('DATA array NOT found')
