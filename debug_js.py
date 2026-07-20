import re
from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')

# Check response.ok
if 'response.ok' in html:
    print('Has response.ok check')
else:
    print('MISSING response.ok check')

# Find all getElementById calls
ids_used = set(re.findall(r"getElementById\('([^']+)'\)", html))
print('DOM IDs used in JS:', sorted(ids_used))

# Find all id= in HTML
ids_defined = set(re.findall(r'id="([^"]+)"', html))
print('DOM IDs in HTML:', sorted(ids_defined))

# Check for missing IDs
missing = ids_used - ids_defined
if missing:
    print('MISSING IDs:', missing)
else:
    print('All IDs accounted for')

# Check for JS syntax issues - unmatched braces
script_start = html.find('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]
opens = script.count('{')
closes = script.count('}')
print(f'\nBraces: {{ = {opens}, }} = {closes}')
if opens != closes:
    print('WARNING: Unbalanced braces!')
else:
    print('Braces balanced')

# Check for potential issues with fetch path
if "fetch('data/xsmn_web.json')" in html:
    print('\nFetch path: data/xsmn_web.json (relative)')
elif 'fetch("data/xsmn_web.json")' in html:
    print('\nFetch path: data/xsmn_web.json (relative, double quotes)')
