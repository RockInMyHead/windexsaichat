#!/bin/bash

# Скрипт для запуска ngrok туннеля для WindexAI Chat
# Автор: WindexAI Assistant

echo "🚀 Запуск ngrok туннеля для WindexAI Chat..."
echo "📡 Порт: 8003"
echo ""

# Проверяем, запущен ли сервер на порту 8003
if ! lsof -i :8003 > /dev/null 2>&1; then
    echo "❌ Ошибка: Сервер не запущен на порту 8003"
    echo "💡 Сначала запустите сервер командой: python main.py"
    exit 1
fi

echo "✅ Сервер обнаружен на порту 8003"
echo "🌐 Запуск ngrok туннеля..."
echo ""

# Запускаем ngrok
ngrok http 8003 --log=stdout
