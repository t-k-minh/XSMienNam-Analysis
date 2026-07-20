"""Check DATA array in HTML."""
from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')

# Check the DATA array size
data_start = html.find('const DATA = [')
data_end = html.find('];', data_start)
if data_start != -1 and data_end != -1:
    data_size = data_end - data_start
    print(f'DATA array size: {data_size} chars ({data_size/1024/1024:.2f} MB)')
    
    # Check if there are any obvious syntax errors
    data_str = html[data_start + len('const DATA = '):data_end]
    
    # Check for unbalanced quotes
    single_quotes = data_str.count("'")
    double_quotes = data_str.count('"')
    print(f'Single quotes: {single_quotes}')
    print(f'Double quotes: {double_quotes}')
    
    if single_quotes % 2 != 0:
        print('WARNING: Odd number of single quotes')
    if double_quotes % 2 != 0:
        print('WARNING: Odd number of double quotes')
else:
    print('DATA array not found')
