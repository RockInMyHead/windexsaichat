# WindexAI Test Suite

Комплексная система тестирования для проекта WindexAI, включающая unit-тесты, интеграционные тесты и нагрузочное тестирование.

## Структура тестов

```
tests/
├── conftest.py              # Общие fixtures для pytest
├── requirements.txt         # Зависимости для тестирования
├── run_tests.py            # Скрипт запуска всех тестов
├── unit/                   # Unit-тесты
│   ├── test_auth_service.py
│   └── test_chat_service.py
├── integration/            # Интеграционные тесты
│   ├── test_auth_api.py
│   └── test_chat_api.py
└── load/                   # Нагрузочное тестирование
    └── locustfile.py
```

## Быстрый запуск

```bash
# Запуск всех тестов
python tests/run_tests.py

# Или запуск отдельных типов тестов
pytest tests/unit/          # Unit-тесты
pytest tests/integration/   # Интеграционные тесты
```

## Unit-тесты

### AuthService
- ✅ Хэширование паролей
- ✅ Валидация JWT токенов
- ✅ Аутентификация пользователей
- ✅ Регистрация пользователей
- ✅ Поиск пользователей

### ChatService
- ✅ Определение необходимости веб-поиска
- ✅ Создание разговоров
- ✅ Получение разговоров
- ✅ Добавление сообщений
- ✅ Генерация ответов ИИ

## Интеграционные тесты

### API Аутентификации
- ✅ Регистрация пользователей
- ✅ Логин пользователей
- ✅ Получение текущего пользователя
- ✅ Обработка ошибок аутентификации

### API Чата
- ✅ Отправка сообщений
- ✅ Получение разговоров
- ✅ Управление разговорами
- ✅ Аутентификация запросов

## Нагрузочное тестирование

Использует **Locust** для симуляции реальной нагрузки.

### Запуск нагрузочных тестов

1. **Запустите сервер:**
```bash
python main_refactored.py
```

2. **Запустите Locust в веб-интерфейсе:**
```bash
locust -f tests/load/locustfile.py --host=http://localhost:8003 --web-host=localhost --web-port=8089
```

3. **Откройте браузер:** http://localhost:8089

4. **Настройте тест:**
   - **Number of users:** 10-100
   - **Spawn rate:** 2-10 пользователей/сек
   - **Host:** http://localhost:8003

### Типы пользователей

- **WindexAIUser** - Обычный пользователь (баланс всех операций)
- **ChatHeavyUser** - Пользователь с интенсивным чатом
- **ReadOnlyUser** - Пользователь только для чтения

## Метрики производительности

Во время нагрузочного тестирования мониторьте:

### Серверные метрики
- **Response Time:** < 500ms для API
- **Error Rate:** < 1%
- **CPU Usage:** < 80%
- **Memory Usage:** < 1GB

### API метрики
- **Auth endpoints:** < 100ms
- **Chat endpoints:** < 2000ms (из-за OpenAI)
- **Database queries:** < 50ms

## Отчеты о покрытии

```bash
# Покрытие unit-тестами
pytest tests/unit/ --cov=services --cov-report=html

# Открыть отчет
open htmlcov/index.html
```

## CI/CD интеграция

Для автоматического запуска в CI:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt

      - name: Run tests
        run: python tests/run_tests.py
```

## Устранение неполадок

### Проблемы с импортами
```bash
# Убедитесь, что находитесь в корне проекта
cd /path/to/windexai

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
pip install -r tests/requirements.txt
```

### Проблемы с базой данных
```bash
# Удалите старую тестовую БД
rm -f windexai_test.db

# Перезапустите тесты
pytest tests/unit/test_auth_service.py::TestAuthService::test_create_user_success -v
```

### Проблемы с OpenAI API
```bash
# Установите переменную окружения
export OPENAI_API_KEY="your-api-key"

# Или создайте .env файл
echo "OPENAI_API_KEY=your-api-key" > .env
```

## Добавление новых тестов

### Unit-тесты
```python
# tests/unit/test_new_service.py
import pytest
from services.new_service import NewService

class TestNewService:
    def test_some_functionality(self):
        service = NewService()
        result = service.some_method()
        assert result == expected_value
```

### Интеграционные тесты
```python
# tests/integration/test_new_api.py
class TestNewAPI:
    def test_new_endpoint(self, client: TestClient):
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
```

### Нагрузочные тесты
```python
# tests/load/locustfile.py (добавить новый класс)
class NewUserType(HttpUser):
    @task
    def new_task(self):
        self.client.get("/api/new-endpoint")
```

## Производительность тестов

- **Unit-тесты:** < 30 секунд
- **Integration-тесты:** < 2 минуты
- **Load-тесты:** 5-15 минут (зависит от конфигурации)

## Мониторинг и алерты

Настройте алерты при:
- Падении тестов > 5%
- Увеличении response time > 20%
- Увеличении error rate > 2%
