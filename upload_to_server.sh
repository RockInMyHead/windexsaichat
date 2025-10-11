#!/bin/bash

# Скрипт для загрузки файлов на сервер
SERVER="rvs@37.110.51.35"
PORT="1100"
PASSWORD="640509040147"
REMOTE_PATH="~/windexai-project/static/"

echo "🚀 Загружаем файлы на сервер..."

# Функция для загрузки файла
upload_file() {
    local file=$1
    echo "📤 Загружаем $file..."
    
    sshpass -p "$PASSWORD" scp -P "$PORT" -o StrictHostKeyChecking=no "$file" "$SERVER:$REMOTE_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ $file успешно загружен"
    else
        echo "❌ Ошибка при загрузке $file"
        return 1
    fi
}

# Проверяем наличие sshpass
if ! command -v sshpass &> /dev/null; then
    echo "❌ sshpass не установлен. Устанавливаем..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install hudochenkov/sshpass/sshpass
        else
            echo "❌ Homebrew не найден. Установите sshpass вручную:"
            echo "brew install hudochenkov/sshpass/sshpass"
            exit 1
        fi
    else
        # Linux
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
fi

# Загружаем файлы
upload_file "static/style.css"
upload_file "static/script.js" 
upload_file "static/index.html"

echo "🎉 Все файлы загружены на сервер!"
echo "📱 Мобильная адаптивность активирована!"

