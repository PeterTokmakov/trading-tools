#!/usr/bin/env python3
# hash: 7c3d5e

"""
GUI Utils module for trading tools.
Provides common UI components and styles for all trading tools.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable


class DarkTheme:
    """Dark theme configuration for trading tools."""
    
    # Colors (Catppuccin Mocha)
    BG = "#1e1e2e"
    FG = "#cdd6f4"
    SURFACE = "#313244"
    SURFACE_HIGH = "#45475a"
    PRIMARY = "#89b4fa"
    SECONDARY = "#a6e3a1"
    TERTIARY = "#f9e2af"
    ERROR = "#f38ba8"
    WARNING = "#fab387"
    
    # Fonts
    FONT_DEFAULT = ("Segoe UI", 10)
    FONT_HEADER = ("Segoe UI", 12, "bold")
    FONT_MONO = ("Consolas", 10)
    FONT_BUTTON = ("Segoe UI", 10, "bold")


def setup_dark_theme(style: ttk.Style) -> None:
    """
    Setup dark theme for ttk widgets.
    
    Args:
        style: ttk.Style instance
    """
    style.theme_use("clam")
    
    # Configure frames
    style.configure("TFrame", background=DarkTheme.BG)
    style.configure("TLabelFrame", background=DarkTheme.BG, foreground=DarkTheme.FG)
    style.configure("TLabelFrame.Label", background=DarkTheme.BG, foreground=DarkTheme.PRIMARY, font=DarkTheme.FONT_HEADER)
    
    # Configure labels
    style.configure("TLabel", background=DarkTheme.BG, foreground=DarkTheme.FG, font=DarkTheme.FONT_DEFAULT)
    style.configure("Header.TLabel", background=DarkTheme.BG, foreground=DarkTheme.PRIMARY, font=DarkTheme.FONT_HEADER)
    style.configure("Success.TLabel", background=DarkTheme.BG, foreground=DarkTheme.SECONDARY)
    style.configure("Error.TLabel", background=DarkTheme.BG, foreground=DarkTheme.ERROR)
    style.configure("Warning.TLabel", background=DarkTheme.BG, foreground=DarkTheme.WARNING)
    
    # Configure buttons
    style.configure("TButton", font=DarkTheme.FONT_BUTTON)
    style.map("TButton",
              background=[("active", DarkTheme.PRIMARY)],
              foreground=[("active", DarkTheme.BG)])
    
    # Configure entries
    style.configure("TEntry", font=DarkTheme.FONT_MONO, fieldbackground=DarkTheme.SURFACE, foreground=DarkTheme.FG)
    
    # Configure progress bar
    style.configure("TProgressbar", background=DarkTheme.PRIMARY, troughcolor=DarkTheme.SURFACE)


def create_dark_button(parent: tk.Widget, text: str, command: Callable, 
                      bg: str = DarkTheme.SURFACE_HIGH, fg: str = DarkTheme.FG,
                      active_bg: str = DarkTheme.PRIMARY, active_fg: str = DarkTheme.BG,
                      padx: int = 15, pady: int = 8) -> tk.Button:
    """
    Create a dark-themed button.
    
    Args:
        parent: Parent widget
        text: Button text
        command: Button command
        bg: Background color
        fg: Foreground color
        active_bg: Active background color
        active_fg: Active foreground color
        padx: Horizontal padding
        pady: Vertical padding
        
    Returns:
        Button widget
    """
    return tk.Button(
        parent,
        text=text,
        font=DarkTheme.FONT_BUTTON,
        bg=bg,
        fg=fg,
        activebackground=active_bg,
        activeforeground=active_fg,
        relief=tk.FLAT,
        padx=padx,
        pady=pady,
        cursor="hand2",
        command=command
    )


def create_dark_label(parent: tk.Widget, text: str, font: tuple = DarkTheme.FONT_DEFAULT,
                     fg: str = DarkTheme.FG, bg: str = DarkTheme.BG) -> tk.Label:
    """
    Create a dark-themed label.
    
    Args:
        parent: Parent widget
        text: Label text
        font: Font tuple
        fg: Foreground color
        bg: Background color
        
    Returns:
        Label widget
    """
    return tk.Label(
        parent,
        text=text,
        font=font,
        fg=fg,
        bg=bg,
        anchor=tk.W
    )


def create_dark_entry(parent: tk.Widget, textvariable: tk.StringVar, width: int = 20,
                     font: tuple = DarkTheme.FONT_MONO) -> tk.Entry:
    """
    Create a dark-themed entry.
    
    Args:
        parent: Parent widget
        textvariable: Text variable
        width: Entry width
        font: Font tuple
        
    Returns:
        Entry widget
    """
    return tk.Entry(
        parent,
        textvariable=textvariable,
        width=width,
        font=font,
        bg=DarkTheme.SURFACE,
        fg=DarkTheme.FG,
        insertbackground=DarkTheme.PRIMARY,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=DarkTheme.SURFACE_HIGH,
        highlightcolor=DarkTheme.PRIMARY
    )


def show_error(parent: tk.Widget, title: str, message: str) -> None:
    """
    Show error message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Error message
    """
    messagebox.showerror(title, message, parent=parent)


def show_warning(parent: tk.Widget, title: str, message: str) -> None:
    """
    Show warning message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Warning message
    """
    messagebox.showwarning(title, message, parent=parent)


def show_info(parent: tk.Widget, title: str, message: str) -> None:
    """
    Show info message box.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Info message
    """
    messagebox.showinfo(title, message, parent=parent)


def show_question(parent: tk.Widget, title: str, message: str) -> bool:
    """
    Show yes/no question dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Question message
        
    Returns:
        True if user clicked Yes, False otherwise
    """
    return messagebox.askyesno(title, message, parent=parent)


class StatusLabel:
    """Status label with color-coded messages."""
    
    def __init__(self, parent: tk.Widget, text: str = "Ready"):
        """
        Initialize status label.
        
        Args:
            parent: Parent widget
            text: Initial text
        """
        self.label = create_dark_label(parent, text, fg=DarkTheme.FG)
        self.label.pack(fill=tk.X)
    
    def set_ready(self, text: str = "Ready") -> None:
        """Set ready status."""
        self.label.config(text=text, fg=DarkTheme.FG)
    
    def set_success(self, text: str) -> None:
        """Set success status."""
        self.label.config(text=text, fg=DarkTheme.SECONDARY)
    
    def set_error(self, text: str) -> None:
        """Set error status."""
        self.label.config(text=text, fg=DarkTheme.ERROR)
    
    def set_warning(self, text: str) -> None:
        """Set warning status."""
        self.label.config(text=text, fg=DarkTheme.WARNING)
    
    def set_info(self, text: str) -> None:
        """Set info status."""
        self.label.config(text=text, fg=DarkTheme.PRIMARY)
