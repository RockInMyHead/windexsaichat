#!/bin/bash

# Простой скрипт для загрузки файлов на сервер
echo "🚀 Начинаем загрузку мобильной адаптивности на сервер..."

# Создаем временные файлы с содержимым
echo "📝 Подготавливаем файлы..."

# Создаем архив с файлами
tar -czf mobile_update.tar.gz static/style.css static/script.js static/index.html

echo "📦 Архив создан: mobile_update.tar.gz"
echo "📤 Теперь нужно загрузить этот архив на сервер вручную:"
echo ""
echo "1. Скопируйте файл mobile_update.tar.gz на сервер:"
echo "   scp -P 1100 mobile_update.tar.gz rvs@37.110.51.35:~/windexai-project/"
echo ""
echo "2. Подключитесь к серверу:"
echo "   ssh rvs@37.110.51.35 -p 1100"
echo ""
echo "3. На сервере выполните:"
echo "   cd ~/windexai-project"
echo "   tar -xzf mobile_update.tar.gz"
echo "   rm mobile_update.tar.gz"
echo "   sudo systemctl restart windexai"
echo ""
echo "🎉 Мобильная адаптивность будет активирована!"

