import re

with open(r'C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove DEBUG logs
content = re.sub(r'\s*self\.log\(f"\[DEBUG\].*?\n', '', content)
content = re.sub(r"\s*self\.log\(f'\[DEBUG\].*?\n", '', content)

# Remove debug.log writing
lines = content.split('\n')
new_lines = []
skip_debug = False
for line in lines:
    if '# Also write to debug log file' in line:
        skip_debug = True
        continue
    if skip_debug and ('debug.log' in line or 'f.write' in line):
        if 'f.write' in line:
            skip_debug = False
        continue
    if '[DEBUG]' not in line:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open(r'C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
