#!/usr/bin/env python3
"""test_ssh"""

import sys
sys.path.insert(0, r'C:\Users\user\Documents\TradingTools\modules')
import yaml
settings = yaml.safe_load(open(r'C:\Users\user\Documents\TradingTools\configs\generate_signals.yaml'))
print('Settings loaded:', settings.get('REMOTE_HOST'))

import paramiko
print('Testing SSH connection...')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
private_key = paramiko.Ed25519Key.from_private_key_file(settings['SSH_KEY_PATH'])
print('Key loaded, connecting to', settings['REMOTE_HOST'])
ssh.connect(hostname=settings['REMOTE_HOST'], username=settings['SSH_USERNAME'], pkey=private_key, timeout=10)
print('SSH connected!')
ssh.close()
print('Done')
