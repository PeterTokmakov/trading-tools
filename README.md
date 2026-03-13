# trading_tools_README
---
# Trading Tools

Единый интерфейс для торговых инструментов на базе FastAPI + HTML/JS.

## 📊 Инструменты

- 📈 **Generate Signals** — генерация CME сигналов с автоматическим применением конфигов
- 💰 **PnL Calculator** — расчёт PnL из CSV файлов
- 📊 **PrintLvl** — симулятор и генератор графиков Level 2 order book
- 📋 **ServerLog Parser** — парсер логов сервера
- 📋 **Signal Log Parser** — парсер логов сигналов
- ⏱️ **Signal Time Converter** — конвертер времени сигналов
- 📋 **StrategiesLog Parser** — парсер логов стратегий

## 🚀 Установка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

**Зависимости:**
- `fastapi` — веб-фреймворк
- `uvicorn` — ASGI сервер
- `pydantic` — валидация данных

### 2. Запуск приложения

#### Windows (irq):
```bash
start.bat
```

#### Linux/Mac:
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8505 --reload
```

Приложение откроется в браузере по адресу: `http://localhost:8505`

## 📁 Структура проекта

```
trading-tools/
├── app.py              # FastAPI backend
├── static/
│   ├── index.html      # Main HTML с 7 вкладками
│   ├── app.js          # Frontend JavaScript
│   └── style.css       # Styles (чёрный фон)
├── modules/            # Модули для каждого инструмента
│   ├── generate_signals.py
│   ├── pnl_calculator.py
│   ├── printlvl.py
│   ├── serverlog_parser.py
│   ├── signallog_parser.py
│   ├── signal_converter.py
│   └── strategieslog_parser.py
├── requirements.txt    # Зависимости Python
├── start.bat           # Bat файл для запуска на Windows
└── README.md          # Этот файл
```

## 🔧 API Endpoints

### Generate Signals
- `POST /api/generate-signals/run` — запуск генерации сигналов
- `GET /api/generate-signals/status` — статус генерации

### PnL Calculator
- `POST /api/pnl-calculator/calculate` — расчёт PnL
- `GET /api/pnl-calculator/strategies` — список стратегий

### PrintLvl
- `POST /api/printlvl/simulate` — запуск симуляции
- `GET /api/printlvl/configs` — список конфигов

### ServerLog Parser
- `POST /api/serverlog-parser/parse` — парсинг логов
- `GET /api/serverlog-parser/logs` — список логов

### Signal Log Parser
- `POST /api/signallog-parser/parse` — парсинг логов сигналов

### Signal Time Converter
- `POST /api/signal-converter/convert` — конвертация времени

### StrategiesLog Parser
- `POST /api/strategieslog-parser/parse` — парсинг логов стратегий

### WebSocket
- `WS /ws` — real-time updates

## 🎨 Особенности

- **Unified UI** — единый интерфейс для всех инструментов
- **FastAPI + HTML/JS** — полный контроль над UI
- **Real-time updates** — WebSocket для логов и статуса
- **Responsive** — адаптивный дизайн
- **Чёрная тема** — комфортная работа в тёмное время

## 📝 Следующие шаги

1. ✅ Создать структуру проекта
2. ✅ Создать FastAPI backend
3. ✅ Создать HTML/JS frontend
4. ⏳ Интегрировать Generate Signals
5. ⏳ Интегрировать PnL Calculator
6. ⏳ Интегрировать PrintLvl
7. ⏳ Интегрировать ServerLog Parser
8. ⏳ Интегрировать Signal Log Parser
9. ⏳ Интегрировать Signal Time Converter
10. ⏳ Интегрировать StrategiesLog Parser

## 📄 Лицензия

MIT License

## 👤 Автор

Peter Tokmakov
