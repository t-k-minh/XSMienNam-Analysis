from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')
script_start = html.find('<script>') + len('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]

lines = script.split('\n')
depth = 0

for i, line in enumerate(lines):
    for j, ch in enumerate(line):
        if ch == '{':
            old = depth
            depth += 1
            if old == 0:
                print(f'L{i+1} col{j+1}: OPEN  depth {old} -> {depth}')
        elif ch == '}':
            old = depth
            depth -= 1
            if depth == 0:
                print(f'L{i+1} col{j+1}: CLOSE depth {old} -> {depth}')

print(f'\nFinal depth: {depth}')
