#!/usr/bin/env bash

# Скрипт для быстрого запуска публичного туннеля ngrok
# Проверьте, что ngrok установлен и авторизован (ngrok authtoken)

if ! command -v ngrok &> /dev/null; then
    echo "ngrok не найден. Установите ngrok: https://ngrok.com/download"
    exit 1
fi

echo "Запускаем ngrok туннель на порт 8003..."
ngrok http 8003

# Скрипт для быстрого запуска публичного туннеля ngrok
# Проверьте, что ngrok установлен и авторизован (ngrok authtoken)

if ! command -v ngrok &> /dev/null; then
    echo "ngrok не найден. Установите ngrok: https://ngrok.com/download"
    exit 1
fi

echo "Запускаем ngrok туннель на порт 8003..."
ngrok http 8003
