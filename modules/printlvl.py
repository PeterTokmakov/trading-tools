#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrintLvl - Simulator & Plot Generator

A tool for running simulator on remote server and generating 
Level 2 order book visualizations.

Author: PrintLvl Team
Version: 2.0
"""

# =============================================================================
# IMPORTS
# =============================================================================

import os
import sys
import json
import re
import time
import threading
import queue
import warnings
from pathlib import Path
from collections import deque
from io import StringIO, BytesIO

import paramiko
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, filedialog
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

# Suppress warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
SSH_SETTINGS_PATH = Path(__file__).parent / 'ssh_settings.json'
LOCAL_CONFIG_TXT_PATH = Path(__file__).parent / 'configs' / 'config.txt'
LOCAL_CONFIG_JSON_PATH = Path(__file__).parent / 'configs' / 'config.json'
LOCAL_OUTPUT_DIR = Path(__file__).parent / 'Plots'

# Load SSH settings
if SSH_SETTINGS_PATH.exists():
    with open(SSH_SETTINGS_PATH, 'r', encoding='utf-8') as f:
        _ssh_settings = json.load(f)
        SSH_USERNAME = _ssh_settings.get('SSH_USERNAME', 'ptokmakov')
        SSH_KEY_PATH = _ssh_settings.get('SSH_KEY_PATH', r'C:\Users\user\.ssh\id_ed25519')
        REMOTE_HOST = _ssh_settings.get('REMOTE_HOST', '192.168.5.11')
else:
    SSH_USERNAME = 'ptokmakov'
    SSH_KEY_PATH = r'C:\Users\user\.ssh\id_ed25519'
    REMOTE_HOST = '192.168.5.11'

SIMULATOR_PATH = f'/home/{SSH_USERNAME}/build/Simulator/Debug/Simulator'
REMOTE_CONFIG_PATH = f'/home/{SSH_USERNAME}/tmp/simulator_config.json'

# Plot parameters
PRINT_ONLY_NOT_EMPTY_LEVELS = True
PRICESCALE = 1_000_000
AMOUNTSCALE = 1
COLOR_PALETTE = {'Sim': '#1E3A8A', 'Real': '#1C1C1C', 'OurReal': '#FFD700'}
MAX_SLIDES = 5000
BATCH_SIZE = 500

# Plot settings
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)

# =============================================================================
# UI THEME CONFIGURATION
# =============================================================================

class Theme:
    """Modern dark theme configuration."""
    
    # Main colors
    BG_DARK = '#1E1E2E'
    BG_MEDIUM = '#2D2D3F'
    BG_LIGHT = '#3D3D52'
    BG_INPUT = '#252535'
    
    # Accent colors  
    ACCENT_PRIMARY = '#7C3AED'
    ACCENT_SECONDARY = '#A78BFA'
    ACCENT_SUCCESS = '#10B981'
    ACCENT_WARNING = '#F59E0B'
    ACCENT_ERROR = '#EF4444'
    ACCENT_INFO = '#3B82F6'
    
    # Text colors
    TEXT_PRIMARY = '#F8FAFC'
    TEXT_SECONDARY = '#94A3B8'
    TEXT_MUTED = '#64748B'
    
    # Button colors
    BTN_PRIMARY_BG = '#7C3AED'
    BTN_PRIMARY_FG = '#FFFFFF'
    BTN_SECONDARY_BG = '#3D3D52'
    BTN_SECONDARY_FG = '#E2E8F0'
    
    # Navigation button colors
    NAV_BTN_BG = '#4C1D95'
    NAV_BTN_FG = '#E9D5FF'
    
    # Fonts
    FONT_FAMILY = 'Segoe UI'
    FONT_MONO = 'Consolas'

# =============================================================================
# CONFIGURATION PARSING
# =============================================================================

def parse_config_txt(config_txt_path, silent=False):
    """Parse config.txt file and extract parameters."""
    if not silent:
        print(f"Reading {config_txt_path}...")
    
    config = {}
    with open(config_txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
    
    if not silent:
        print(f"✓ Parsed config: {config}")
    return config


def save_config_txt(config_txt_path, config_params):
    """Save config parameters to config.txt file."""
    with open(config_txt_path, 'w', encoding='utf-8') as f:
        for key, value in config_params.items():
            f.write(f"{key} = {value}\n")


def update_config_json(config_json_path, config_txt_params):
    """Update config.json based on config.txt parameters."""
    print(f"Updating {config_json_path}...")
    
    with open(config_json_path, 'r', encoding='utf-8') as f:
        config_json = json.load(f)
    
    if 'ticker' in config_txt_params:
        config_json['Instruments'] = [config_txt_params['ticker']]
    
    if 'date' in config_txt_params:
        config_json['Dates'] = [config_txt_params['date']]
    
    if 'time' in config_txt_params:
        time_str = config_txt_params['time']
        time_parts = time_str.split(':')
        hour = int(time_parts[0])
        min_val = int(time_parts[1])
        sec_ms = time_parts[2].split('.')
        sec = int(sec_ms[0])
        ms = int(sec_ms[1]) if len(sec_ms) > 1 else 0
        
        params = config_json.get('Parameters', [])
        param_dict = {}
        for param in params:
            if isinstance(param, dict):
                param_dict.update(param)
        
        param_dict['hour'] = [hour, 0, 0, 0]
        param_dict['min'] = [min_val, 0, 0, 0]
        param_dict['sec'] = [sec, 0, 0, 0]
        param_dict['ms'] = [ms, 0, 0, 0]
        
        if 'start_time_offset' in config_txt_params:
            param_dict['start_offset_ms'] = [int(config_txt_params['start_time_offset']), 0, 0, 0]
        
        if 'end_time_offset' in config_txt_params:
            param_dict['end_offset_ms'] = [int(config_txt_params['end_time_offset']), 0, 0, 0]
        
        config_json['Parameters'] = [{k: v} for k, v in param_dict.items()]
    
    with open(config_json_path, 'w', encoding='utf-8') as f:
        json.dump(config_json, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Config.json updated")
    return config_json

# =============================================================================
# SSH OPERATIONS
# =============================================================================

def connect_ssh():
    """Establish SSH connection to remote server."""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        private_key = paramiko.Ed25519Key.from_private_key_file(SSH_KEY_PATH)
        ssh.connect(
            hostname=REMOTE_HOST,
            username=SSH_USERNAME,
            pkey=private_key,
            timeout=30
        )
        print(f"✓ Connected to {REMOTE_HOST}")
        return ssh
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        sys.exit(1)


def ensure_remote_dir(ssh, remote_dir):
    """Ensure remote directory exists."""
    try:
        sftp = ssh.open_sftp()
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            ssh.exec_command(f"mkdir -p {remote_dir}")
        finally:
            sftp.close()
    except Exception as e:
        print(f"  Warning: Could not ensure directory {remote_dir}: {e}")


def upload_config(ssh, local_config_path, remote_config_path):
    """Upload config.json to remote server."""
    print(f"Uploading config.json to server...")
    
    try:
        remote_dir = os.path.dirname(remote_config_path)
        if remote_dir:
            ensure_remote_dir(ssh, remote_dir)
        
        with open(local_config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        sftp = ssh.open_sftp()
        try:
            config_json_str = json.dumps(config_data, ensure_ascii=False, indent=2)
            with sftp.open(remote_config_path, 'w') as remote_file:
                remote_file.write(config_json_str.encode('utf-8'))
            print(f"✓ Config uploaded to {remote_config_path}")
            return config_data
        finally:
            sftp.close()
    except Exception as e:
        print(f"✗ Failed to upload config: {e}")
        sys.exit(1)


def run_simulator(ssh, simulator_path, config_json, log_print=None):
    """Run simulator on remote server with real-time output."""
    if log_print is None:
        log_print = print
    
    log_print(f"Running simulator...")
    
    config_json_str = json.dumps(config_json, ensure_ascii=False)
    command = f"{simulator_path} config '{config_json_str}'"
    
    stdin, stdout, stderr = ssh.exec_command(command)
    
    output_lines = []
    error_lines = []
    has_critical_errors = False
    
    # Read stdout line by line
    while True:
        line = stdout.readline()
        if not line:
            break
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        line = line.strip()
        if line:
            output_lines.append(line)
            print(line)
            
            if "Prepare to filtration" in line:
                log_print("🔄 Filtration Started")
            if "Filtration completed  " in line:
                log_print("✓ Filtration completed")
    
    # Read stderr
    while True:
        line = stderr.readline()
        if not line:
            break
        if isinstance(line, bytes):
            line = line.decode('utf-8')
        line = line.strip()
        if line:
            error_lines.append(line)
            print(f"Warning/Error: {line}")
            
            if "Prepare to filtration" in line:
                log_print("🔄 Filtration Started")
            if "Filtration completed  " in line:
                log_print("✓ Filtration completed")
            
            if any(kw in line.lower() for kw in ['error', 'failed', 'exception', 'fatal']):
                has_critical_errors = True
    
    exit_status = stdout.channel.recv_exit_status()
    
    if has_critical_errors:
        log_print(f"✗ Simulator has critical errors")
        return False
    
    log_print("✓ Simulator completed")
    return True

# =============================================================================
# DATA LOADING AND PROCESSING
# =============================================================================

def read_file_from_server(sftp, file_path):
    """Read file content from remote server."""
    try:
        file_stat = sftp.stat(file_path)
        if file_stat.st_size == 0:
            return None
        
        with sftp.open(file_path, 'r') as f:
            content = f.read().decode('utf-8')
        
        if not content or not content.strip():
            return None
        
        for sep in ['\t', r'\s+', ',']:
            try:
                df = pd.read_csv(StringIO(content), sep=sep, header=None, 
                                 engine='python', on_bad_lines='skip', dtype=str)
                if df is not None and not df.empty:
                    return df
            except Exception:
                continue
        return None
    except FileNotFoundError:
        return None
    except Exception:
        return None


def load_data_from_server(ssh, file_path):
    """Load data from specific file on server."""
    print(f"Loading data from file: {file_path}")
    
    sftp = ssh.open_sftp()
    try:
        try:
            sftp.stat(file_path)
        except FileNotFoundError:
            return None
        
        df = read_file_from_server(sftp, file_path)
        if df is None or df.empty:
            return None
        
        print(f"✓ Loaded {len(df)} rows")
        return df
    finally:
        sftp.close()


def process_data(df):
    """Process the loaded data according to R script logic."""
    print("Processing data...")
    
    df.columns = ['Symbol', 'Index', 'Day', 'Time', 'Price', 'Amount', 'Side', 'Id_ord', 'IsOur']
    
    df['Id_ord'] = pd.to_numeric(df['Id_ord'], errors='coerce')
    df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['IsOur'] = pd.to_numeric(df['IsOur'], errors='coerce')
    
    df.loc[df['IsOur'] == -1, 'Id_ord'] = df.loc[df['IsOur'] == -1, 'Id_ord'] + 0.5
    df = df.sort_values(['Day', 'Time', 'Symbol', 'Price', 'Id_ord']).reset_index(drop=True)
    
    df_msp = df.groupby(['Symbol', 'Day', 'Price']).size().reset_index()
    df_msp = df_msp.groupby(['Symbol', 'Day']).apply(
        lambda x: pd.Series({'MSP': np.min(np.diff(np.sort(x['Price'].unique()))) / PRICESCALE})
    ).reset_index()
    
    df = df.merge(df_msp, on=['Symbol', 'Day'], how='inner')
    
    breaks_info = df.groupby('Symbol').agg({
        'Price': ['min', 'max'],
        'MSP': 'first'
    }).reset_index()
    breaks_info.columns = ['Symbol', 'PriceMin', 'PriceMax', 'MSP']
    
    breaks_for_plot = []
    for _, row in breaks_info.iterrows():
        price_range = np.arange(
            row['PriceMin'] / PRICESCALE,
            row['PriceMax'] / PRICESCALE + row['MSP'],
            row['MSP']
        )
        breaks_for_plot.extend(price_range)
    
    breaks_for_plot = sorted(set(breaks_for_plot))
    
    df['IsOurTemp'] = df['IsOur'].apply(lambda x: 1 if x > 0 else x)
    df['fontface'] = df['IsOur'].apply(lambda x: 'bold' if x != 0 else 'normal')
    
    type_mapping = {-1: 'Sim', 0: 'Real', 1: 'OurReal'}
    df['Type'] = df['IsOurTemp'].map(type_mapping)
    df = df.drop('IsOurTemp', axis=1)
    
    print("✓ Data processed")
    return df, breaks_for_plot

# =============================================================================
# PLOTTING
# =============================================================================

def plot_lvl2_with_orders(df_plot, breaks_for_plot=None):
    """Create level 2 order book plot."""
    if df_plot.empty:
        return None
    
    valid_prices = df_plot[df_plot['IsOur'] >= 0]
    if valid_prices.empty:
        return None
    
    price_min = valid_prices['Price'].min()
    price_max = valid_prices['Price'].max()
    
    df_plot = df_plot[(df_plot['Price'] >= price_min) & (df_plot['Price'] <= price_max)].copy()
    df_plot = df_plot.sort_values(['Side', 'Id_ord'], ascending=[False, True]).reset_index(drop=True)
    df_plot['AmountLogScale'] = np.log1p(df_plot['Amount'])
    
    # Calculate text positions
    df_plot['TextPosition'] = 0.0
    for (symbol, price), group_idx in df_plot.groupby(['Symbol', 'Price']).groups.items():
        group = df_plot.loc[group_idx].sort_values(['Side', 'Id_ord'], ascending=[False, True])
        lagged = group['AmountLogScale'].shift(1).fillna(0)
        cumsum_values = lagged.cumsum()
        df_plot.loc[group.index, 'TextPosition'] = 0.25 + cumsum_values.values
    
    symbols = df_plot['Symbol'].unique()
    n_symbols = len(symbols)
    
    if n_symbols == 0:
        return None
    
    n_cols = min(3, n_symbols)
    n_rows = (n_symbols + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 10))
    if n_symbols == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if n_symbols > 1 else [axes]
    
    for sym_idx, symbol in enumerate(symbols):
        ax = axes[sym_idx] if n_symbols > 1 else axes[0]
        df_symbol = df_plot[df_plot['Symbol'] == symbol].copy()
        
        if df_symbol.empty:
            continue
        
        if PRINT_ONLY_NOT_EMPTY_LEVELS:
            unique_prices = sorted(df_symbol['Price'].unique())
            price_labels = [str(p / PRICESCALE) for p in unique_prices]
            price_to_idx = {p: idx for idx, p in enumerate(unique_prices)}
        else:
            unique_prices = sorted(df_symbol['Price'].unique())
            price_labels = [p / PRICESCALE for p in unique_prices]
            price_to_idx = {p: idx for idx, p in enumerate(unique_prices)}
        
        df_symbol = df_symbol.sort_values(['Side', 'Id_ord'], ascending=[False, True]).reset_index(drop=True)
        bottom_positions = {price: 0 for price in unique_prices}
        
        for _, row in df_symbol.iterrows():
            price = row['Price']
            price_idx = price_to_idx[price]
            amount_log = row['AmountLogScale']
            
            # Modern color scheme for buy/sell
            if row['Side'] == 'DirBuy':
                side_color = '#22C55E'  # Green
            elif row['Side'] == 'DirSell':
                side_color = '#EF4444'  # Red
            else:
                side_color = '#6B7280'  # Gray
            
            bar_width = 0.8 if PRINT_ONLY_NOT_EMPTY_LEVELS else (
                (unique_prices[1] - unique_prices[0]) / PRICESCALE if len(unique_prices) > 1 else 0.01
            )
            
            if PRINT_ONLY_NOT_EMPTY_LEVELS:
                ax.barh(price_idx, amount_log, left=bottom_positions[price],
                        height=0.8, color=side_color, edgecolor='#1F2937', linewidth=0.5)
            else:
                ax.barh(price / PRICESCALE, amount_log, left=bottom_positions[price],
                        height=bar_width, color=side_color, edgecolor='#1F2937', linewidth=0.5)
            
            bottom_positions[price] += amount_log
            
            # Format amount label
            amount_value = row['Amount'] / AMOUNTSCALE if PRINT_ONLY_NOT_EMPTY_LEVELS else row['Amount']
            if abs(amount_value - round(amount_value)) < 1e-10:
                label = str(int(round(amount_value)))
            else:
                label = f"{amount_value:.6f}".rstrip('0').rstrip('.')
            
            text_color = COLOR_PALETTE.get(row['Type'], '#1F2937')
            weight = 'bold' if row['fontface'] == 'bold' else 'normal'
            style = 'italic' if row['IsOur'] != 0 else 'normal'
            
            y_pos = price_idx if PRINT_ONLY_NOT_EMPTY_LEVELS else price / PRICESCALE
            ax.text(row['TextPosition'], y_pos, label,
                    ha='left', va='center',
                    color=text_color, weight=weight, style=style, fontsize=8)
        
        ax.set_xlabel('Amount (log scale)', fontsize=10)
        ax.set_ylabel('Price', fontsize=10)
        ax.set_title(f"{symbol}", fontsize=12, fontweight='bold')
        ax.set_xlim(left=0)
        ax.grid(False, axis='y')
        
        if PRINT_ONLY_NOT_EMPTY_LEVELS:
            ax.set_yticks(range(len(price_labels)))
            ax.set_yticklabels(price_labels)
        elif breaks_for_plot:
            ax.set_yticks(breaks_for_plot)
    
    # Remove unused axes
    for idx in range(n_symbols, len(axes)):
        fig.delaxes(axes[idx])
    
    # Title with date and time
    if not df_plot.empty:
        day = df_plot['Day'].iloc[0]
        time_val = df_plot['Time'].iloc[0]
        fig.suptitle(f"{day} {time_val}", fontsize=14, fontweight='bold', y=0.995)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=color, label=label)
        for label, color in COLOR_PALETTE.items()
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=3, bbox_to_anchor=(0.5, 0.01))
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.98])
    return fig


def generate_pdfs(df, breaks_for_plot, file_name_out='mgnt', date='', 
                  show_gui=False, gui_callback=None, gui_obj=None):
    """Generate plots and show in GUI."""
    print(f"Generating plots...")
    
    unique_moments = df.groupby(['Day', 'Time', 'Index']).size().reset_index()[['Day', 'Time', 'Index']]
    n_moments = len(unique_moments)
    
    print("  Pre-calculating slide mapping...")
    moment_to_slide_map = {}
    slide_to_moment_map = {}
    df_plot_prev_check = None
    slide_index = 0
    
    for i in range(n_moments):
        moment = unique_moments.iloc[i]
        df_plot_check = df[
            (df['Index'] == moment['Index']) &
            (df['Day'] == moment['Day']) &
            (df['Time'] == moment['Time'])
        ].drop(['Time', 'Index'], axis=1, errors='ignore')
        
        skip_this = False
        if df_plot_prev_check is not None:
            if df_plot_check.equals(df_plot_prev_check):
                skip_this = True
        
        if not skip_this:
            moment_to_slide_map[i] = slide_index
            slide_to_moment_map[slide_index] = i
            slide_index += 1
            df_plot_prev_check = df_plot_check.copy()
    
    n_slides = slide_index
    print(f"  Total unique moments: {n_moments}, total slides: {n_slides}")
    
    # Limit slides
    if n_slides > MAX_SLIDES:
        print(f"  ⚠ Limiting to first {MAX_SLIDES} slides (found {n_slides})")
        n_slides = MAX_SLIDES
        slide_to_moment_map = {k: v for k, v in slide_to_moment_map.items() if k < MAX_SLIDES}
        moment_to_slide_map = {k: v for k, v in moment_to_slide_map.items() if v < MAX_SLIDES}
        unique_moment_indices = sorted(set(slide_to_moment_map.values()))
        unique_moments = unique_moments.iloc[unique_moment_indices].reset_index(drop=True)
        n_moments = len(unique_moments)
    
    # Pre-calculate all slide times
    all_slide_times = {}
    for slide_idx in range(n_slides):
        if slide_idx in slide_to_moment_map:
            moment_idx = slide_to_moment_map[slide_idx]
            moment = unique_moments.iloc[moment_idx]
            all_slide_times[slide_idx] = moment.get('Time', '')
    
    if show_gui and gui_callback:
        gui_callback(None, 0, n_slides, file_name_out, date, is_total_count=True, all_slide_times=all_slide_times)
        if n_slides == 0:
            return [], file_name_out, date
    
    cnt_plot = 0
    df_plot_prev = None
    figures_list = [None] * n_slides
    slide_queue = deque(range(n_slides))
    
    try:
        while slide_queue:
            if gui_obj and gui_obj.plot_window_closed:
                print("  Processing stopped: Plot Viewer closed")
                break
            
            # Handle priority slides
            if gui_obj and gui_obj.priority_slide_index is not None:
                priority_idx = gui_obj.priority_slide_index
                
                if priority_idx < len(figures_list) and figures_list[priority_idx] is not None:
                    gui_obj.priority_slide_index = None
                    gui_obj.root.after(0, lambda idx=priority_idx: gui_obj._display_slide_visual_only(idx))
                else:
                    slide_queue.appendleft(priority_idx)
                    df_plot_prev = None
            
            slide_idx = slide_queue.popleft()
            
            # Skip already processed
            if slide_idx < len(figures_list) and figures_list[slide_idx] is not None:
                continue
            
            if slide_idx not in slide_to_moment_map:
                continue
            
            moment_idx = slide_to_moment_map[slide_idx]
            moment = unique_moments.iloc[moment_idx]
            
            df_plot = df[
                (df['Index'] == moment['Index']) &
                (df['Day'] == moment['Day']) &
                (df['Time'] == moment['Time'])
            ].copy()
            
            slide_time = moment.get('Time', '')
            df_plot_check = df_plot.drop(['Time', 'Index'], axis=1, errors='ignore')
            skip_this = False
            is_current_slide = (gui_obj and gui_obj.current_slide_index == slide_idx)
            
            if df_plot_prev is not None:
                df_prev_check = df_plot_prev.drop(['Time', 'Index'], axis=1, errors='ignore')
                if df_plot_check.equals(df_prev_check) and not is_current_slide:
                    df_plot_prev = df_plot
                    skip_this = True
            
            if not skip_this:
                fig = plot_lvl2_with_orders(df_plot, breaks_for_plot)
                if fig is not None:
                    fig.set_size_inches(15, 10)
                    if show_gui and gui_callback:
                        gui_callback(fig, slide_idx, n_slides, file_name_out, date, slide_time=slide_time)
                        figures_list[slide_idx] = fig
                    else:
                        plt.close(fig)
                    
                    cnt_plot += 1
                    
                    if gui_obj and gui_obj.current_slide_index == slide_idx:
                        if gui_obj.priority_slide_index == slide_idx:
                            gui_obj.priority_slide_index = None
                        gui_obj.root.after(0, lambda idx=slide_idx: gui_obj._display_slide_visual_only(idx))
                    
                    if cnt_plot % 100 == 0:
                        print(f"    Processed {cnt_plot}/{n_slides} slides...")
                
                df_plot_prev = df_plot
        
        print(f"✓ Generated {cnt_plot} plot(s)")
        return figures_list, file_name_out, date
        
    except Exception as e:
        for fig in figures_list:
            try:
                plt.close(fig)
            except:
                pass
        print(f"✗ Error generating plots: {e}")
        raise

# =============================================================================
# PIPELINE
# =============================================================================

def run_pipeline(log_queue=None):
    """Run the full pipeline: Config -> Simulator -> Plots."""
    log_print = print
    if log_queue:
        def log_print(*args, **kwargs):
            msg = ' '.join(str(arg) for arg in args)
            log_queue.put(msg)
            print(*args, **kwargs)
    
    log_print("=" * 50)
    log_print("🚀 Starting Pipeline: Config → Simulator → Plots")
    log_print("=" * 50)
    
    if not LOCAL_CONFIG_TXT_PATH.exists():
        log_print(f"✗ Config file not found: {LOCAL_CONFIG_TXT_PATH}")
        return False
    
    config_txt_params = parse_config_txt(LOCAL_CONFIG_TXT_PATH)
    date = config_txt_params.get('date', '').strip()
    
    if not date:
        log_print(f"✗ Date not found in config.txt")
        return False
    
    config_json = update_config_json(LOCAL_CONFIG_JSON_PATH, config_txt_params)
    remote_file_path = f'/data/Research/Datasets/SimulatorLogs/temp_PT_{date}'
    
    ssh = None
    try:
        log_print("\n📡 Step 1: Running Simulator")
        log_print("-" * 40)
        
        ssh = connect_ssh()
        config_data = upload_config(ssh, LOCAL_CONFIG_JSON_PATH, REMOTE_CONFIG_PATH)
        success = run_simulator(ssh, SIMULATOR_PATH, config_data, log_print=log_print)
        
        if not success:
            log_print("✗ Simulator run failed")
            return False
        
        log_print("\n📊 Step 2: Generating Plots")
        log_print("-" * 40)
        
        log_print("Waiting for data file...")
        df = None
        
        for attempt in range(5):
            if attempt > 0:
                wait_time = 2 * attempt
                log_print(f"  Attempt {attempt + 1}/5, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                time.sleep(2)
            
            df = load_data_from_server(ssh, remote_file_path)
            if df is not None and not df.empty:
                # Delete temp file from server
                try:
                    sftp = ssh.open_sftp()
                    try:
                        sftp.remove(remote_file_path)
                        log_print(f"✓ Cleaned up temp file on server")
                    except Exception:
                        pass
                    finally:
                        sftp.close()
                except Exception:
                    pass
                break
        
        if df is None or df.empty:
            # Try alternative file names
            dir_path = os.path.dirname(remote_file_path)
            date_part = config_txt_params.get('date', '')
            try:
                sftp = ssh.open_sftp()
                try:
                    files = sftp.listdir(dir_path)
                    matching_files = [f for f in files if date_part in f and ('temp_PT' in f or 'PT' in f)]
                    for alt_file in matching_files[:5]:
                        alt_path = os.path.join(dir_path, alt_file)
                        log_print(f"Trying: {alt_path}")
                        df = load_data_from_server(ssh, alt_path)
                        if df is not None and not df.empty:
                            try:
                                sftp.remove(alt_path)
                                log_print(f"✓ Cleaned up temp file on server")
                            except Exception:
                                pass
                            break
                finally:
                    sftp.close()
            except Exception as e:
                log_print(f"Error searching files: {e}")
            
            if df is None or df.empty:
                log_print("✗ No data found")
                return False
        
        df, breaks_for_plot = process_data(df)
        
        ticker = config_txt_params.get('ticker', 'mgnt')
        gui_callback = getattr(log_queue, 'gui_callback', None)
        show_gui = gui_callback is not None
        gui_obj = getattr(gui_callback, '__self__', None) if gui_callback else None
        
        generate_pdfs(df, breaks_for_plot, file_name_out=ticker.lower(), date=date,
                      show_gui=show_gui, gui_callback=gui_callback, gui_obj=gui_obj)
        
        log_print("\n" + "=" * 50)
        log_print("✅ Complete! Plots displayed in Plot Viewer")
        log_print("=" * 50)
        return True
        
    except KeyboardInterrupt:
        log_print("\n⛔ Interrupted by user")
        return False
    except Exception as e:
        log_print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if ssh:
            ssh.close()
            log_print("📡 SSH connection closed")

# =============================================================================
# GUI APPLICATION
# =============================================================================

class PrintLvlGUI:
    """Main GUI application for PrintLvl with modern dark theme."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("PrintLvl")
        self.root.geometry("950x800")
        self.root.configure(bg=Theme.BG_DARK)
        self.root.minsize(800, 600)
        
        self._configure_styles()
        self._init_state()
        self._create_widgets()
        self._start_log_polling()
    
    def _configure_styles(self):
        """Configure ttk styles for modern appearance."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Frame styles
        style.configure('Dark.TFrame', background=Theme.BG_DARK)
        style.configure('Card.TFrame', background=Theme.BG_MEDIUM)
        
        # Label styles
        style.configure('Title.TLabel',
                        font=(Theme.FONT_FAMILY, 20, 'bold'),
                        background=Theme.BG_DARK,
                        foreground=Theme.TEXT_PRIMARY)
        
        style.configure('Subtitle.TLabel',
                        font=(Theme.FONT_FAMILY, 11),
                        background=Theme.BG_DARK,
                        foreground=Theme.TEXT_SECONDARY)
        
        style.configure('Header.TLabel',
                        font=(Theme.FONT_FAMILY, 10, 'bold'),
                        background=Theme.BG_MEDIUM,
                        foreground=Theme.TEXT_PRIMARY)
        
        style.configure('Field.TLabel',
                        font=(Theme.FONT_FAMILY, 9),
                        background=Theme.BG_MEDIUM,
                        foreground=Theme.TEXT_SECONDARY)
        
        style.configure('Status.TLabel',
                        font=(Theme.FONT_FAMILY, 9),
                        background=Theme.BG_LIGHT,
                        foreground=Theme.TEXT_SECONDARY,
                        padding=(10, 5))
        
        # Button styles
        style.configure('Action.TButton',
                        font=(Theme.FONT_FAMILY, 11, 'bold'),
                        background=Theme.BTN_PRIMARY_BG,
                        foreground=Theme.BTN_PRIMARY_FG,
                        padding=(20, 12))
        style.map('Action.TButton',
                  background=[('active', Theme.ACCENT_SECONDARY), ('pressed', Theme.ACCENT_PRIMARY)])
        
        style.configure('Nav.TButton',
                        font=(Theme.FONT_FAMILY, 10),
                        background=Theme.NAV_BTN_BG,
                        foreground=Theme.NAV_BTN_FG,
                        padding=(8, 6))
        style.map('Nav.TButton',
                  background=[('active', Theme.ACCENT_SECONDARY), ('pressed', Theme.NAV_BTN_BG)])
        
        style.configure('Secondary.TButton',
                        font=(Theme.FONT_FAMILY, 10),
                        background=Theme.BTN_SECONDARY_BG,
                        foreground=Theme.BTN_SECONDARY_FG,
                        padding=(12, 8))
        
        # Entry style
        style.configure('Dark.TEntry',
                        fieldbackground=Theme.BG_INPUT,
                        foreground=Theme.TEXT_PRIMARY,
                        insertcolor=Theme.TEXT_PRIMARY)
        
        # LabelFrame style
        style.configure('Card.TLabelframe',
                        background=Theme.BG_MEDIUM,
                        foreground=Theme.TEXT_PRIMARY)
        style.configure('Card.TLabelframe.Label',
                        font=(Theme.FONT_FAMILY, 10, 'bold'),
                        background=Theme.BG_MEDIUM,
                        foreground=Theme.ACCENT_SECONDARY)
    
    def _init_state(self):
        """Initialize application state."""
        self.log_queue = queue.Queue()
        self.log_queue.gui_callback = self.show_plot
        
        self.plot_window = None
        self.plot_canvas = None
        self.canvas_frame = None
        self.current_fig = None
        self.current_slide_index = 0
        self.slide_var = None
        self.time_var = None
        self.first_slide_displayed = False
        self.reference_fig_size = None
        self.plot_window_closed = False
        self.priority_slide_index = None
        self.processed_slides_count = 0
        self.total_slides_count = 0
        self.save_pdf_button = None
        self.processed_slides_label = None
        self.total_slides_label = None
        self.slide_times = {}
        self.figures_list = []
        self.suggested_filename = ''
        self.suggested_date = ''
        
        self.config_params = {}
        self._load_config()
    
    def _load_config(self):
        """Load config from config.txt."""
        if LOCAL_CONFIG_TXT_PATH.exists():
            self.config_params = parse_config_txt(LOCAL_CONFIG_TXT_PATH, silent=True)
        else:
            self.config_params = {
                'ticker': 'MGNT_TQBR',
                'date': '2025-12-11',
                'time': '22:59:51.000',
                'start_time_offset': '0',
                'end_time_offset': '1000'
            }
    
    def _create_widgets(self):
        """Create main GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding=20)
        main_frame.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Header
        header_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        
        ttk.Label(header_frame, text="📊 PrintLvl", style='Title.TLabel').pack(anchor='w')
        ttk.Label(header_frame, text="Simulator & Order Book Visualizer", style='Subtitle.TLabel').pack(anchor='w')
        
        # Config card
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ Configuration", style='Card.TLabelframe', padding=15)
        config_frame.grid(row=1, column=0, sticky='ew', pady=10)
        config_frame.columnconfigure(1, weight=1)
        
        fields = [
            ('ticker', 'Ticker', '📈'),
            ('date', 'Date (yyyy-mm-dd)', '📅'),
            ('time', 'Time (HH:MM:SS.mmm)', '🕐'),
            ('start_time_offset', 'Start Offset (ms)', '⏪'),
            ('end_time_offset', 'End Offset (ms)', '⏩'),
        ]
        
        self.entries = {}
        for row, (key, label, icon) in enumerate(fields):
            lbl = ttk.Label(config_frame, text=f"{icon} {label}", style='Field.TLabel')
            lbl.grid(row=row, column=0, sticky='w', pady=6, padx=(0, 15))
            
            entry = tk.Entry(config_frame, width=40,
                           font=(Theme.FONT_FAMILY, 10),
                           bg=Theme.BG_INPUT,
                           fg=Theme.TEXT_PRIMARY,
                           insertbackground=Theme.TEXT_PRIMARY,
                           relief='flat',
                           highlightthickness=1,
                           highlightcolor=Theme.ACCENT_PRIMARY,
                           highlightbackground=Theme.BG_LIGHT)
            entry.grid(row=row, column=1, sticky='ew', pady=6, padx=5, ipady=6)
            entry.insert(0, self.config_params.get(key, ''))
            self.entries[key] = entry
        
        # Action button
        button_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        button_frame.grid(row=2, column=0, pady=20)
        
        self.run_button = ttk.Button(
            button_frame,
            text="▶ Run Pipeline",
            command=self.run_pipeline,
            style='Action.TButton'
        )
        self.run_button.pack()
        
        # Log output card
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log Output", style='Card.TLabelframe', padding=10)
        log_frame.grid(row=3, column=0, sticky='nsew', pady=10)
        main_frame.rowconfigure(3, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            font=(Theme.FONT_MONO, 9),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief='flat',
            highlightthickness=0
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Configure log text tags for colored output
        self.log_text.tag_configure('success', foreground=Theme.ACCENT_SUCCESS)
        self.log_text.tag_configure('error', foreground=Theme.ACCENT_ERROR)
        self.log_text.tag_configure('warning', foreground=Theme.ACCENT_WARNING)
        self.log_text.tag_configure('info', foreground=Theme.ACCENT_INFO)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, style='Status.TLabel')
        status_bar.grid(row=4, column=0, sticky='ew', pady=(10, 0))
    
    def log(self, message):
        """Add message to log with color coding."""
        # Determine tag based on message content
        tag = None
        if '✓' in message or '✅' in message or 'Complete' in message:
            tag = 'success'
        elif '✗' in message or 'Error' in message or 'Failed' in message:
            tag = 'error'
        elif '⚠' in message or 'Warning' in message:
            tag = 'warning'
        elif '🔄' in message or 'Step' in message:
            tag = 'info'
        
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
    
    def _start_log_polling(self):
        """Start polling log queue."""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._start_log_polling)
    
    def show_plot(self, fig, slide_idx, total, file_name_out='mgnt', date='',
                  is_total_count=False, slide_time=None, all_slide_times=None):
        """Store figure and show in plot viewer."""
        def update_plot():
            try:
                if self.plot_window_closed:
                    return
                
                if is_total_count:
                    if total == 0:
                        return
                    
                    self.figures_list = [None] * total
                    self.processed_slides_count = 0
                    self.total_slides_count = total
                    self.slide_times = all_slide_times.copy() if all_slide_times else {}
                    self.current_slide_index = 0
                    
                    if self.slide_var:
                        self.slide_var.set("1")
                    if self.time_var and 0 in self.slide_times:
                        self.time_var.set(str(self.slide_times[0]))
                    elif self.time_var:
                        self.time_var.set("")
                    
                    if not self.plot_window_closed and (self.plot_window is None or not self.plot_window.winfo_exists()):
                        self._create_plot_window()
                    
                    self._update_labels()
                    return
                
                if fig is not None and slide_idx is not None:
                    if len(self.figures_list) <= slide_idx:
                        self.figures_list.extend([None] * (slide_idx - len(self.figures_list) + 1))
                    
                    was_new = self.figures_list[slide_idx] is None
                    self.figures_list[slide_idx] = fig
                    
                    if slide_time is not None:
                        self.slide_times[slide_idx] = slide_time
                        if slide_idx == self.current_slide_index and self.time_var:
                            self.time_var.set(str(slide_time))
                    
                    if was_new:
                        self.processed_slides_count += 1
                        self._update_labels()
                
                if not self.suggested_filename:
                    self.suggested_filename = file_name_out
                    self.suggested_date = date
                
                if self.plot_window_closed:
                    return
                
                if self.plot_window is None or not self.plot_window.winfo_exists():
                    self._create_plot_window()
                    self._update_labels()
                
                if self.figures_list and self.plot_canvas is None and not self.first_slide_displayed:
                    self.first_slide_displayed = True
                    self._display_slide_visual_only(0)
            
            except Exception:
                pass
        
        self.root.after(0, update_plot)
    
    def _update_labels(self):
        """Update processed slides and total labels."""
        if self.processed_slides_label and hasattr(self.processed_slides_label, 'winfo_exists'):
            try:
                if self.processed_slides_label.winfo_exists():
                    self.processed_slides_label.config(
                        text=f"📊 {self.processed_slides_count}/{self.total_slides_count}")
            except Exception:
                self.processed_slides_label = None
        
        if self.total_slides_label and hasattr(self.total_slides_label, 'winfo_exists'):
            try:
                if self.total_slides_label.winfo_exists():
                    self.total_slides_label.config(text=str(self.total_slides_count))
            except Exception:
                self.total_slides_label = None
        
        # Enable save button when all processed
        if self.save_pdf_button and self.processed_slides_count >= self.total_slides_count:
            try:
                if self.save_pdf_button.winfo_exists():
                    self.save_pdf_button.config(state=tk.NORMAL)
            except Exception:
                self.save_pdf_button = None
    
    def _create_plot_window(self):
        """Create plot viewer window with modern styling."""
        self.plot_window = tk.Toplevel(self.root)
        self.plot_window.title("📊 Plot Viewer")
        self.plot_window.geometry("1350x900")
        self.plot_window.configure(bg=Theme.BG_DARK)
        self.plot_window.minsize(1000, 700)
        
        self.plot_window.columnconfigure(0, weight=1)
        self.plot_window.rowconfigure(2, weight=1)
        
        # Toolbar
        toolbar = tk.Frame(self.plot_window, bg=Theme.BG_MEDIUM, padx=15, pady=10)
        toolbar.grid(row=0, column=0, sticky='ew')
        
        # Save button
        self.save_pdf_button = tk.Button(
            toolbar,
            text="💾 Save PDF",
            command=self.save_pdf_dialog,
            state=tk.DISABLED,
            font=(Theme.FONT_FAMILY, 10, 'bold'),
            bg=Theme.ACCENT_SUCCESS,
            fg='white',
            activebackground='#059669',
            activeforeground='white',
            relief='flat',
            padx=15,
            pady=8,
            cursor='hand2'
        )
        self.save_pdf_button.pack(side='left', padx=(0, 15))
        
        # Progress label
        self.processed_slides_label = tk.Label(
            toolbar,
            text=f"📊 0/0",
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_MEDIUM,
            fg=Theme.TEXT_SECONDARY
        )
        self.processed_slides_label.pack(side='left', padx=10)
        
        # Time field
        tk.Label(toolbar, text="⏱ Time:", font=(Theme.FONT_FAMILY, 10),
                 bg=Theme.BG_MEDIUM, fg=Theme.TEXT_SECONDARY).pack(side='left', padx=(20, 5))
        
        self.time_var = tk.StringVar(value="")
        time_entry = tk.Entry(
            toolbar,
            textvariable=self.time_var,
            width=20,
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief='flat',
            highlightthickness=1,
            highlightcolor=Theme.ACCENT_PRIMARY,
            highlightbackground=Theme.BG_LIGHT
        )
        time_entry.pack(side='left', padx=5, ipady=4)
        time_entry.bind('<Return>', lambda e: self._on_time_entry_change())
        time_entry.bind('<FocusOut>', lambda e: self._on_time_entry_change())
        
        # Navigation bar
        nav_bar = tk.Frame(self.plot_window, bg=Theme.BG_LIGHT, padx=15, pady=8)
        nav_bar.grid(row=1, column=0, sticky='ew')
        
        # Slide number entry
        tk.Label(nav_bar, text="Slide:", font=(Theme.FONT_FAMILY, 10),
                 bg=Theme.BG_LIGHT, fg=Theme.TEXT_SECONDARY).pack(side='left', padx=(0, 5))
        
        self.slide_var = tk.StringVar(value="1")
        slide_entry = tk.Entry(
            nav_bar,
            textvariable=self.slide_var,
            width=8,
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_INPUT,
            fg=Theme.TEXT_PRIMARY,
            insertbackground=Theme.TEXT_PRIMARY,
            relief='flat',
            justify='center'
        )
        slide_entry.pack(side='left', padx=5, ipady=4)
        slide_entry.bind('<Return>', lambda e: self._on_slide_entry_change())
        slide_entry.bind('<FocusOut>', lambda e: self._on_slide_entry_change())
        
        tk.Label(nav_bar, text="/", font=(Theme.FONT_FAMILY, 10),
                 bg=Theme.BG_LIGHT, fg=Theme.TEXT_SECONDARY).pack(side='left', padx=3)
        
        self.total_slides_label = tk.Label(
            nav_bar,
            text="0",
            font=(Theme.FONT_FAMILY, 10),
            bg=Theme.BG_LIGHT,
            fg=Theme.TEXT_PRIMARY
        )
        self.total_slides_label.pack(side='left', padx=(0, 20))
        
        # Navigation buttons
        nav_buttons = [
            ("⏪ -100", -100),
            ("◀◀ -10", -10),
            ("◀ -1", -1),
            ("▶ +1", 1),
            ("▶▶ +10", 10),
            ("⏩ +100", 100)
        ]
        
        for text, delta in nav_buttons:
            btn = tk.Button(
                nav_bar,
                text=text,
                command=lambda d=delta: self.change_slide(d),
                font=(Theme.FONT_FAMILY, 9),
                bg=Theme.NAV_BTN_BG,
                fg=Theme.NAV_BTN_FG,
                activebackground=Theme.ACCENT_SECONDARY,
                activeforeground='white',
                relief='flat',
                padx=10,
                pady=4,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)
        
        # Canvas frame
        self.canvas_frame = tk.Frame(self.plot_window, bg=Theme.BG_DARK)
        self.canvas_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=10)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(0, weight=1)
        
        self.plot_canvas = None
        self.current_fig = None
        
        # Events
        self.plot_window.protocol("WM_DELETE_WINDOW", self._on_plot_window_close)
        self.plot_window_closed = False
        
        # Keyboard bindings
        self.plot_window.bind('<Left>', lambda e: self.change_slide(-1))
        self.plot_window.bind('<Right>', lambda e: self.change_slide(1))
        self.plot_window.bind('<Up>', lambda e: self.change_slide(10))
        self.plot_window.bind('<Down>', lambda e: self.change_slide(-10))
        self.plot_window.bind('<Configure>', self._on_window_resize)
        self.plot_window.focus_set()
    
    def _on_slide_entry_change(self):
        """Handle manual slide number entry."""
        try:
            slide_num = int(self.slide_var.get())
            self.display_slide(slide_num - 1)
        except ValueError:
            self.slide_var.set(str(self.current_slide_index + 1))
    
    def _on_time_entry_change(self):
        """Handle time entry change - search for slide by time."""
        try:
            entered_time = self.time_var.get().strip()
            if not entered_time:
                return
            
            found_idx = None
            for idx in sorted(self.slide_times.keys()):
                if self.slide_times[idx] >= entered_time:
                    found_idx = idx
                    break
            
            if found_idx is not None:
                self.display_slide(found_idx)
            else:
                if self.current_slide_index in self.slide_times:
                    self.time_var.set(str(self.slide_times[self.current_slide_index]))
        except Exception:
            if self.current_slide_index in self.slide_times:
                self.time_var.set(str(self.slide_times[self.current_slide_index]))
    
    def change_slide(self, delta):
        """Change slide by delta."""
        self.display_slide(self.current_slide_index + delta)
    
    def _on_window_resize(self, event):
        """Handle window resize - update canvas size."""
        if event.widget != self.plot_window:
            return
        
        if self.plot_canvas is None or self.canvas_frame is None:
            return
        
        self.plot_window.update_idletasks()
        self.canvas_frame.update_idletasks()
        
        frame_width = self.canvas_frame.winfo_width()
        frame_height = self.canvas_frame.winfo_height()
        
        if frame_width <= 1 or frame_height <= 1:
            return
        
        if self.current_fig:
            dpi = self.current_fig.get_dpi()
            fig_width = frame_width / dpi
            fig_height = frame_height / dpi
            self.reference_fig_size = (fig_width, fig_height)
            self.current_fig.set_size_inches(fig_width, fig_height)
            self.plot_canvas.draw()
    
    def _on_plot_window_close(self):
        """Handle plot window closing."""
        self.plot_window_closed = True
        if self.plot_window:
            self.plot_window.destroy()
        
        # Clear all references
        self.plot_window = None
        self.save_pdf_button = None
        self.processed_slides_label = None
        self.total_slides_label = None
        self.slide_var = None
        self.time_var = None
        self.plot_canvas = None
        self.canvas_frame = None
    
    def display_slide(self, index):
        """Display slide at given index (user action)."""
        max_index = max(0, self.total_slides_count - 1) if self.total_slides_count > 0 else 0
        
        if self.figures_list:
            for i in range(len(self.figures_list) - 1, -1, -1):
                if self.figures_list[i] is not None:
                    max_index = max(max_index, i)
                    break
        
        index = max(0, min(index, max_index))
        self.current_slide_index = index
        
        if self.slide_var:
            self.slide_var.set(str(index + 1))
        
        if self.time_var and index in self.slide_times:
            self.time_var.set(str(self.slide_times[index]))
        elif self.time_var:
            self.time_var.set("")
        
        if index >= len(self.figures_list) or self.figures_list[index] is None:
            self.priority_slide_index = index
            return
        
        if self.priority_slide_index == index:
            self.priority_slide_index = None
        
        self._display_slide_visual_only(index)
    
    def _display_slide_visual_only(self, index):
        """Display slide visually without changing navigation state."""
        if not self.figures_list or index >= len(self.figures_list) or self.figures_list[index] is None:
            return
        
        fig = self.figures_list[index]
        
        if self.plot_canvas is None:
            if self.canvas_frame is None:
                return
            
            for _ in range(3):
                self.plot_window.update_idletasks()
                self.canvas_frame.update_idletasks()
            
            frame_width = self.canvas_frame.winfo_width()
            frame_height = self.canvas_frame.winfo_height()
            
            if frame_width <= 1 or frame_height <= 1:
                window_width = self.plot_window.winfo_width()
                window_height = self.plot_window.winfo_height()
                frame_width = max(window_width - 30, 1100)
                frame_height = max(window_height - 130, 600)
            else:
                frame_width = max(frame_width, 1100)
                frame_height = max(frame_height, 600)
            
            dpi = fig.get_dpi()
            fig_width = frame_width / dpi
            fig_height = frame_height / dpi
            
            self.reference_fig_size = (fig_width, fig_height)
            fig.set_size_inches(fig_width, fig_height)
            
            try:
                self.plot_canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
                self.plot_canvas.draw()
                self.plot_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
                self.plot_window.update_idletasks()
            except Exception:
                self.plot_canvas = None
                raise
        else:
            self.plot_window.update_idletasks()
            self.canvas_frame.update_idletasks()
            
            frame_width = self.canvas_frame.winfo_width()
            frame_height = self.canvas_frame.winfo_height()
            
            if frame_width > 1 and frame_height > 1:
                dpi = fig.get_dpi()
                fig_width = frame_width / dpi
                fig_height = frame_height / dpi
                self.reference_fig_size = (fig_width, fig_height)
                fig.set_size_inches(fig_width, fig_height)
            elif self.reference_fig_size:
                fig.set_size_inches(*self.reference_fig_size)
            
            self.current_fig = fig
            self.plot_canvas.figure = fig
            self.plot_canvas.draw()
        
        total = self.total_slides_count if self.total_slides_count > 0 else len(self.figures_list)
        self.plot_window.title(f"📊 Plot Viewer - {index + 1}/{total}")
    
    def save_pdf_dialog(self):
        """Open file save dialog and save PDFs."""
        if not self.figures_list:
            messagebox.showwarning("No Plots", "No plots available to save.")
            return
        
        date_suffix = f"_{self.suggested_date}" if self.suggested_date else ""
        suggested_name = f"{self.suggested_filename}{date_suffix}.pdf" if self.suggested_filename else f"plots{date_suffix}.pdf"
        
        LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        file_path = filedialog.asksaveasfilename(
            title="Save PDF As",
            initialdir=str(LOCAL_OUTPUT_DIR),
            initialfile=suggested_name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        saved_slide_index = self.current_slide_index
        
        if self.plot_window and self.plot_window.winfo_exists():
            self.display_slide(0)
            self.plot_window.update_idletasks()
        
        # Disable button and set wait cursor
        if self.save_pdf_button and self.save_pdf_button.winfo_exists():
            try:
                self.save_pdf_button.config(state=tk.DISABLED)
            except Exception:
                pass
        
        self.root.config(cursor="wait")
        if self.plot_window and self.plot_window.winfo_exists():
            try:
                self.plot_window.config(cursor="wait")
            except Exception:
                pass
        
        def save_thread():
            try:
                self._save_pdfs_to_file(file_path)
            finally:
                self.root.after(0, lambda: self._restore_after_save(saved_slide_index))
        
        threading.Thread(target=save_thread, daemon=True).start()
    
    def _restore_after_save(self, saved_slide_index):
        """Restore UI state after PDF save."""
        self.root.config(cursor="")
        if self.plot_window and self.plot_window.winfo_exists():
            try:
                self.plot_window.config(cursor="")
            except Exception:
                pass
        
        if self.save_pdf_button and self.save_pdf_button.winfo_exists():
            try:
                self.save_pdf_button.config(state=tk.NORMAL)
            except Exception:
                pass
        
        if self.plot_window and self.plot_window.winfo_exists():
            self.display_slide(saved_slide_index)
    
    def _save_pdfs_to_file(self, first_file_path):
        """Save all figures to PDF files."""
        file_path = Path(first_file_path)
        file_dir = file_path.parent
        file_stem = file_path.stem
        
        cnt_batch = 0
        pdf = None
        cnt_plot = 0
        total_figures = sum(1 for f in self.figures_list if f is not None) if self.figures_list else 0
        
        self.log_queue.put(f"💾 Saving {total_figures} slides to PDF...")
        
        try:
            for slide_idx in range(len(self.figures_list)):
                fig = self.figures_list[slide_idx]
                if fig is None:
                    continue
                
                if cnt_plot == 0 or cnt_plot >= BATCH_SIZE:
                    if pdf is not None:
                        pdf.close()
                    
                    cnt_batch += 1
                    cnt_plot = 0
                    
                    if cnt_batch == 1:
                        pdf_path = file_dir / f"{file_stem}.pdf"
                    else:
                        pdf_path = file_dir / f"{file_stem}_part{cnt_batch}.pdf"
                    
                    pdf = PdfPages(str(pdf_path))
                    self.log_queue.put(f"  📄 Creating: {pdf_path.name}")
                
                # Save with standard size
                current_size = fig.get_size_inches().copy()
                fig.set_size_inches(11.0, 8.5)
                
                current_fig = plt.gcf() if plt.get_fignums() else None
                current_fig_num = current_fig.number if current_fig else None
                
                plt.figure(fig.number)
                pdf.savefig(fig, bbox_inches='tight')
                
                fig.set_size_inches(*current_size)
                
                if current_fig_num is not None and current_fig_num != fig.number:
                    plt.figure(current_fig_num)
                
                cnt_plot += 1
                
                if cnt_plot % 100 == 0:
                    self.log_queue.put(f"    Saved {cnt_plot} slides...")
            
            if pdf is not None:
                pdf.close()
            
            self.log_queue.put(f"✅ Saved {total_figures} slides to {cnt_batch} PDF file(s)")
            self.log_queue.put(f"📁 Location: {file_dir}")
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", f"Saved {total_figures} plots to {cnt_batch} PDF file(s)\n{file_dir}"))
        
        except Exception as e:
            if pdf is not None:
                pdf.close()
            self.log_queue.put(f"✗ Error saving PDF: {e}")
            self.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Error saving PDF: {err}"))
    
    def run_pipeline(self):
        """Run pipeline in separate thread."""
        try:
            for key, entry in self.entries.items():
                self.config_params[key] = entry.get().strip()
            save_config_txt(LOCAL_CONFIG_TXT_PATH, self.config_params)
            self.log("✓ Config saved")
        except Exception as e:
            self.log(f"✗ Error saving config: {e}")
            messagebox.showerror("Error", f"Failed to save config: {e}")
            return
        
        # Reset state
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("🔄 Running...")
        self.figures_list = []
        self.suggested_filename = ''
        self.suggested_date = ''
        self.processed_slides_count = 0
        self.total_slides_count = 0
        self.slide_times = {}
        self.plot_window_closed = False
        self.first_slide_displayed = False
        self.priority_slide_index = None
        self.reference_fig_size = None
        self.current_slide_index = 0
        
        if self.save_pdf_button and hasattr(self.save_pdf_button, 'winfo_exists'):
            try:
                if self.save_pdf_button.winfo_exists():
                    self.save_pdf_button.config(state=tk.DISABLED)
            except Exception:
                self.save_pdf_button = None
        
        if self.slide_var:
            self.slide_var.set("1")
        if self.time_var:
            self.time_var.set("")
        
        def run_thread():
            try:
                success = run_pipeline(self.log_queue)
                if success:
                    self.log_queue.put("=" * 50)
                    self.log_queue.put("✅ Pipeline completed successfully!")
                    self.root.after(0, lambda: self.status_var.set("✅ Completed"))
                else:
                    self.log_queue.put("=" * 50)
                    self.log_queue.put("✗ Pipeline failed")
                    self.root.after(0, lambda: self.status_var.set("❌ Failed"))
            except Exception as e:
                self.log_queue.put(f"✗ Error: {e}")
                self.root.after(0, lambda: self.status_var.set("❌ Error"))
        
        threading.Thread(target=run_thread, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing."""
        try:
            for key, entry in self.entries.items():
                self.config_params[key] = entry.get().strip()
            save_config_txt(LOCAL_CONFIG_TXT_PATH, self.config_params)
        except Exception as e:
            print(f"✗ Error saving config: {e}")
        self.root.destroy()

# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point for CLI mode."""
    run_pipeline()


if __name__ == '__main__':
    if GUI_AVAILABLE and len(sys.argv) == 1:
        root = tk.Tk()
        app = PrintLvlGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    else:
        main()
