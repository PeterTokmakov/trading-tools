#!/usr/bin/env python3
"""fix_env_encoding"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read file
with open('C:/Users/user/Documents/TradingTools/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if already has PYTHONIOENCODING
if 'PYTHONIOENCODING' in content:
    print('Already has PYTHONIOENCODING')
else:
    # Add after imports
    import_line = 'import sys'
    new_content = content.replace(import_line, import_line + '\nimport os\nos.environ["PYTHONIOENCODING"] = "utf-8"', 1)
    
    # Write back
    with open('C:/Users/user/Documents/TradingTools/app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print('Fixed!')
