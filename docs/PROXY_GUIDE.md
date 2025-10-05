# 🌐 Руководство по настройке прокси в WindexAI

## Обзор

WindexAI поддерживает использование прокси-серверов для всех внешних HTTP/HTTPS запросов:
- ✅ OpenAI API (через httpx)
- ✅ Веб-поиск (через requests)
- ✅ Продвинутый веб-поиск (через requests)

## Быстрая настройка

### 1. Настройка переменных окружения

Добавьте следующие параметры в файл `.env`:

```env
# Proxy Configuration
PROXY_ENABLED=true
PROXY_HOST=45.147.183.125
PROXY_PORT=8000
PROXY_USERNAME=E31cha
PROXY_PASSWORD=hxycdk
```

### 2. Параметры

| Параметр | Описание | Обязательный |
|----------|----------|--------------|
| `PROXY_ENABLED` | Включить/выключить прокси (`true`/`false`) | Нет (по умолчанию `false`) |
| `PROXY_HOST` | IP-адрес или домен прокси-сервера | Да (если прокси включен) |
| `PROXY_PORT` | Порт прокси-сервера | Да (если прокси включен) |
| `PROXY_USERNAME` | Имя пользователя для аутентификации | Нет (если не требуется) |
| `PROXY_PASSWORD` | Пароль для аутентификации | Нет (если не требуется) |

### 3. Перезапуск приложения

После настройки переменных окружения перезапустите приложение:

```bash
# Локально
python main.py

# На сервере через screen
screen -X -S windexai quit
screen -dmS windexai bash -c 'source venv/bin/activate && python main.py'
```

## Проверка работы прокси

### Тест инициализации модулей

```bash
python -c "from utils.openai_client import openai_client; \
           from utils.web_search import web_search_engine; \
           from utils.advanced_web_search import advanced_search"
```

Вы должны увидеть:
```
🌐 Proxy enabled: 45.147.183.125:8000
✅ OpenAI client initialized successfully with proxy
🌐 WebSearchEngine: Proxy enabled 45.147.183.125:8000
```

### Проверка переменных окружения

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); \
           print('PROXY_ENABLED:', os.getenv('PROXY_ENABLED')); \
           print('PROXY_HOST:', os.getenv('PROXY_HOST'))"
```

## Архитектура

### OpenAI Client (utils/openai_client.py)

```python
# Использует httpx.Client для настройки прокси
if proxy_url:
    http_client = httpx.Client(
        proxies={
            "http://": proxy_url,
            "https://": proxy_url,
        },
        timeout=30.0
    )
    openai_client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
```

### Web Search (utils/web_search.py)

```python
# Использует requests.Session.proxies
self.session.proxies = {
    "http": proxy_url,
    "https": proxy_url,
}
```

### Advanced Web Search (utils/advanced_web_search.py)

```python
# Использует requests.Session.proxies
self.session.proxies = {
    "http": proxy_url,
    "https": proxy_url,
}
```

## Отключение прокси

Чтобы отключить прокси, установите в `.env`:

```env
PROXY_ENABLED=false
```

Или просто удалите/закомментируйте строку `PROXY_ENABLED`.

## Поддерживаемые типы прокси

- ✅ HTTP прокси
- ✅ HTTP прокси с аутентификацией (username:password)
- ✅ Работа через прокси для HTTPS трафика

## Требования

- `httpx==0.27.2` - для OpenAI клиента с прокси
- `requests==2.32.3` - для веб-поиска
- `python-dotenv==1.0.1` - для загрузки переменных окружения

## Решение проблем

### Прокси не активируется

1. Проверьте, что `PROXY_ENABLED=true` в `.env`
2. Убедитесь, что файл `.env` находится в корне проекта
3. Перезапустите приложение

### Ошибки подключения

1. Проверьте доступность прокси-сервера:
   ```bash
   curl -x http://username:password@host:port https://api.openai.com/v1/models
   ```
2. Убедитесь, что порт открыт и доступен
3. Проверьте правильность учетных данных

### Модули не загружаются

1. Убедитесь, что установлен `httpx`:
   ```bash
   pip install httpx==0.27.2
   ```
2. Проверьте логи запуска приложения

## Безопасность

⚠️ **Важно:**
- Никогда не коммитьте файл `.env` с реальными учетными данными в Git
- Используйте `.env.example` как шаблон
- Храните пароли в безопасных местах (например, в менеджере паролей)
- Регулярно меняйте пароли прокси

## Примеры использования

### Пример 1: Прокси без аутентификации

```env
PROXY_ENABLED=true
PROXY_HOST=proxy.example.com
PROXY_PORT=8080
```

### Пример 2: Прокси с аутентификацией

```env
PROXY_ENABLED=true
PROXY_HOST=45.147.183.125
PROXY_PORT=8000
PROXY_USERNAME=E31cha
PROXY_PASSWORD=hxycdk
```

### Пример 3: Отключить прокси

```env
PROXY_ENABLED=false
```

## Поддержка

Если возникли проблемы с настройкой прокси:
1. Проверьте логи приложения
2. Убедитесь в правильности всех параметров
3. Протестируйте прокси отдельно через curl

---

**Версия:** 1.0  
**Дата обновления:** 03.10.2025  
**Статус:** ✅ Работает на production

