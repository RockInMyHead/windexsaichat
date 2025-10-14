# Инструкции для ручного деплоя на сервер

## Данные сервера
- **Хост**: 77.37.146.116
- **Порт**: 1060 (или 1062)
- **Пользователь**: res
- **Пароль**: 640509040147

## Шаги для деплоя

### 1. Подготовка архива проекта
```bash
# Создаем архив с проектом (исключая ненужные файлы)
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
```

### 2. Загрузка на сервер
```bash
# Загружаем архив на сервер
scp -P 1060 windexai-project.tar.gz res@77.37.146.116:~/windexai-project/
```

### 3. Настройка на сервере
```bash
# Подключаемся к серверу
ssh -p 1060 res@77.37.146.116

# Переходим в директорию проекта
cd ~/windexai-project

# Распаковываем архив
tar -xzf windexai-project.tar.gz

# Удаляем архив
rm windexai-project.tar.gz

# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Создаем .env файл
cp env.example .env
# ВАЖНО: Отредактируйте .env файл и добавьте ваш OpenAI API ключ!

# Создаем systemd сервис
sudo tee /etc/systemd/system/windexai.service > /dev/null << 'EOF'
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
EOF

# Перезагружаем systemd и запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable windexai
sudo systemctl restart windexai

# Проверяем статус
sudo systemctl status windexai
```

### 4. Проверка работы
После выполнения всех шагов приложение должно быть доступно по адресу:
- **http://77.37.146.116:1107**

### 5. Управление сервисом
```bash
# Проверить статус
sudo systemctl status windexai

# Перезапустить
sudo systemctl restart windexai

# Остановить
sudo systemctl stop windexai

# Запустить
sudo systemctl start windexai

# Посмотреть логи
sudo journalctl -u windexai -f
```

## Возможные проблемы

### Если соединение не удается:
1. Проверьте, что сервер доступен: `ping 77.37.146.116`
2. Попробуйте другой порт (1062 вместо 1060)
3. Убедитесь, что SSH сервис запущен на сервере
4. Проверьте настройки файрвола

### Если приложение не запускается:
1. Проверьте логи: `sudo journalctl -u windexai -f`
2. Убедитесь, что .env файл настроен правильно
3. Проверьте, что все зависимости установлены
4. Убедитесь, что порт 1107 свободен

### Если нужны права sudo:
Возможно, потребуется добавить пользователя в группу sudo или использовать другого пользователя с правами администратора.
