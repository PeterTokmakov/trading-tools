#!/usr/bin/env python3
# hash: 9b2e3d

"""
Trading Tools Launcher - Main application launcher.

Provides a unified interface for all trading tools.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import sys
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from trading_tools.gui_utils import DarkTheme, setup_dark_theme, create_dark_button, create_dark_label


class TradingToolsLauncher:
    """Main launcher for trading tools."""
    
    TOOLS = [
        {
            "name": "Generate Signals",
            "description": "Генерация сигналов CME с историческими конфигурациями",
            "module": "generate_signals.generate_signals",
            "icon": "📊"
        },
        {
            "name": "PnL Calculator",
            "description": "Расчёт PnL для торговых стратегий",
            "module": "pnl_calculator.pnl_calculator",
            "icon": "💰"
        },
        {
            "name": "PrintLvl",
            "description": "Симулятор и визуализация Level 2 order book",
            "module": "printlvl.printlvl",
            "icon": "📈"
        },
        {
            "name": "ServerLog Parser",
            "description": "Парсинг и фильтрация логов сервера",
            "module": "server_log_parser.log_parser",
            "icon": "🔍"
        },
        {
            "name": "Signal Log Parser",
            "description": "Парсинг CME Quincy логов",
            "module": "signal_log_parser.signal_log_parser",
            "icon": "📋"
        },
        {
            "name": "Signal Time Converter",
            "description": "Конвертация времени в сигналах",
            "module": "signal_converter.signal_converter",
            "icon": "🔄"
        },
        {
            "name": "StrategiesLog Parser",
            "description": "Парсинг логов стратегий",
            "module": "strategies_log_parser.log_parser_gui",
            "icon": "📊"
        }
    ]
    
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Tools Launcher")
        self.root.geometry("900x600")
        self.root.configure(bg=DarkTheme.BG)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup UI components."""
        # Setup dark theme
        style = ttk.Style()
        setup_dark_theme(style)
        
        # Header
        header_frame = tk.Frame(self.root, bg=DarkTheme.BG)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        title_label = create_dark_label(
            header_frame,
            "🚀 Trading Tools Launcher",
            font=("Segoe UI", 18, "bold"),
            fg=DarkTheme.PRIMARY
        )
        title_label.pack(pady=(0, 5))
        
        subtitle_label = create_dark_label(
            header_frame,
            "Unified interface for all trading utilities",
            font=("Segoe UI", 10),
            fg=DarkTheme.FG
        )
        subtitle_label.pack()
        
        # Tools list
        tools_frame = tk.Frame(self.root, bg=DarkTheme.BG)
        tools_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Scrollable frame
        canvas = tk.Canvas(tools_frame, bg=DarkTheme.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tools_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=DarkTheme.BG)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create tool cards
        for i, tool in enumerate(self.TOOLS):
            self.create_tool_card(scrollable_frame, tool, i)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg=DarkTheme.SURFACE)
        footer_frame.pack(fill=tk.X, padx=20, pady=20)
        
        version_label = create_dark_label(
            footer_frame,
            f"Trading Tools v1.0.0 | Python {sys.version.split()[0]}",
            font=("Segoe UI", 9),
            fg=DarkTheme.FG,
            bg=DarkTheme.SURFACE
        )
        version_label.pack(pady=10)
    
    def create_tool_card(self, parent: tk.Frame, tool: dict, index: int) -> None:
        """
        Create tool card.
        
        Args:
            parent: Parent widget
            tool: Tool dictionary
            index: Tool index
        """
        # Card frame
        card = tk.Frame(
            parent,
            bg=DarkTheme.SURFACE,
            highlightbackground=DarkTheme.SURFACE_HIGH,
            highlightthickness=1
        )
        card.pack(fill=tk.X, padx=10, pady=5)
        
        # Card content
        content_frame = tk.Frame(card, bg=DarkTheme.SURFACE)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Left side: icon and name
        left_frame = tk.Frame(content_frame, bg=DarkTheme.SURFACE)
        left_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        icon_label = create_dark_label(
            left_frame,
            tool["icon"],
            font=("Segoe UI", 24),
            fg=DarkTheme.PRIMARY,
            bg=DarkTheme.SURFACE
        )
        icon_label.pack()
        
        # Middle: name and description
        middle_frame = tk.Frame(content_frame, bg=DarkTheme.SURFACE)
        middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        name_label = create_dark_label(
            middle_frame,
            tool["name"],
            font=("Segoe UI", 12, "bold"),
            fg=DarkTheme.FG,
            bg=DarkTheme.SURFACE
        )
        name_label.pack(anchor=tk.W)
        
        desc_label = create_dark_label(
            middle_frame,
            tool["description"],
            font=("Segoe UI", 9),
            fg=DarkTheme.FG,
            bg=DarkTheme.SURFACE
        )
        desc_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Right side: launch button
        launch_btn = create_dark_button(
            content_frame,
            "🚀 Запустить",
            command=lambda: self.launch_tool(tool["module"]),
            bg=DarkTheme.PRIMARY,
            fg=DarkTheme.BG,
            active_bg=DarkTheme.SECONDARY,
            padx=20,
            pady=8
        )
        launch_btn.pack(side=tk.RIGHT)
        
        # Hover effect
        def on_enter(e):
            card.config(highlightbackground=DarkTheme.PRIMARY, highlightthickness=2)
        
        def on_leave(e):
            card.config(highlightbackground=DarkTheme.SURFACE_HIGH, highlightthickness=1)
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        content_frame.bind("<Enter>", on_enter)
        content_frame.bind("<Leave>", on_leave)
    
    def launch_tool(self, module_name: str) -> None:
        """
        Launch trading tool.
        
        Args:
            module_name: Module name to launch
        """
        try:
            # Import and run the tool
            module_path = f"trading_tools.{module_name}"
            
            # Run in subprocess to avoid blocking
            script_path = Path(__file__).parent / "trading_tools" / module_name.replace(".", "/") + ".py"
            
            if not script_path.exists():
                tk.messagebox.showerror(
                    "Ошибка",
                    f"Модуль не найден: {module_name}\nПуть: {script_path}",
                    parent=self.root
                )
                return
            
            # Launch in new window
            subprocess.Popen(
                [sys.executable, str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
        except Exception as e:
            tk.messagebox.showerror(
                "Ошибка запуска",
                f"Не удалось запустить инструмент:\n{str(e)}",
                parent=self.root
            )


def main():
    """Main entry point."""
    root = tk.Tk()
    app = TradingToolsLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
