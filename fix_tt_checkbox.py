#!/usr/bin/env python3
"""fix_tt_checkbox"""

with open('C:/Users/user/Documents/TradingTools/static/style.css', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix checkbox touch targets
content = content.replace(
    '.checkbox {\n    display: flex;\n    align-items: center;\n    gap: var(--space-2);\n    cursor: pointer;\n    color: var(--text-primary);\n    font-size: 0.85rem;\n    min-height: 36px;',
    '.checkbox {\n    display: flex;\n    align-items: center;\n    gap: var(--space-2);\n    cursor: pointer;\n    color: var(--text-primary);\n    font-size: 0.85rem;\n    min-height: 44px;'
)

# Fix mobile checkbox
content = content.replace(
    '    .checkbox {\n        min-height: 40px;\n        padding: var(--space-3) var(--space-4);\n    }',
    '    .checkbox {\n        min-height: 48px;\n        padding: var(--space-3) var(--space-4);\n    }'
)

# Fix checkbox input size on mobile
content = content.replace(
    '    .checkbox input[type="checkbox"] {\n        width: 18px;\n        height: 18px;\n    }',
    '    .checkbox input[type="checkbox"] {\n        width: 20px;\n        height: 20px;\n    }'
)

with open('C:/Users/user/Documents/TradingTools/static/style.css', 'w', encoding='utf-8') as f:
    f.write(content)
print('CSS updated')
