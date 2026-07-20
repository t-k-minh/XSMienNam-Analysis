from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')
script_start = html.find('<script>') + len('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]

lines = script.split('\n')
depth = 0

# Find all top-level function starts and their expected end
import re

# Track depth changes per line
for i, line in enumerate(lines):
    old_depth = depth
    for ch in line:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
    if depth != old_depth and depth > 0 and old_depth == 0:
        # A new block opened at top level
        func_match = re.search(r'function\s+(\w+)', line)
        name = func_match.group(1) if func_match else '<anon>'
        print(f'L{i+1}: OPEN  {name:25s}  depth 0 -> {depth}')

    if old_depth > 0 and depth == 0:
        # A block closed back to top level
        print(f'L{i+1}: CLOSE                   depth {old_depth} -> 0')

print(f'\nFinal depth: {depth}')
