#!/bin/bash

# Интерактивный скрипт для деплоя проекта на сервер
SERVER="res@77.37.146.116"
PORT="1060"
REMOTE_PATH="~/windexai-project"

echo "🚀 Начинаем интерактивный деплой проекта на сервер $SERVER:$PORT..."
echo "📝 Вам будет предложено ввести пароль для подключения к серверу"
echo ""

# Создаем архив с проектом
echo "📦 Создаем архив проекта..."
tar -czf windexai-project.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.db' \
    --exclude='cache' \
    --exclude='uploads' \
    --exclude='test_nextjs' \
    --exclude='*.log' \
    --exclude='.env' \
    --exclude='windexai_backup_*.db' \
    --exclude='*.tar.gz' \
    .

echo "📤 Загружаем архив на сервер..."
echo "🔑 Введите пароль для подключения к серверу:"
scp -P "$PORT" -o StrictHostKeyChecking=no windexai-project.tar.gz "$SERVER:$REMOTE_PATH/"

if [ $? -eq 0 ]; then
    echo "✅ Архив успешно загружен"
else
    echo "❌ Ошибка при загрузке архива"
    exit 1
fi

echo "🔧 Настраиваем проект на сервере..."
echo "🔑 Введите пароль для подключения к серверу:"
ssh -p "$PORT" -o StrictHostKeyChecking=no "$SERVER" << 'EOF'
    cd ~/windexai-project
    
    # Распаковываем архив
    echo "📦 Распаковываем архив..."
    tar -xzf windexai-project.tar.gz
    
    # Удаляем архив
    rm windexai-project.tar.gz
    
    # Создаем виртуальное окружение если его нет
    if [ ! -d "venv" ]; then
        echo "🐍 Создаем виртуальное окружение..."
        python3 -m venv venv
    fi
    
    # Активируем виртуальное окружение и устанавливаем зависимости
    echo "📦 Устанавливаем зависимости..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Создаем .env файл если его нет
    if [ ! -f ".env" ]; then
        echo "⚙️ Создаем .env файл..."
        cp env.example .env
        echo "⚠️  ВАЖНО: Отредактируйте .env файл и добавьте ваш OpenAI API ключ!"
    fi
    
    # Создаем systemd сервис если его нет
    if [ ! -f "/etc/systemd/system/windexai.service" ]; then
        echo "🔧 Создаем systemd сервис..."
        sudo tee /etc/systemd/system/windexai.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=WindexAI Chat Platform
After=network.target

[Service]
Type=simple
User=res
WorkingDirectory=/home/res/windexai-project
Environment=PATH=/home/res/windexai-project/venv/bin
ExecStart=/home/res/windexai-project/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE_EOF
    fi
    
    # Перезагружаем systemd и запускаем сервис
    echo "🚀 Запускаем сервис..."
    sudo systemctl daemon-reload
    sudo systemctl enable windexai
    sudo systemctl restart windexai
    
    # Проверяем статус
    echo "📊 Статус сервиса:"
    sudo systemctl status windexai --no-pager
    
    echo "🎉 Проект успешно развернут!"
    echo "🌐 Приложение должно быть доступно на порту 1107"
EOF

# Удаляем локальный архив
rm windexai-project.tar.gz

echo "✅ Деплой завершен!"
echo "🌐 Проверьте доступность приложения:"
echo "   http://77.37.146.116:1107"
echo ""
echo "📝 Для управления сервисом используйте:"
echo "   sudo systemctl status windexai"
echo "   sudo systemctl restart windexai"
echo "   sudo systemctl stop windexai"
