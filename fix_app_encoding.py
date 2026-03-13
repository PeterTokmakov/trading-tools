#!/usr/bin/env python3
"""fix_app_encoding"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read file
with open('C:/Users/user/Documents/TradingTools/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already has reconfigure
if 'sys.stdout.reconfigure' in content:
    print('Already has reconfigure')
else:
    # Add after imports
    import_line = 'import sys'
    new_content = content.replace(import_line, import_line + '\nsys.stdout.reconfigure(encoding=\'utf-8\')', 1)
    
    # Write back
    with open('C:/Users/user/Documents/TradingTools/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('Fixed!')
