from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')
script_start = html.find('<script>') + len('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]

lines = script.split('\n')

# Focus on calcScores function (L53 to where depth returns to 0 or end)
depth = 0
for i, line in enumerate(lines):
    if i < 52:  # skip before calcScores
        for ch in line:
            if ch == '{': depth += 1
            elif ch == '}': depth -= 1
        continue

    old_depth = depth
    for ch in line:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
    print(f'L{i+1} depth {old_depth} -> {depth}: {line[:120]}')

    if depth == 0 and old_depth > 0:
        print('  ^^^ calcScores closed here')
        break
