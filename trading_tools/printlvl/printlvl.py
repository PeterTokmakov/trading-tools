#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintLvl GUI - Simulator & Plot Generator

A tkinter GUI for running simulator and viewing Level 2 order book plots.

Author: TradingTools Team
Version: 1.0
"""

import os
import sys
import threading
from pathlib import Path
from typing import Optional, List, Any

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from trading_tools.gui_utils import (
    DarkTheme, setup_dark_theme, create_dark_button, create_dark_label,
    create_dark_entry, show_error, show_info
)
from modules.printlvl import PrintLvl

# Try to import matplotlib for plot viewing
try:
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PlotViewerWindow:
    """Child window for viewing plots."""
    
    def __init__(self, parent: tk.Tk, title: str = "Plot Viewer"):
        """
        Initialize plot viewer window.
        
        Args:
            parent: Parent window
            title: Window title
        """
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("1350x900")
        self.window.configure(bg=DarkTheme.BG)
        
        # State
        self.figures: List[Any] = []
        self.current_index = 0
        self.canvas = None
        self.figure = None
        
        # Build UI
        self._build_ui()
        
        # Bind keyboard shortcuts
        self.window.bind('<Left>', lambda e: self.prev_slide())
        self.window.bind('<Right>', lambda e: self.next_slide())
        self.window.bind('<Escape>', lambda e: self.window.destroy())
        
        # Focus window
        self.window.focus_set()
    
    def _build_ui(self):
        """Build the UI components."""
        # Main frame
        main_frame = tk.Frame(self.window, bg=DarkTheme.BG)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas frame for plots
        self.canvas_frame = tk.Frame(main_frame, bg=DarkTheme.BG)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Navigation frame
        nav_frame = tk.Frame(main_frame, bg=DarkTheme.BG)
        nav_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Navigation buttons
        btn_style = {
            'font': DarkTheme.FONT_BUTTON,
            'bg': DarkTheme.SURFACE_HIGH,
            'fg': DarkTheme.FG,
            'activebackground': DarkTheme.PRIMARY,
            'activeforeground': DarkTheme.BG,
            'relief': tk.FLAT,
            'padx': 20,
            'pady': 8,
            'cursor': 'hand2'
        }
        
        self.prev_btn = tk.Button(
            nav_frame, text="< Prev", command=self.prev_slide, **btn_style
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.slide_label = tk.Label(
            nav_frame, text="0 / 0", font=DarkTheme.FONT_DEFAULT,
            bg=DarkTheme.BG, fg=DarkTheme.FG
        )
        self.slide_label.pack(side=tk.LEFT, padx=20)
        
        self.next_btn = tk.Button(
            nav_frame, text="Next >", command=self.next_slide, **btn_style
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Save PDF button
        self.save_btn = tk.Button(
            nav_frame, text="Save PDF", command=self.save_pdf, **btn_style
        )
        self.save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Keyboard shortcuts hint
        hint_label = tk.Label(
            nav_frame, text="Keyboard: Left/Right arrows to navigate, Esc to close",
            font=("Segoe UI", 9), bg=DarkTheme.BG, fg=DarkTheme.TERTIARY
        )
        hint_label.pack(side=tk.RIGHT, padx=20)
    
    def set_figures(self, figures: List[Any]):
        """
        Set figures to display.
        
        Args:
            figures: List of matplotlib figures
        """
        self.figures = figures
        self.current_index = 0
        self._update_display()
    
    def _update_display(self):
        """Update the display with current figure."""
        # Clear previous canvas
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        
        if self.figure:
            plt.close(self.figure)
            self.figure = None
        
        # Update label
        total = len(self.figures)
        if total == 0:
            self.slide_label.config(text="0 / 0")
            return
        
        self.slide_label.config(text=f"{self.current_index + 1} / {total}")
        
        # Get current figure
        fig = self.figures[self.current_index]
        
        # Create new canvas
        self.canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Update button states
        self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if self.current_index < total - 1 else tk.DISABLED)
    
    def prev_slide(self):
        """Go to previous slide."""
        if self.current_index > 0:
            self.current_index -= 1
            self._update_display()
    
    def next_slide(self):
        """Go to next slide."""
        if self.current_index < len(self.figures) - 1:
            self.current_index += 1
            self._update_display()
    
    def save_pdf(self):
        """Save all figures to PDF."""
        if not self.figures:
            show_info(self.window, "Info", "No figures to save")
            return
        
        filepath = filedialog.asksaveasfilename(
            parent=self.window,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save PDF"
        )
        
        if filepath:
            try:
                from matplotlib.backends.backend_pdf import PdfPages
                with PdfPages(filepath) as pdf:
                    for fig in self.figures:
                        pdf.savefig(fig, bbox_inches='tight')
                show_info(self.window, "Success", f"PDF saved to:\n{filepath}")
            except Exception as e:
                show_error(self.window, "Error", f"Failed to save PDF:\n{e}")


class PrintLvlGUI:
    """Main GUI for PrintLvl tool."""
    
    def __init__(self, root: tk.Tk, base_dir: Path):
        """
        Initialize PrintLvl GUI.
        
        Args:
            root: Tkinter root window
            base_dir: Base directory for configs and output
        """
        self.root = root
        self.base_dir = Path(base_dir)
        
        # Configure root
        self.root.title("PrintLvl - Simulator & Plot Generator")
        self.root.geometry("800x700")
        self.root.configure(bg=DarkTheme.BG)
        
        # Initialize backend
        self.printlvl = PrintLvl(base_dir, log_callback=self._log)
        
        # State
        self.plot_viewer: Optional[PlotViewerWindow] = None
        self.figures: List[Any] = []
        
        # Build UI
        self._build_ui()
        
        # Load config if exists
        self._load_config()
    
    def _build_ui(self):
        """Build the UI components."""
        # Setup ttk style
        style = ttk.Style()
        setup_dark_theme(style)
        
        # Main frame
        main_frame = tk.Frame(self.root, bg=DarkTheme.BG, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = create_dark_label(
            main_frame, "PrintLvl - Simulator & Plot Generator",
            font=DarkTheme.FONT_HEADER, fg=DarkTheme.PRIMARY
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Config frame
        config_frame = tk.LabelFrame(
            main_frame, text="Configuration", font=DarkTheme.FONT_HEADER,
            bg=DarkTheme.BG, fg=DarkTheme.PRIMARY, padx=15, pady=15
        )
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Ticker
        ticker_frame = tk.Frame(config_frame, bg=DarkTheme.BG)
        ticker_frame.pack(fill=tk.X, pady=5)
        create_dark_label(ticker_frame, "Ticker:").pack(side=tk.LEFT)
        self.ticker_var = tk.StringVar(value="MGNT_TQBR")
        ticker_entry = create_dark_entry(ticker_frame, self.ticker_var, width=25)
        ticker_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Date
        date_frame = tk.Frame(config_frame, bg=DarkTheme.BG)
        date_frame.pack(fill=tk.X, pady=5)
        create_dark_label(date_frame, "Date:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value="11.12.2025")
        date_entry = create_dark_entry(date_frame, self.date_var, width=15)
        date_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Time
        time_frame = tk.Frame(config_frame, bg=DarkTheme.BG)
        time_frame.pack(fill=tk.X, pady=5)
        create_dark_label(time_frame, "Time:").pack(side=tk.LEFT)
        self.time_var = tk.StringVar(value="22:59:51.000")
        time_entry = create_dark_entry(time_frame, self.time_var, width=15)
        time_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Offsets frame
        offset_frame = tk.Frame(config_frame, bg=DarkTheme.BG)
        offset_frame.pack(fill=tk.X, pady=5)
        
        create_dark_label(offset_frame, "Start Offset (ms):").pack(side=tk.LEFT)
        self.start_offset_var = tk.StringVar(value="0")
        start_entry = create_dark_entry(offset_frame, self.start_offset_var, width=10)
        start_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        create_dark_label(offset_frame, "End Offset (ms):").pack(side=tk.LEFT)
        self.end_offset_var = tk.StringVar(value="1000")
        end_entry = create_dark_entry(offset_frame, self.end_offset_var, width=10)
        end_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons frame
        btn_frame = tk.Frame(main_frame, bg=DarkTheme.BG)
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.run_btn = create_dark_button(
            btn_frame, "Run Pipeline", self._run_pipeline,
            bg=DarkTheme.PRIMARY, fg=DarkTheme.BG
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.view_btn = create_dark_button(
            btn_frame, "View Plots", self._show_plot_viewer,
            bg=DarkTheme.SECONDARY, fg=DarkTheme.BG
        )
        self.view_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.view_btn.config(state=tk.DISABLED)
        
        self.save_btn = create_dark_button(
            btn_frame, "Save PDF", self._save_pdf
        )
        self.save_btn.pack(side=tk.LEFT)
        self.save_btn.config(state=tk.DISABLED)
        
        # Log frame
        log_frame = tk.LabelFrame(
            main_frame, text="Log", font=DarkTheme.FONT_HEADER,
            bg=DarkTheme.BG, fg=DarkTheme.PRIMARY, padx=10, pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, font=DarkTheme.FONT_MONO,
            bg=DarkTheme.SURFACE, fg=DarkTheme.FG,
            insertbackground=DarkTheme.PRIMARY,
            relief=tk.FLAT, wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_label = create_dark_label(
            main_frame, textvariable=self.status_var,
            fg=DarkTheme.TERTIARY
        )
        status_label.pack(anchor=tk.W, pady=(10, 0))
    
    def _log(self, message: str):
        """Log message to text widget."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _load_config(self):
        """Load config from file if exists."""
        config_txt_path = self.base_dir / 'configs' / 'config.txt'
        if config_txt_path.exists():
            try:
                config = self.printlvl.parse_config_txt(config_txt_path)
                if 'ticker' in config:
                    self.ticker_var.set(config['ticker'])
                if 'date' in config:
                    self.date_var.set(config['date'])
                if 'time' in config:
                    self.time_var.set(config['time'])
                if 'start_time_offset' in config:
                    self.start_offset_var.set(config['start_time_offset'])
                if 'end_time_offset' in config:
                    self.end_offset_var.set(config['end_time_offset'])
            except Exception as e:
                self._log(f"Warning: Could not load config: {e}")
    
    def _save_config(self):
        """Save current config to file."""
        config_txt_path = self.base_dir / 'configs' / 'config.txt'
        config_json_path = self.base_dir / 'configs' / 'config.json'
        
        config_params = {
            'ticker': self.ticker_var.get(),
            'date': self.date_var.get(),
            'time': self.time_var.get(),
            'start_time_offset': self.start_offset_var.get(),
            'end_time_offset': self.end_offset_var.get()
        }
        
        try:
            self.printlvl.save_config_txt(config_txt_path, config_params)
            if config_json_path.exists():
                self.printlvl.update_config_json(config_json_path, config_params)
        except Exception as e:
            self._log(f"Warning: Could not save config: {e}")
    
    def _run_pipeline(self):
        """Run the pipeline in a background thread."""
        # Save config first
        self._save_config()
        
        # Disable buttons
        self.run_btn.config(state=tk.DISABLED)
        self.status_var.set("Running...")
        
        # Run in background thread
        def run():
            try:
                self._log("Starting pipeline...")
                
                # Connect SSH
                ssh = self.printlvl.connect_ssh()
                
                # Upload config
                config_json = self.printlvl.upload_config(
                    ssh,
                    self.printlvl.local_config_json_path,
                    self.printlvl.remote_config_path
                )
                
                # Run simulator
                success = self.printlvl.run_simulator(
                    ssh,
                    self.printlvl.simulator_path,
                    config_json
                )
                
                if success:
                    self._log("Pipeline completed successfully")
                    self.status_var.set("Completed")
                    
                    # Load figures if available
                    # TODO: Implement figure loading from server
                    
                    # Enable view button
                    self.view_btn.config(state=tk.NORMAL)
                    self.save_btn.config(state=tk.NORMAL)
                else:
                    self._log("Pipeline failed")
                    self.status_var.set("Failed")
                
                ssh.close()
                
            except Exception as e:
                self._log(f"Error: {e}")
                self.status_var.set("Error")
            finally:
                self.run_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def _show_plot_viewer(self):
        """Show the plot viewer window."""
        if not MATPLOTLIB_AVAILABLE:
            show_error(self.root, "Error", "Matplotlib is not available")
            return
        
        # Create viewer window
        self.plot_viewer = PlotViewerWindow(self.root)
        
        # Set figures if available
        if self.figures:
            self.plot_viewer.set_figures(self.figures)
    
    def _save_pdf(self):
        """Save figures to PDF."""
        if not self.figures:
            show_info(self.root, "Info", "No figures to save. Run pipeline first.")
            return
        
        filepath = filedialog.asksaveasfilename(
            parent=self.root,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save PDF"
        )
        
        if filepath:
            try:
                from matplotlib.backends.backend_pdf import PdfPages
                with PdfPages(filepath) as pdf:
                    for fig in self.figures:
                        pdf.savefig(fig, bbox_inches='tight')
                show_info(self.root, "Success", f"PDF saved to:\n{filepath}")
            except Exception as e:
                show_error(self.root, "Error", f"Failed to save PDF:\n{e}")


def main():
    """Main entry point."""
    # Get base directory
    base_dir = Path(__file__).parent.parent.parent
    
    # Create root window
    root = tk.Tk()
    
    # Create GUI
    app = PrintLvlGUI(root, base_dir)
    
    # Run main loop
    root.mainloop()


if __name__ == "__main__":
    main()
