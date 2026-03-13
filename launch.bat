@echo off
REM Trading Tools Launcher
REM hash: 5e8d2c

chcp 65001 >nul
title Trading Tools Launcher

echo ========================================
echo   🚀 Trading Tools Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python не найден. Установите Python 3.8+ и добавьте его в PATH.
    echo.
    pause
    exit /b 1
)

REM Check if launcher.py exists
if not exist "launcher.py" (
    echo ❌ Файл launcher.py не найден.
    echo.
    pause
    exit /b 1
)

REM Check if trading_tools package exists
if not exist "trading_tools\__init__.py" (
    echo ❌ Пакет trading_tools не найден.
    echo.
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist "venv\" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Не удалось создать виртуальное окружение.
        echo.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Проверка зависимостей...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Не удалось установить зависимости.
    echo.
    pause
    exit /b 1
)

REM Run launcher
echo.
echo 🚀 Запуск Trading Tools Launcher...
echo.
python launcher.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

REM Pause on exit
echo.
echo Нажмите любую клавишу для выхода...
pause >nul
