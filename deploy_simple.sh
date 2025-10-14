#!/bin/bash

# Простой скрипт для деплоя - создает архив и показывает команды для загрузки
echo "🚀 Подготавливаем проект для деплоя..."

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

echo "✅ Архив создан: windexai-project.tar.gz"
echo ""
echo "📤 Теперь выполните следующие команды для загрузки на сервер:"
echo ""
echo "1. Загрузите архив на сервер:"
echo "   scp -P 1060 windexai-project.tar.gz res@77.37.146.116:~/windexai-project/"
echo ""
echo "2. Подключитесь к серверу:"
echo "   ssh -p 1060 res@77.37.146.116"
echo ""
echo "3. На сервере выполните:"
echo "   cd ~/windexai-project"
echo "   tar -xzf windexai-project.tar.gz"
echo "   rm windexai-project.tar.gz"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   cp env.example .env"
echo "   # Отредактируйте .env файл и добавьте ваш OpenAI API ключ!"
echo "   python main.py"
echo ""
echo "🌐 После запуска приложение будет доступно на:"
echo "   http://77.37.146.116:1107"
echo ""
echo "📝 Подробные инструкции сохранены в файле: manual_deploy_instructions.md"
