from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')
script_start = html.find('<script>') + len('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]

# Track brace depth line by line
lines = script.split('\n')
depth = 0
for i, line in enumerate(lines):
    for ch in line:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
    if depth < 0:
        print(f'Line {i+1}: depth went negative ({depth})')
        print(f'  {line.strip()}')

print(f'\nFinal depth: {depth}')
if depth != 0:
    # Find where depth should end but doesn't
    depth = 0
    for i, line in enumerate(lines):
        prev_depth = depth
        for ch in line:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
        # After last line at depth 0, check what's missing
        if i == len(lines) - 1 and depth != 0:
            print(f'Script ends at depth {depth} on line {i+1}')
            print(f'  Last line: {line.strip()}')

    # More detailed: find depth 0 transitions
    depth = 0
    last_zero_line = -1
    for i, line in enumerate(lines):
        for ch in line:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
        if depth == 0:
            last_zero_line = i

    print(f'\nLast line at depth 0: line {last_zero_line+1}')
    print(f'Content: {lines[last_zero_line].strip() if last_zero_line >= 0 else "none"}')
    print(f'Next line ({last_zero_line+2}): {lines[last_zero_line+1].strip() if last_zero_line+1 < len(lines) else "none"}')
