# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import csv
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

# Получаем директорию, где находится скрипт
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Файл для хранения типов стратегий
STRATEGIES_FILE = os.path.join(SCRIPT_DIR, "strategy_types.json")
CSV_FILE = os.path.join(SCRIPT_DIR, "Russia.csv")


def load_strategies_from_csv():
    """Загружает уникальные стратегии из CSV файла"""
    strategies = set()
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Пропускаем заголовок
            for row in reader:
                if len(row) >= 2:
                    strategies.add(row[1])
    except FileNotFoundError:
        messagebox.showerror("Ошибка", f"Файл {CSV_FILE} не найден!")
    return strategies


def load_strategy_types():
    """Загружает сохранённые типы стратегий"""
    if os.path.exists(STRATEGIES_FILE):
        try:
            with open(STRATEGIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_strategy_types(strategy_types):
    """Сохраняет типы стратегий в файл"""
    with open(STRATEGIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(strategy_types, f, ensure_ascii=False, indent=2)


def load_pnl_data():
    """Загружает данные PnL из CSV файла"""
    data = []
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Пропускаем заголовок
            for row in reader:
                if len(row) >= 6 and row[2] == 'TOTAL':
                    try:
                        date_str = row[0]
                        strategy = row[1]
                        net = float(row[5]) if row[5] else 0.0
                        data.append({
                            'date': date_str,
                            'strategy': strategy,
                            'net': net
                        })
                    except ValueError:
                        continue
    except FileNotFoundError:
        messagebox.showerror("Ошибка", f"Файл {CSV_FILE} не найден!")
    return data


class PnLCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PnL Calculator")
        self.root.geometry("1600x750")
        self.root.configure(bg='#f0f0f0')
        
        # Стиль
        self.setup_styles()
        
        # Загружаем данные
        self.csv_strategies = load_strategies_from_csv()
        self.strategy_types = load_strategy_types()
        
        # Добавляем новые стратегии из CSV без типа
        for strategy in self.csv_strategies:
            if strategy not in self.strategy_types:
                self.strategy_types[strategy] = None
        
        # Сохраняем обновлённый список
        save_strategy_types(self.strategy_types)
        
        self.create_widgets()
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Стиль для Treeview
        style.configure("Strategies.Treeview",
                        background="#ffffff",
                        foreground="#333333",
                        rowheight=28,
                        fieldbackground="#ffffff",
                        font=('Segoe UI', 10))
        style.configure("Strategies.Treeview.Heading",
                        font=('Segoe UI', 10, 'bold'),
                        background="#4a90d9",
                        foreground="white",
                        padding=5)
        style.map("Strategies.Treeview",
                  background=[('selected', '#cce5ff')],
                  foreground=[('selected', '#000000')])
        
        # Стиль для таблицы PnL
        style.configure("PnL.Treeview",
                        background="#ffffff",
                        foreground="#333333",
                        rowheight=26,
                        fieldbackground="#ffffff",
                        font=('Consolas', 10))
        style.configure("PnL.Treeview.Heading",
                        font=('Segoe UI', 10, 'bold'),
                        background="#2e7d32",
                        foreground="white",
                        padding=5)
        style.map("PnL.Treeview",
                  background=[('selected', '#c8e6c9')],
                  foreground=[('selected', '#000000')])
        
        # Стиль для кнопок
        style.configure("Action.TButton",
                        font=('Segoe UI', 10, 'bold'),
                        padding=10)
        
        # Стиль для LabelFrame
        style.configure("Card.TLabelframe",
                        background="#f0f0f0")
        style.configure("Card.TLabelframe.Label",
                        font=('Segoe UI', 11, 'bold'),
                        foreground="#333333",
                        background="#f0f0f0")
    
    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель - стратегии (фиксированная ширина)
        left_frame = ttk.LabelFrame(main_frame, text="📋 Стратегии и типы", 
                                     padding="10", style="Card.TLabelframe")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        left_frame.pack_propagate(False)
        left_frame.configure(width=420)
        
        # Таблица стратегий
        strategies_container = ttk.Frame(left_frame)
        strategies_container.pack(fill=tk.BOTH, expand=True)
        
        # Treeview для стратегий
        columns = ('strategy', 'type')
        self.strategies_tree = ttk.Treeview(strategies_container, columns=columns, 
                                             show='headings', style="Strategies.Treeview")
        
        self.strategies_tree.heading('strategy', text='Название стратегии')
        self.strategies_tree.heading('type', text='Тип')
        
        self.strategies_tree.column('strategy', width=250, minwidth=150)
        self.strategies_tree.column('type', width=50, anchor='center', minwidth=40)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(strategies_container, orient="vertical", 
                                   command=self.strategies_tree.yview)
        self.strategies_tree.configure(yscrollcommand=scrollbar.set)
        
        self.strategies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Заполняем таблицу стратегий
        self.populate_strategies_table()
        
        # Двойной клик для редактирования
        self.strategies_tree.bind('<Double-1>', self.on_strategy_double_click)
        
        # Кнопки управления
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="💾 Сохранить типы", 
                   command=self.save_types, style="Action.TButton").pack(side=tk.LEFT, padx=5)
        
        # Фрейм для быстрого назначения типа
        quick_frame = ttk.LabelFrame(left_frame, text="Быстрое назначение", padding="5")
        quick_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Первая строка - радиокнопки
        radio_frame = ttk.Frame(quick_frame)
        radio_frame.pack(fill=tk.X)
        
        self.quick_type_var = tk.StringVar(value='1')
        for t in ['1', '2', '3', '4', '5', '6', '—']:
            ttk.Radiobutton(radio_frame, text=t, value=t if t != '—' else '', 
                           variable=self.quick_type_var).pack(side=tk.LEFT, padx=2)
        
        # Вторая строка - кнопка
        ttk.Button(quick_frame, text="Применить", 
                   command=self.apply_quick_type).pack(fill=tk.X, pady=(5, 0))
        
        # Правая панель - расчёт PnL
        right_frame = ttk.LabelFrame(main_frame, text="📊 Расчёт PnL", 
                                      padding="10", style="Card.TLabelframe")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Фрейм для дат
        dates_frame = ttk.Frame(right_frame)
        dates_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(dates_frame, text="📅 Начало:", 
                  font=('Segoe UI', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.start_date = DateEntry(dates_frame, width=12, date_pattern='dd.mm.yyyy',
                                     font=('Segoe UI', 10))
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dates_frame, text="📅 Конец:", 
                  font=('Segoe UI', 10)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.end_date = DateEntry(dates_frame, width=12, date_pattern='dd.mm.yyyy',
                                   font=('Segoe UI', 10))
        self.end_date.grid(row=0, column=3, padx=5, pady=5)
        
        # Кнопка расчёта
        calc_btn = ttk.Button(dates_frame, text="🔢 Рассчитать PnL", 
                              command=self.calculate_pnl, style="Action.TButton")
        calc_btn.grid(row=0, column=4, padx=20, pady=5)
        
        # Контейнер для таблицы PnL
        pnl_container = ttk.Frame(right_frame)
        pnl_container.pack(fill=tk.BOTH, expand=True)
        
        # Таблица результатов - 8 колонок
        columns = ('date', 'combo', 'type1', 'type2', 'type3', 'type4', 'type5', 'type6')
        self.results_tree = ttk.Treeview(pnl_container, columns=columns, 
                                          show='headings', style="PnL.Treeview")
        
        headers = {
            'date': 'Дата',
            'combo': 'T1×0.1 + T2×0.5',
            'type1': 'PnL типа 1',
            'type2': 'PnL типа 2',
            'type3': 'PnL типа 3',
            'type4': 'PnL типа 4',
            'type5': 'PnL типа 5',
        }
        
        for col, header in headers.items():
            self.results_tree.heading(col, text=header)
            width = 110 if col != 'date' else 90
            self.results_tree.column(col, width=width, anchor='center')
        
        # Скроллбар для результатов
        pnl_scrollbar = ttk.Scrollbar(pnl_container, orient="vertical", 
                                       command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=pnl_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pnl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Настройка тегов для итоговой строки
        self.results_tree.tag_configure('total', background='#e8f5e9', 
                                         font=('Consolas', 10, 'bold'))
        self.results_tree.tag_configure('oddrow', background='#f5f5f5')
        self.results_tree.tag_configure('evenrow', background='#ffffff')
        
        # Лог-область
        log_frame = ttk.LabelFrame(right_frame, text="📝 Подробный лог", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = tk.Text(log_frame, height=10, font=('Consolas', 9), wrap=tk.NONE)
        log_scrollbar_y = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar_x = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=log_scrollbar_y.set, xscrollcommand=log_scrollbar_x.set)
        
        log_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        log_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    def populate_strategies_table(self):
        """Заполняет таблицу стратегий"""
        # Очищаем таблицу
        for item in self.strategies_tree.get_children():
            self.strategies_tree.delete(item)
        
        # Добавляем стратегии
        sorted_strategies = sorted(self.strategy_types.keys())
        for idx, strategy in enumerate(sorted_strategies):
            type_val = self.strategy_types.get(strategy)
            type_str = str(type_val) if type_val is not None else '—'
            
            tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
            self.strategies_tree.insert('', 'end', values=(strategy, type_str), tags=(tag,))
        
        # Настройка цветов строк
        self.strategies_tree.tag_configure('oddrow', background='#f8f9fa')
        self.strategies_tree.tag_configure('evenrow', background='#ffffff')
    
    def on_strategy_double_click(self, event):
        """Обработка двойного клика для редактирования типа"""
        item = self.strategies_tree.selection()
        if not item:
            return
        
        item = item[0]
        values = self.strategies_tree.item(item, 'values')
        strategy_name = values[0]
        current_type = values[1]
        
        # Создаём диалог
        dialog = tk.Toplevel(self.root)
        dialog.title("Изменить тип")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Стратегия:\n{strategy_name}", 
                  font=('Segoe UI', 10), wraplength=280).pack(pady=10)
        
        ttk.Label(dialog, text="Выберите тип:", font=('Segoe UI', 10)).pack()
        
        type_var = tk.StringVar(value=current_type if current_type != '—' else '')
        
        type_frame = ttk.Frame(dialog)
        type_frame.pack(pady=10)
        
        for t in ['', '1', '2', '3', '4', '5', '6']:
            text = t if t else '—'
            ttk.Radiobutton(type_frame, text=text, value=t, 
                           variable=type_var).pack(side=tk.LEFT, padx=5)
        
        def apply_type():
            new_type = type_var.get()
            self.strategy_types[strategy_name] = int(new_type) if new_type else None
            self.populate_strategies_table()
            dialog.destroy()
        
        ttk.Button(dialog, text="Применить", command=apply_type).pack(pady=10)
    
    def apply_quick_type(self):
        """Применяет выбранный тип ко всем выделенным стратегиям"""
        selected = self.strategies_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите стратегии для назначения типа!")
            return
        
        type_val = self.quick_type_var.get()
        new_type = int(type_val) if type_val else None
        
        for item in selected:
            strategy_name = self.strategies_tree.item(item, 'values')[0]
            self.strategy_types[strategy_name] = new_type
        
        self.populate_strategies_table()
        messagebox.showinfo("Успех", f"Тип применён к {len(selected)} стратегиям!")
    
    def save_types(self):
        """Сохраняет типы стратегий"""
        save_strategy_types(self.strategy_types)
        messagebox.showinfo("Успех", "Типы стратегий сохранены!")
    
    def calculate_pnl(self):
        """Рассчитывает PnL по типам стратегий за выбранный период"""
        # Очищаем таблицу и лог
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.log_text.delete('1.0', tk.END)
        
        # Получаем даты
        start = self.start_date.get_date()
        end = self.end_date.get_date()
        
        if start > end:
            messagebox.showerror("Ошибка", "Начальная дата должна быть меньше конечной!")
            return
        
        self.log_text.insert(tk.END, f"=== Расчёт PnL с {start.strftime('%d.%m.%Y')} по {end.strftime('%d.%m.%Y')} ===\n\n")
        
        # Загружаем данные PnL
        pnl_data = load_pnl_data()
        
        # Группируем PnL по датам и типам, сохраняя детали
        pnl_by_date_type = defaultdict(lambda: defaultdict(float))
        details_by_date_type = defaultdict(lambda: defaultdict(list))
        
        for record in pnl_data:
            try:
                record_date = datetime.strptime(record['date'], '%d.%m.%Y').date()
            except ValueError:
                continue
            
            if start <= record_date <= end:
                strategy = record['strategy']
                strategy_type = self.strategy_types.get(strategy)
                
                if strategy_type is not None:
                    pnl_by_date_type[record_date][strategy_type] += record['net']
                    details_by_date_type[record_date][strategy_type].append({
                        'strategy': strategy,
                        'net': record['net']
                    })
        
        # Генерируем все даты в диапазоне
        current_date = start
        totals = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 'combo': 0}
        row_idx = 0
        
        while current_date <= end:
            type_pnls = pnl_by_date_type.get(current_date, {})
            details = details_by_date_type.get(current_date, {})
            
            pnl_type1 = type_pnls.get(1, 0)
            pnl_type2 = type_pnls.get(2, 0)
            pnl_type3 = type_pnls.get(3, 0)
            pnl_type4 = type_pnls.get(4, 0)
            pnl_type5 = type_pnls.get(5, 0)
            pnl_type6 = type_pnls.get(6, 0)
            
            combo = pnl_type1 * 0.1 + pnl_type2 * 0.5
            
            # Форматируем числа
            date_str = current_date.strftime('%d.%m.%Y')
            
            # Логируем детали
            self.log_text.insert(tk.END, f"{'='*60}\n")
            self.log_text.insert(tk.END, f"📅 ДАТА: {date_str}\n")
            self.log_text.insert(tk.END, f"{'='*60}\n")
            
            for type_num in [1, 2, 3, 4, 5, 6]:
                type_details = details.get(type_num, [])
                type_sum = type_pnls.get(type_num, 0)
                if type_details:
                    self.log_text.insert(tk.END, f"\n  📊 Тип {type_num} (сумма = {type_sum:,.2f}):\n")
                    for d in type_details:
                        self.log_text.insert(tk.END, f"      • {d['strategy']}: {d['net']:,.2f}\n")
            
            self.log_text.insert(tk.END, f"\n  🔢 ИТОГ в таблице:\n")
            self.log_text.insert(tk.END, f"      Комбо (T1×0.1 + T2×0.5) = {pnl_type1:,.2f} × 0.1 + {pnl_type2:,.2f} × 0.5 = {combo:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 1 = {pnl_type1:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 2 = {pnl_type2:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 3 = {pnl_type3:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 4 = {pnl_type4:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 5 = {pnl_type5:,.2f}\n")
            self.log_text.insert(tk.END, f"      PnL типа 6 = {pnl_type6:,.2f}\n\n")
            
            tag = 'oddrow' if row_idx % 2 == 0 else 'evenrow'
            
            self.results_tree.insert('', 'end', values=(
                date_str,
                f"{combo:,.2f}".replace(',', ' '),
                f"{pnl_type1:,.2f}".replace(',', ' '),
                f"{pnl_type2:,.2f}".replace(',', ' '),
                f"{pnl_type3:,.2f}".replace(',', ' '),
                f"{pnl_type4:,.2f}".replace(',', ' '),
                f"{pnl_type5:,.2f}".replace(',', ' '),
                f"{pnl_type6:,.2f}".replace(',', ' ')
            ), tags=(tag,))
            
            # Обновляем итоги
            totals[1] += pnl_type1
            totals[2] += pnl_type2
            totals[3] += pnl_type3
            totals[4] += pnl_type4
            totals[5] += pnl_type5
            totals[6] += pnl_type6
            totals['combo'] += combo
            
            current_date += timedelta(days=1)
            row_idx += 1
        
        # Логируем итоги
        self.log_text.insert(tk.END, f"\n{'='*60}\n")
        self.log_text.insert(tk.END, f"📊 ОБЩИЕ ИТОГИ:\n")
        self.log_text.insert(tk.END, f"{'='*60}\n")
        self.log_text.insert(tk.END, f"  Комбо (T1×0.1 + T2×0.5) = {totals['combo']:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 1 = {totals[1]:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 2 = {totals[2]:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 3 = {totals[3]:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 4 = {totals[4]:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 5 = {totals[5]:,.2f}\n")
        self.log_text.insert(tk.END, f"  PnL типа 6 = {totals[6]:,.2f}\n")
        
        # Добавляем итоговую строку
        self.results_tree.insert('', 'end', values=(
            '📊 ИТОГО',
            f"{totals['combo']:,.2f}".replace(',', ' '),
            f"{totals[1]:,.2f}".replace(',', ' '),
            f"{totals[2]:,.2f}".replace(',', ' '),
            f"{totals[3]:,.2f}".replace(',', ' '),
            f"{totals[4]:,.2f}".replace(',', ' '),
            f"{totals[5]:,.2f}".replace(',', ' '),
            f"{totals[6]:,.2f}".replace(',', ' ')
        ), tags=('total',))
        
        # Прокручиваем лог в начало
        self.log_text.see('1.0')


def main():
    root = tk.Tk()
    app = PnLCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""pnl_calculator_class"""



# API class for programmatic access (non-GUI)
class PnLCalculator:
    """API wrapper for PnL calculation without GUI"""
    
    def __init__(self, script_dir: str = None):
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
        self.strategy_types = {}
        self._log_callback = None
    
    def log(self, message: str, level: str = "info"):
        """Log message via callback or print"""
        if self._log_callback:
            self._log_callback(message, level)
        else:
            print(f"[{level.upper()}] {message}")
    

    def get_strategies(self) -> list:
        """Get list of strategies from strategy_names.csv"""
        strategies_file = os.path.join(self.script_dir, 'configs', 'strategy_names.csv')
        if not os.path.exists(strategies_file):
            self.log(f'Strategies file not found: {strategies_file}', 'warning')
            return []
        
        strategies = []
        with open(strategies_file, 'r', encoding='utf-8-sig') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(';')
                    if len(parts) >= 2:
                        strategies.append(parts[1])  # Strategy name is second column
        
        self.log(f'Loaded {len(strategies)} strategies', 'success')
        return strategies

    def _load_strategy_types(self) -> dict:
        """Load strategy types from CSV"""
        types_file = os.path.join(self.script_dir, '..', 'configs', 'strategy_types.csv')
        if not os.path.exists(types_file):
            return {}
        
        import csv
        strategy_types = {}
        with open(types_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                strategy = row.get('strategy', '').strip()
                type_str = row.get('type', '').strip()
                if strategy and type_str:
                    try:
                        strategy_types[strategy] = int(type_str)
                    except ValueError:
                        pass
        return strategy_types
    
    def _load_pnl_data(self) -> list:
        """Load PnL data from JSON"""
        pnl_file = os.path.join(self.script_dir, '..', 'data', 'pnl_data.json')
        if not os.path.exists(pnl_file):
            return []
        
        with open(pnl_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def calculate(
        self,
        start_date: str,
        end_date: str,
        log_callback=None
    ) -> dict:
        """
        Calculate PnL by strategy types for date range
        
        Args:
            start_date: Start date (DD.MM.YYYY or YYYY-MM-DD)
            end_date: End date (DD.MM.YYYY or YYYY-MM-DD)
            log_callback: Callback function(message, level)
        
        Returns:
            dict with status, totals, and daily breakdown
        """
        self._log_callback = log_callback
        
        try:
            # Parse dates
            formats = ["%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"]
            start = None
            end = None
            
            for fmt in formats:
                try:
                    start = datetime.strptime(start_date, fmt).date()
                    break
                except ValueError:
                    pass
            
            for fmt in formats:
                try:
                    end = datetime.strptime(end_date, fmt).date()
                    break
                except ValueError:
                    pass
            
            if not start or not end:
                return {"status": "error", "message": "Invalid date format"}
            
            if start > end:
                return {"status": "error", "message": "Start date must be before end date"}
            
            self.log(f"Calculating PnL: {start} - {end}", "info")
            
            # Load data
            self.strategy_types = self._load_strategy_types()
            pnl_data = self._load_pnl_data()
            
            if not pnl_data:
                self.log("No PnL data found", "warning")
                return {"status": "success", "message": "No data", "totals": {}, "daily": []}
            
            # Group PnL by date and type
            from collections import defaultdict
            pnl_by_date_type = defaultdict(lambda: defaultdict(float))
            
            for record in pnl_data:
                try:
                    record_date = datetime.strptime(record['date'], '%d.%m.%Y').date()
                except ValueError:
                    continue
                
                if start <= record_date <= end:
                    strategy = record['strategy']
                    strategy_type = self.strategy_types.get(strategy)
                    
                    if strategy_type is not None:
                        pnl_by_date_type[record_date][strategy_type] += record['net']
            
            # Calculate totals
            totals = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 'combo': 0}
            daily = []
            
            current_date = start
            while current_date <= end:
                type_pnls = pnl_by_date_type.get(current_date, {})
                
                pnl_type1 = type_pnls.get(1, 0)
                pnl_type2 = type_pnls.get(2, 0)
                pnl_type3 = type_pnls.get(3, 0)
                pnl_type4 = type_pnls.get(4, 0)
                pnl_type5 = type_pnls.get(5, 0)
                pnl_type6 = type_pnls.get(6, 0)
                
                combo = pnl_type1 * 0.1 + pnl_type2 * 0.5
                
                daily.append({
                    'date': current_date.strftime('%d.%m.%Y'),
                    'combo': round(combo, 2),
                    'type1': round(pnl_type1, 2),
                    'type2': round(pnl_type2, 2),
                    'type3': round(pnl_type3, 2),
                    'type4': round(pnl_type4, 2),
                    'type5': round(pnl_type5, 2),
                    'type6': round(pnl_type6, 2)
                })
                
                totals[1] += pnl_type1
                totals[2] += pnl_type2
                totals[3] += pnl_type3
                totals[4] += pnl_type4
                totals[5] += pnl_type5
                totals[6] += pnl_type6
                totals['combo'] += combo
                
                current_date += timedelta(days=1)
            
            # Round totals
            for key in totals:
                totals[key] = round(totals[key], 2)
            
            self.log(f"PnL calculation complete: combo={totals['combo']}", "success")
            
            return {
                "status": "success",
                "message": f"Calculated PnL for {start} - {end}",
                "totals": totals,
                "daily": daily
            }
            
        except Exception as e:
            self.log(f"Error: {e}", "error")
            return {"status": "error", "message": str(e)}


    # Alias for backward compatibility
    def calculate_pnl(self, *args, **kwargs):
        """Alias for calculate() method"""
        return self.calculate(*args, **kwargs)