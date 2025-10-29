# Инструкции для ручного деплоя WindexAI

## Проблема с автоматическим деплоем
SSH соединение с сервером `res@77.37.146.116:1060` не работает. Сервер принимает соединения, но закрывает их на этапе SSH handshake.

## Альтернативные методы деплоя

### 1. Через веб-интерфейс (если доступен)
Если на сервере есть веб-интерфейс для управления файлами:
1. Загрузите архив `windexai-project.tar.gz` через веб-интерфейс
2. Распакуйте архив в директорию `/home/res/windexai-project/`
3. Выполните команды настройки (см. ниже)

### 2. Через другой SSH порт
Попробуйте подключиться к другим портам:
```bash
ssh -p 22 res@77.37.146.116
ssh -p 2222 res@77.37.146.116
ssh -p 1061 res@77.37.146.116
# и т.д. для портов 1061-1069
```

### 3. Через SFTP
Попробуйте загрузить файлы через SFTP:
```bash
sftp -P 1060 res@77.37.146.116
# или
sftp -P 1062 res@77.37.146.116
```

## Команды для настройки на сервере

После загрузки файлов на сервер, выполните следующие команды:

```bash
# Переходим в директорию проекта
cd ~/windexai-project

# Распаковываем архив (если загрузили архив)
tar -xzf windexai-project.tar.gz
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
# Отредактируйте .env файл и добавьте ваш OpenAI API ключ!

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

## Проверка работы

После настройки приложение должно быть доступно по адресу:
- http://77.37.146.116:1107 (или другой порт, указанный в конфигурации)

## Управление сервисом

```bash
# Проверить статус
sudo systemctl status windexai

# Перезапустить
sudo systemctl restart windexai

# Остановить
sudo systemctl stop windexai

# Посмотреть логи
sudo journalctl -u windexai -f
```

## Файлы для загрузки

Создан архив `windexai-project.tar.gz` со всеми необходимыми файлами проекта.