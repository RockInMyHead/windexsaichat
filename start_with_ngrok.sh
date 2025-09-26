#!/bin/bash

# Скрипт для запуска WindexAI с ngrok
# Убедитесь, что у вас есть authtoken в ngrok.yml

echo "🚀 Запуск WindexAI с ngrok..."

# Проверяем, запущен ли уже ngrok
if pgrep -f "ngrok" > /dev/null; then
    echo "⚠️  ngrok уже запущен. Останавливаем..."
    pkill -f "ngrok"
    sleep 2
fi

# Запускаем ngrok в фоновом режиме
echo "🌐 Запуск ngrok туннеля..."
ngrok start windexai --config=ngrok.yml &
NGROK_PID=$!

# Ждем запуска ngrok
sleep 3

# Получаем публичный URL
echo "🔍 Получение публичного URL..."
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
data = json.load(sys.stdin)
for tunnel in data['tunnels']:
    if tunnel['proto'] == 'https':
        print(tunnel['public_url'])
        break
")

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Не удалось получить публичный URL"
    exit 1
fi

echo "✅ Публичный URL: $PUBLIC_URL"

# Обновляем переменную окружения для приложения
export NGROK_URL="$PUBLIC_URL"

# Запускаем FastAPI приложение
echo "🚀 Запуск FastAPI приложения..."
python3 main.py

# Очистка при завершении
echo "🛑 Остановка ngrok..."
kill $NGROK_PID

