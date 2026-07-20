"""Check JavaScript in HTML for errors."""
import re
from pathlib import Path

html = Path('readme.html').read_text(encoding='utf-8')

# Find script content
script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if script_match:
    script = script_match.group(1)
    
    # Check for common issues
    issues = []
    
    # Check for unbalanced braces
    open_braces = script.count('{{')  # Python f-string doubles braces
    close_braces = script.count('}}')
    
    # Check for undefined variables
    if 'NaN' in script:
        issues.append('Contains NaN - possible number conversion issue')
    
    # Check for missing functions
    if 'renderResultTable' in script and 'function renderResultTable' not in script:
        issues.append('renderResultTable called but not defined')
    
    if issues:
        print('Issues found:')
        for issue in issues:
            print(f'  - {issue}')
    else:
        print('No obvious issues found in script')
    
    # Check first 500 chars of script
    print()
    print('Script starts with:')
    print(script[:500])
else:
    print('No script tag found')
