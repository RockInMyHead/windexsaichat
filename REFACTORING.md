# Проект рефакторинга WindexAI

## Обзор изменений

Этот документ описывает комплексный рефакторинг проекта WindexAI для улучшения архитектуры, поддерживаемости и масштабируемости.

## Основные улучшения

### 1. Архитектура приложения

#### Было:
- Монолитная структура с большим количеством кода в одном файле
- Смешанная ответственность (API + бизнес-логика)
- Отсутствие dependency injection

#### Стало:
```
windexai/
├── config.py              # Централизованная конфигурация
├── core/                  # Ядро приложения
│   ├── __init__.py
│   └── database.py        # Конфигурация БД и сессии
├── schemas/               # Pydantic схемы
│   ├── __init__.py
│   ├── user.py
│   └── chat.py
├── services/              # Бизнес-логика
│   ├── auth_service.py
│   └── chat_service.py
├── dependencies/          # Dependency injection
│   ├── __init__.py
│   └── auth.py
├── routes/                # API роутеры
│   ├── auth_refactored.py
│   └── chat_refactored.py
├── main_refactored.py     # Новый entry point
└── ...
```

### 2. Конфигурация

#### config.py
- Централизованная конфигурация через Pydantic Settings
- Поддержка переменных окружения
- Типизированные настройки с валидацией

### 3. Сервисы (Business Logic)

#### AuthService
- Хэширование паролей через PassLib
- JWT токены через python-jose
- Четкое разделение ответственности

#### ChatService
- Логика обработки сообщений
- Управление разговорами
- Веб-поиск фильтры

### 4. Схемы (Pydantic Models)

#### User schemas
- UserBase, UserCreate, UserUpdate, User
- Token, TokenData для аутентификации

#### Chat schemas
- Message, Conversation модели
- ChatRequest, ChatResponse для API

### 5. Dependency Injection

#### dependencies/auth.py
- OAuth2PasswordBearer для токенов
- get_current_user dependency
- AuthService injection

### 6. API Роутеры

#### Улучшения:
- Четкое разделение роутеров
- Использование dependency injection
- Правильные HTTP статус коды
- Валидация через Pydantic

## Преимущества рефакторинга

### 1. **Поддерживаемость**
- Код разделен на логические модули
- Легче найти и исправить баги
- Упрощенное добавление новых функций

### 2. **Тестируемость**
- Dependency injection позволяет мокать зависимости
- Сервисы можно тестировать изолированно
- Четкие интерфейсы между компонентами

### 3. **Масштабируемость**
- Легко добавить новые сервисы
- Независимое масштабирование компонентов
- Четкая архитектура для роста

### 4. **Безопасность**
- CORS ограничен конкретными origins
- JWT токены с правильной валидацией
- Хэширование паролей

### 5. **Производительность**
- Конфигурируемые таймауты
- Оптимизированные запросы к БД
- Кэширование сессий

## Миграция на новую версию

### 1. Запуск нового приложения
```bash
python main_refactored.py
```

### 2. API endpoints остались те же
- `/api/auth/register`
- `/api/auth/login`
- `/api/chat`
- `/api/conversations`

### 3. База данных совместима
- Существующие таблицы работают
- Новые модели добавляются автоматически

## Следующие шаги

1. **Добавить тесты** для всех сервисов
2. **Внедрить кэширование** (Redis)
3. **Добавить rate limiting**
4. **Реализовать API versioning**
5. **Добавить monitoring** (health checks, metrics)

## Запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск с development режимом
python main_refactored.py

# Или через uvicorn напрямую
uvicorn main_refactored:app --host 0.0.0.0 --port 8003 --reload
```

## API Документация

После запуска доступна по адресу:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc
