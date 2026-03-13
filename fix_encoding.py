#!/usr/bin/env python3
"""fix_encoding"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read file
with open('C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count occurrences
count = content.count('.decode()')
print(f'Found {count} occurrences of .decode()')

# Replace .decode() with .decode('utf-8')
new_content = content.replace('.decode()', ".decode('utf-8')")

# Write back
with open('C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Fixed!')
