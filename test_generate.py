#!/usr/bin/env python3
"""Test GenerateSignals directly"""
import sys
import os

# Add modules to path
sys.path.insert(0, r'C:\Users\user\Documents\TradingTools\modules')

import yaml
from datetime import datetime

# Load settings
config_path = r'C:\Users\user\Documents\TradingTools\configs\generate_signals.yaml'
settings = yaml.safe_load(open(config_path))
print(f'Settings loaded: {list(settings.keys())}')

# Create GenerateSignals instance
from generate_signals import GenerateSignals
gs = GenerateSignals(settings)
print('GenerateSignals instance created')

# Test generate with log callback
def log_callback(message, level):
    print(f'[{level.upper()}] {message}')

print('Starting generate...')
result = gs.generate(
    start_date='01.03.2026',
    end_date='10.03.2026',
    run_features_calculator=True,
    run_rscript=False,
    run_signal_processing=False,
    run_cleanup=False,
    log_callback=log_callback
)

print(f'Result: {result}')
