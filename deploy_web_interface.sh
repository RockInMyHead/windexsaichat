#!/bin/bash

# Скрипт для деплоя через веб-интерфейс или альтернативные методы
echo "🚀 Альтернативные методы деплоя WindexAI"
echo "======================================"
echo ""

# Создаем архив проекта
echo "📦 Создаем архив проекта..."
tar -czf windexai-project-web.tar.gz \
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

echo "✅ Архив создан: windexai-project-web.tar.gz"
echo ""

echo "🌐 Альтернативные методы деплоя:"
echo "================================"
echo ""
echo "1. 📁 ЧЕРЕЗ ВЕБ-ИНТЕРФЕЙС:"
echo "   - Откройте веб-панель управления сервером"
echo "   - Загрузите файл windexai-project-web.tar.gz"
echo "   - Распакуйте в директорию /home/res/windexai-project/"
echo "   - Выполните команды настройки (см. ниже)"
echo ""
echo "2. 🔑 ЧЕРЕЗ ДРУГОЙ SSH ПОРТ:"
echo "   - Попробуйте подключиться к другим портам:"
echo "     ssh -p 22 res@77.37.146.116"
echo "     ssh -p 2222 res@77.37.146.116"
echo "     ssh -p 1061-1069 res@77.37.146.116"
echo ""
echo "3. 📤 ЧЕРЕЗ SFTP:"
echo "   - sftp -P 1060 res@77.37.146.116"
echo "   - sftp -P 1062 res@77.37.146.116"
echo ""
echo "4. 🌐 ЧЕРЕЗ ВЕБ-ЗАГРУЗКУ:"
echo "   - Если есть веб-интерфейс для загрузки файлов"
echo "   - Загрузите архив через браузер"
echo ""

echo "🔧 КОМАНДЫ ДЛЯ НАСТРОЙКИ НА СЕРВЕРЕ:"
echo "===================================="
echo ""
echo "После загрузки файлов на сервер выполните:"
echo ""
echo "cd ~/windexai-project"
echo "tar -xzf windexai-project-web.tar.gz"
echo "rm windexai-project-web.tar.gz"
echo ""
echo "# Создаем виртуальное окружение"
echo "python3 -m venv venv"
echo "source venv/bin/activate"
echo "pip install --upgrade pip"
echo "pip install -r requirements.txt"
echo ""
echo "# Создаем .env файл"
echo "cp env.example .env"
echo "# Отредактируйте .env файл и добавьте ваш OpenAI API ключ!"
echo ""
echo "# Создаем systemd сервис"
echo "sudo tee /etc/systemd/system/windexai.service > /dev/null << 'EOF'"
echo "[Unit]"
echo "Description=WindexAI Chat Platform"
echo "After=network.target"
echo ""
echo "[Service]"
echo "Type=simple"
echo "User=res"
echo "WorkingDirectory=/home/res/windexai-project"
echo "Environment=PATH=/home/res/windexai-project/venv/bin"
echo "ExecStart=/home/res/windexai-project/venv/bin/python main.py"
echo "Restart=always"
echo "RestartSec=3"
echo ""
echo "[Install]"
echo "WantedBy=multi-user.target"
echo "EOF"
echo ""
echo "# Запускаем сервис"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable windexai"
echo "sudo systemctl restart windexai"
echo "sudo systemctl status windexai"
echo ""
echo "🎉 После настройки приложение будет доступно по адресу:"
echo "   http://77.37.146.116:1107"
echo ""
echo "📝 Управление сервисом:"
echo "   sudo systemctl status windexai"
echo "   sudo systemctl restart windexai"
echo "   sudo systemctl stop windexai"
