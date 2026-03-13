#!/usr/bin/env python3
"""
Серверный скрипт для обработки файлов сигналов.
Выполняется на удалённом сервере.
"""

import json
import os
import re
import sys
from datetime import datetime


def get_month_order(month_code, year_suffix):
    """Получение порядкового номера месяца для сортировки"""
    month_codes = {
        'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
        'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12
    }
    month = month_codes.get(month_code, 0)
    if len(year_suffix) == 1:
        year = 2020 + int(year_suffix)
    else:
        year = 2000 + int(year_suffix)
    return year * 12 + month


def get_instrument_mapping(config_json):
    """Получение маппинга signal_id -> название инструмента"""
    mapping = {
        2: 'GOLD',
        3: 'SILV',
        5: 'SPYF',
        7: 'PLT',
        8: 'NASD',
        9: 'PLD',
    }
    
    all_instruments = []
    for key, instruments in config_json.items():
        if isinstance(instruments, list):
            all_instruments.extend(instruments)
    
    # NG (signal_id 1, 6, 13)
    ng_instruments = []
    for instr in all_instruments:
        signal_id = instr.get('SignalId')
        symbol = instr.get('Symbol', '')
        if signal_id in [1, 6, 13] and symbol.startswith('NG'):
            month_code = symbol[2]
            year_suffix = symbol[3:]
            order = get_month_order(month_code, year_suffix)
            ng_instruments.append((signal_id, order))
    
    ng_instruments.sort(key=lambda x: x[1])
    ng_names = ['NG_FIRST', 'NG_SECOND', 'NG_THIRD']
    for i, (signal_id, _) in enumerate(ng_instruments):
        if i < len(ng_names):
            mapping[signal_id] = ng_names[i]
    
    # BZ (signal_id 4, 14)
    bz_instruments = []
    for instr in all_instruments:
        signal_id = instr.get('SignalId')
        symbol = instr.get('Symbol', '')
        if signal_id in [4, 14] and symbol.startswith('BZ'):
            month_code = symbol[2]
            year_suffix = symbol[3:]
            order = get_month_order(month_code, year_suffix)
            bz_instruments.append((signal_id, order))
    
    bz_instruments.sort(key=lambda x: x[1])
    bz_names = ['BR_FIRST', 'BR_SECOND']
    for i, (signal_id, _) in enumerate(bz_instruments):
        if i < len(bz_names):
            mapping[signal_id] = bz_names[i]
    
    return mapping


def parse_config_filename(filename):
    """Парсинг даты из имени файла формата dd-mm-yyyy.json"""
    match = re.match(r'(\d{2})-(\d{2})-(\d{4})\.json', filename)
    if match:
        day, month, year = match.groups()
        return datetime(int(year), int(month), int(day)).date()
    return None


def load_config_files(config_history_path):
    """Загрузка списка конфигов с датами"""
    config_files = []
    if not os.path.exists(config_history_path):
        return config_files
    
    for f in os.listdir(config_history_path):
        date = parse_config_filename(f)
        if date:
            config_files.append((date, f))
    
    config_files.sort(key=lambda x: x[0])
    return config_files


def clean_json_string(json_str):
    """Очистка JSON от комментариев и trailing commas"""
    json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
    json_str = json_str.replace('\r\n', '\n').replace('\r', '\n')
    json_str = re.sub(r'(?<!:)//.*?(?=\n|$)', '', json_str)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    return json_str


def main():
    if len(sys.argv) != 3:
        print("ERROR: Usage: process_signals_server.py <signal_folder> <config_history_path>")
        sys.exit(1)
    
    signal_folder = sys.argv[1].rstrip('/')
    config_history_path = sys.argv[2]
    
    temp_fixed_path = f"{signal_folder}/temp_moment_fixed"
    
    # Проверяем существование папки
    if not os.path.exists(temp_fixed_path):
        print(f"ERROR: Папка не существует: {temp_fixed_path}")
        sys.exit(1)
    
    # Загружаем конфиги
    config_files = load_config_files(config_history_path)
    if not config_files:
        print(f"ERROR: Не найдены файлы конфигов в {config_history_path}")
        sys.exit(1)
    
    print(f"INFO: Загружено {len(config_files)} конфигов")
    
    # Получаем список файлов сигналов
    signal_files = [f for f in os.listdir(temp_fixed_path) if '_signal' in f]
    
    if not signal_files:
        print("WARNING: Нет файлов сигналов для обработки")
        sys.exit(0)
    
    total_files = len(signal_files)
    print(f"INFO: Найдено {total_files} файлов сигналов")
    
    # Кэш конфигов
    config_cache = {}
    processed_count = 0
    error_count = 0
    
    for signal_file in signal_files:
        try:
            # Парсим имя файла
            match = re.match(r'(\d{4}-\d{2}-\d{2})_(\d+)_signal', signal_file)
            if not match:
                print(f"SKIP: Неверный формат: {signal_file}")
                continue
            
            file_date_str = match.group(1)
            signal_id = int(match.group(2))
            file_date = datetime.strptime(file_date_str, '%Y-%m-%d').date()
            
            # Получаем конфиг
            if file_date_str not in config_cache:
                applicable_config = None
                for config_date, config_file in config_files:
                    if config_date <= file_date:
                        applicable_config = config_file
                    else:
                        break
                
                if applicable_config:
                    config_path = os.path.join(config_history_path, applicable_config)
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    cleaned = clean_json_string(content)
                    config_cache[file_date_str] = json.loads(cleaned)
                else:
                    print(f"SKIP: Нет конфига для {file_date_str}")
                    continue
            
            config_json = config_cache[file_date_str]
            mapping = get_instrument_mapping(config_json)
            
            instrument_name = mapping.get(signal_id)
            if not instrument_name:
                print(f"SKIP: Нет маппинга для signal_id={signal_id}")
                continue
            
            # Читаем и обрабатываем файл
            source_path = os.path.join(temp_fixed_path, signal_file)
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            output_lines = []
            for line in content.strip().split('\n'):
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) >= 6:
                    output_lines.append(f"{parts[2]} {parts[3]} {parts[5]}")
            
            if not output_lines:
                print(f"SKIP: Пустой результат для {signal_file}")
                continue
            
            # Создаём папку и записываем файл
            dest_folder = f"{signal_folder}/{instrument_name}"
            os.makedirs(dest_folder, exist_ok=True)
            
            # Формируем имя файла: дата_signal (без signal_id)
            dest_filename = f"{file_date_str}_signal"
            dest_path = os.path.join(dest_folder, dest_filename)
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines) + '\n')
            
            processed_count += 1
            
            # Выводим прогресс каждые 5 файлов
            if processed_count % 5 == 0:
                print(f"PROGRESS: {processed_count}/{total_files}")
                sys.stdout.flush()
            
        except Exception as e:
            error_count += 1
            print(f"ERROR: {signal_file} - {str(e)}")
    
    print(f"PROGRESS: {processed_count}/{total_files}")
    print(f"DONE: Обработано {processed_count}/{total_files}, ошибок: {error_count}")


def convert_single_file(file_path):
    """Преобразование одного файла: извлечение колонок 3, 4, 6"""
    if not os.path.exists(file_path):
        print(f"ERROR: Файл не существует: {file_path}")
        sys.exit(1)
    
    print(f"INFO: Чтение файла: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        output_lines = []
        line_count = 0
        for line in content.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 6:
                output_lines.append(f"{parts[2]} {parts[3]} {parts[5]}")
                line_count += 1
        
        print(f"INFO: Обработано строк: {line_count}")
        
        # Формируем имя выходного файла
        if '.' in file_path:
            base, ext = file_path.rsplit('.', 1)
            output_path = f"{base}_modified.{ext}"
        else:
            output_path = f"{file_path}_modified"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines) + '\n')
        
        print(f"DONE: Файл сохранён: {output_path}")
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: Usage:")
        print("  process_signals_server.py <signal_folder> <config_history_path>  - обработка сигналов")
        print("  process_signals_server.py --convert <file_path>                   - преобразование файла")
        sys.exit(1)
    
    if sys.argv[1] == "--convert":
        if len(sys.argv) != 3:
            print("ERROR: Usage: process_signals_server.py --convert <file_path>")
            sys.exit(1)
        convert_single_file(sys.argv[2])
    else:
        main()

