#!/usr/bin/env python3
"""fix_logs"""

import re

with open(r'C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix log messages
content = content.replace('self.log(f"Обновление ConfigCmeLocal.json...")', 'self.log("Обновление ConfigCmeLocal.json...", "info")')
content = content.replace('self.log(f"Обновление SignalPrinter.json...")', 'self.log("Обновление SignalPrinter.json...", "info")')

# Add "Загрузка конфига" message
content = content.replace(
    '# Update Instruments.json',
    '''# Загрузка конфигурации
                            config_file_path = f"{config_history_path}/{interval['config_file']}"
                            self.log(f"Загрузка конфига: {config_file_path}", "info")
                            
                            # Update Instruments.json'''
)

# Fix "Запуск FeaturesCalculator..." to include interval
content = content.replace(
    'self.log("Запуск FeaturesCalculator...", "info")',
    'self.log(f"Запуск FeaturesCalculator для интервала {interval["start"].date()} - {interval["end"].date()}...", "info")'
)

with open(r'C:/Users/user/Documents/TradingTools/modules/generate_signals.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done')
