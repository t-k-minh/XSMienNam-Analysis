from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')
script_start = html.find('<script>') + len('<script>')
script_end = html.find('</script>')
script = html[script_start:script_end]

# Find each function and its brace balance
import re
funcs = list(re.finditer(r'function\s+(\w+)', script))

lines = script.split('\n')

# Track depth changes
depth = 0
depth_at_line = []
for i, line in enumerate(lines):
    for ch in line:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
    depth_at_line.append(depth)

# Find functions where depth doesn't return to 0
current_func = None
func_start_line = 0
for fi, f in enumerate(funcs):
    name = f.group(1)
    line_num = script[:f.start()].count('\n')
    func_start_depth = depth_at_line[line_num] if line_num < len(depth_at_line) else 0
    
    # Find next function or end
    if fi + 1 < len(funcs):
        next_line = script[:funcs[fi+1].start()].count('\n')
    else:
        next_line = len(lines) - 1
    
    end_depth = depth_at_line[min(next_line, len(depth_at_line)-1)]
    
    if end_depth != 0:
        print(f'FUNC {name} (line {line_num+1}): starts at depth {func_start_depth}, ends at depth {end_depth}')
        # Show lines near end
        for l in range(max(0, next_line-3), min(len(lines), next_line+2)):
            print(f'  L{l+1} [depth={depth_at_line[l]}]: {lines[l].rstrip()}')
        print()
