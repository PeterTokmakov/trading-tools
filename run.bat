@echo off
cd /d "C:\Users\user\Documents\TradingTools"
pythonw -m uvicorn app:app --host 0.0.0.0 --port 8505
