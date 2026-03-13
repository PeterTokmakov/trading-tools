# SCP_GUIDE
# hash: 8b13a0
---
# Передача файлов на irq через scp

## Как передавать файлы на irq

Используй `scp` с Tailscale конфигом для передачи файлов на irq:

```bash
scp -F /root/.ssh/tailscale_config <local_file> irq:/C:/Users/user/Documents/Cursor_coding/<remote_path>
```

## Примеры

### Передать один файл
```bash
scp -F /root/.ssh/tailscale_config /tmp/app.py irq:/C:/Users/user/Documents/Cursor_coding/trading_dashboard/app.py
```

### Передать несколько файлов
```bash
scp -F /root/.ssh/tailscale_config /tmp/app.py /tmp/requirements.txt irq:/C:/Users/user/Documents/Cursor_coding/trading_dashboard/
```

### Передать папку (с флагом -r)
```bash
scp -r -F /root/.ssh/tailscale_config /tmp/trading_tools irq:/C:/Users/user/Documents/Cursor_coding/
```

## Почему scp

- Работает напрямую через Tailscale (без VPS proxy)
- Передаёт файлы любого размера
- Не имеет ограничений по длине командной строки
- Использует SFTP протокол (надёжно)

## Проверка файлов на irq

```bash
# Проверить список файлов
python3 Projects/Peter-assistant/scripts/tailscale_exec.py irq "dir C:\\Users\\user\\Documents\\Cursor_coding\\trading-tools" user

# Прочитать файл
python3 Projects/Peter-assistant/scripts/tailscale_exec.py irq "type C:\\Users\\user\\Documents\\Cursor_coding\\trading-tools\\README.md" user
```

## Конфигурация Tailscale

Файл конфигурации: `/root/.ssh/tailscale_config`

Содержит настройки для подключения к Tailscale устройствам.
