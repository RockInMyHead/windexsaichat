# flake8: noqa
import re
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Conversation as DBConversation
from database import Message as DBMessage
from database import get_db
from routes.auth import User, get_current_user
from utils.openai_client import format_messages_for_openai, generate_response
from utils.web_parser import get_comprehensive_web_info, get_web_info
from utils.web_search import format_search_results, search_web

router = APIRouter(prefix="/api/chat", tags=["chat"])


def should_search_web(message: str) -> bool:
    """Определяет, нужен ли веб-поиск для сообщения"""
    search_keywords = [
        "найди",
        "поиск",
        "актуальн",
        "новости",
        "сейчас",
        "сегодня",
        "последние",
        "тренд",
        "курс",
        "погода",
        "цены",
        "события",
        "что происходит",
        "как дела",
        "статистика",
        "данные",
        "информация о",
        "расскажи про",
        "что нового",
        "какая погода",
        "биткоин",
        "bitcoin",
        "btc",
        "криптовалют",
        "крипто",
        "ethereum",
        "доллар",
        "евро",
        "рубль",
        "валюта",
        "обмен",
        "exchange",
        "котировки",
        "котировка",
        "цена",
        "стоимость",
        "курс валют",
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)


def extract_search_query(message: str) -> str:
    """Извлекает поисковый запрос из сообщения"""
    # Спец. обработка для погоды: формируем более точный запрос
    message_lower = message.lower()
    if "погод" in message_lower:
        city = extract_weather_city(message)
        if city:
            # Формируем целевой запрос под погоду
            return f"погода {city} сейчас температура прогноз"
        # Если город не извлекли, оставляем слово погода и просим текущие данные
        return "погода сейчас температура прогноз"

    # Убираем общие фразы, оставляем суть запроса
    patterns_to_remove = [
        r"найди\s*",
        r"поиск\s*",
        r"расскажи\s*про\s*",
        r"что\s*такое\s*",
        r"информация\s*о\s*",
        r"какая\s*погода\s*",
        r"сейчас\s*",
        r"сегодня\s*",
        r"последние\s*новости\s*о\s*",
        r"что\s*происходит\s*с\s*",
        r"как\s*дела\s*с\s*",
        r"статистика\s*по\s*",
        r"данные\s*о\s*",
    ]

    query = message
    for pattern in patterns_to_remove:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)

    return query.strip()


def extract_weather_city(message: str) -> str:
    """Пытается извлечь город из запроса о погоде"""
    # Паттерны вида: "погода в Москве", "какая погода в санкт-петербурге", "погода во Владивостоке"
    match = re.search(
        r"погод[аы]\s*(?:в|во)\s+([A-Za-zА-Яа-яёЁ\-\s]+)", message, flags=re.IGNORECASE
    )
    if match:
        # Обрезаем по знакам препинания, если есть хвост
        city = match.group(1)
        city = re.split(r"[\?\!\.,;:\n\r\t]", city)[0]
        city = city.strip()
        # Нормализуем регистр
        if city:
            return city
    return ""


def get_specialist_system_prompt(specialist: str) -> str:
    """Возвращает системный промпт для специалиста"""
    prompts = {
        "mentor": """Ты - опытный ментор и карьерный консультант. Твоя задача - помочь пользователю в развитии навыков, планировании карьеры и достижении целей.

Твой стиль общения:
- Поддерживающий и мотивирующий
- Конструктивный и практичный
- Задаешь правильные вопросы для самоанализа
- Даешь конкретные советы и планы действий

Твои области экспертизы:
- Карьерное планирование и развитие
- Навыки лидерства и управления
- Постановка и достижение целей
- Работа с мотивацией и препятствиями
- Развитие профессиональных навыков""",
        "psychologist": """Ты - профессиональный психолог с опытом работы в области психического здоровья. Твоя задача - поддержать пользователя в эмоциональном благополучии и личностном развитии.

Твой стиль общения:
- Эмпатичный и понимающий
- Недирективный, но поддерживающий
- Помогаешь пользователю самому найти ответы
- Создаешь безопасную атмосферу для обсуждения

Твои области экспертизы:
- Управление стрессом и тревожностью
- Работа с эмоциями и чувствами
- Развитие эмоционального интеллекта
- Самопознание и личностный рост
- Техники релаксации и mindfulness""",
        "programmer": """Ты - senior разработчик с многолетним опытом в различных технологиях. Твоя задача - помочь пользователю с техническими вопросами, кодом и архитектурными решениями.

Твой стиль общения:
- Технически точный и детальный
- Объясняешь сложные концепции простым языком
- Даешь практические примеры кода
- Предлагаешь лучшие практики и паттерны

Твои области экспертизы:
- Разработка на различных языках программирования
- Архитектура программного обеспечения
- Алгоритмы и структуры данных
- Отладка и оптимизация кода
- Современные фреймворки и инструменты""",
        "accountant": """Ты - опытный бухгалтер и финансовый консультант. Твоя задача - помочь пользователю с вопросами учета, налогообложения и финансового планирования.

Твой стиль общения:
- Точный и профессиональный
- Объясняешь сложные финансовые концепции доступно
- Даешь практические советы по учету
- Помогаешь с планированием и оптимизацией

Твои области экспертизы:
- Бухгалтерский учет и отчетность
- Налогообложение и налоговое планирование
- Финансовый анализ и планирование
- Управление денежными потоками
- Соответствие требованиям законодательства""",
        "analyst": """Ты - опытный аналитик данных и бизнес-аналитик. Твоя задача - помочь пользователю с анализом данных, статистикой и принятием решений на основе данных.

Твой стиль общения:
- Логичный и структурированный
- Используешь данные для обоснования выводов
- Объясняешь статистические концепции доступно
- Предлагаешь конкретные методы анализа

Твои области экспертизы:
- Анализ данных и статистика
- Визуализация данных
- Машинное обучение и прогнозирование
- Бизнес-аналитика и KPI
- A/B тестирование и эксперименты""",
        "general": """Ты - универсальный AI-помощник WindexsAI. Твоя задача - помочь пользователю с любыми вопросами и задачами.

Твой стиль общения:
- Дружелюбный и отзывчивый
- Адаптируешься под потребности пользователя
- Даешь точные и полезные ответы
- Поддерживаешь конструктивный диалог

Твои возможности:
- Ответы на общие вопросы
- Помощь с творческими задачами
- Объяснение сложных концепций
- Поддержка в обучении и развитии""",
    }

    return prompts.get(specialist, prompts["general"])


# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: Optional[int] = None
    specialist: Optional[str] = None


class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    response: str
    conversation_id: int
    model_used: str
    timestamp: str


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Process chat message and return AI response"""

    # Generate conversation ID if not provided
    if not request.conversation_id:
        # Create new conversation
        conversation = DBConversation(title="Новый чат", user_id=current_user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation_id = request.conversation_id
        # Verify conversation belongs to user
        conversation = (
            db.query(DBConversation)
            .filter(
                DBConversation.id == conversation_id,
                DBConversation.user_id == current_user.id,
            )
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
            )

    # Add user message
    user_message = DBMessage(
        role="user", content=request.message, conversation_id=conversation_id
    )
    db.add(user_message)
    db.commit()

    # Проверяем, нужен ли веб-поиск
    web_search_results = ""
    if should_search_web(request.message):

        # Извлекаем поисковый запрос
        search_query = extract_search_query(request.message)
        if not search_query:
            search_query = request.message

        # Выполняем поиск с помощью комплексного парсера
        try:
            web_data = get_comprehensive_web_info(search_query)

            # Форматируем результаты для ИИ
            if "error" not in web_data:
                web_search_results = format_web_data(web_data)
            else:
                # Fallback к обычному поиску
                search_results = search_web(search_query, num_results=3)
                web_search_results = format_search_results(search_results)

        except Exception as e:
            # Fallback к обычному поиску при ошибке
            try:
                search_results = search_web(search_query, num_results=3)
                web_search_results = format_search_results(search_results)
            except Exception as e2:
                web_search_results = "Ошибка при поиске в интернете."

    # Prepare messages for OpenAI
    if web_search_results:
        # Для запросов с веб-поиском
        system_content = f"""Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex.

Твоя задача - дать полный и точный ответ на основе найденной информации.

ВАЖНО:
• Используй информацию из результатов поиска для ответа
• Если информация противоречивая, укажи это
• Ссылайся на источники когда это уместно
• Если информации недостаточно, скажи об этом честно
• Отвечай на русском языке, будь полезным и дружелюбным

РЕЗУЛЬТАТЫ ПОИСКА:
{web_search_results}

Теперь ответь на вопрос пользователя, используя эту информацию."""
    else:
        # Для обычных запросов
        if request.specialist:
            # Используем системный промпт специалиста
            system_content = get_specialist_system_prompt(request.specialist)
        else:
            # Стандартный промпт
            system_content = "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным."

    messages = [{"role": "system", "content": system_content}]

    # Get conversation messages
    conversation_messages = (
        db.query(DBMessage)
        .filter(DBMessage.conversation_id == conversation_id)
        .order_by(DBMessage.timestamp)
        .all()
    )

    for msg in conversation_messages:
        messages.append({"role": msg.role, "content": msg.content})

    # Generate AI response using OpenAI
    try:
        ai_response = generate_response(messages, request.model)
    except Exception as e:
        ai_response = f"Извините, произошла ошибка при обращении к OpenAI API. Проверьте настройки API ключа. Ошибка: {str(e)}"

    # Add AI response
    ai_message = DBMessage(
        role="assistant", content=ai_response, conversation_id=conversation_id
    )
    db.add(ai_message)

    # Update conversation title based on first user message
    if len(conversation_messages) == 1:  # First exchange
        title = (
            request.message[:50] + "..."
            if len(request.message) > 50
            else request.message
        )
        conversation.title = title

    db.commit()

    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        model_used=request.model,
        timestamp=datetime.now().isoformat(),
    )


def format_web_data(web_data: dict) -> str:
    """Форматирует данные веб-парсера для передачи ИИ"""
    if not web_data:
        return ""

    formatted_text = f"АКТУАЛЬНЫЕ ДАННЫЕ ИЗ ИНТЕРНЕТА (обновлено: {web_data.get('timestamp', 'неизвестно')}):\n\n"

    # Обработка курсов криптовалют
    if "crypto_prices" in web_data:
        formatted_text += "📈 КУРСЫ КРИПТОВАЛЮТ:\n"
        for crypto, data in web_data["crypto_prices"].items():
            change_symbol = (
                "📈"
                if data["change_24h"] > 0
                else "📉" if data["change_24h"] < 0 else "➡️"
            )
            formatted_text += f"• {crypto}: ${data['usd']:,.2f} ({data['rub']:,.0f} ₽) {change_symbol} {data['change_24h']:+.2f}%\n"
        formatted_text += "\n"

    # Обработка курсов валют
    if "exchange_rates" in web_data:
        formatted_text += "💱 КУРСЫ ВАЛЮТ (ЦБ РФ):\n"
        for currency, data in web_data["exchange_rates"].items():
            change_symbol = (
                "📈" if data["change"] > 0 else "📉" if data["change"] < 0 else "➡️"
            )
            formatted_text += f"• {data['name']} ({currency}): {data['value']:.2f} ₽ {change_symbol} {data['change']:+.4f}\n"
        formatted_text += "\n"

    # Обработка новостей
    if "news" in web_data and web_data["news"]:
        formatted_text += "📰 ПОСЛЕДНИЕ НОВОСТИ:\n"
        for i, news in enumerate(web_data["news"][:5], 1):
            formatted_text += f"{i}. {news['title']}\n"
            if news.get("url"):
                formatted_text += f"   Источник: {news['url']}\n"
        formatted_text += "\n"

    # Обработка погоды
    if "weather" in web_data:
        weather = web_data["weather"]
        formatted_text += f"🌤️ ПОГОДА В {web_data.get('city', 'городе')}:\n"
        formatted_text += f"• Температура: {weather.get('temperature', 'N/A')}\n"
        formatted_text += f"• Описание: {weather.get('description', 'N/A')}\n"
        formatted_text += f"• Влажность: {weather.get('humidity', 'N/A')}\n"
        formatted_text += f"• Ветер: {weather.get('wind', 'N/A')}\n"
        if weather.get("note"):
            formatted_text += f"• Примечание: {weather['note']}\n"
        formatted_text += "\n"

    # Обработка результатов продвинутого поиска
    if "search_type" in web_data and web_data["search_type"] == "advanced_search":
        formatted_text += (
            f"🌐 ПРОДВИНУТЫЙ ВЕБ-ПОИСК ПО ЗАПРОСУ '{web_data.get('query', '')}':\n"
        )
        formatted_text += (
            f"📊 Найдено результатов: {web_data.get('total_results', 0)}\n"
        )
        formatted_text += f"💾 Кэш-файлов: {web_data.get('cache_hits', 0)}\n\n"

        for i, result in enumerate(web_data.get("results", [])[:3], 1):
            formatted_text += f"### Результат #{result.get('rank', i)}\n"
            formatted_text += f"🔗 URL: {result.get('url', 'N/A')}\n"
            formatted_text += (
                f"📈 Релевантность: {result.get('relevance_score', 0):.2f}\n"
            )
            formatted_text += f"📄 Контент:\n{result.get('content', '')[:1500]}...\n\n"
        formatted_text += "\n"

    # Обработка результатов обычного поиска
    elif "results" in web_data and web_data["results"]:
        formatted_text += (
            f"🔍 РЕЗУЛЬТАТЫ ПОИСКА ПО ЗАПРОСУ '{web_data.get('query', '')}':\n"
        )
        for i, result in enumerate(web_data["results"][:5], 1):
            formatted_text += f"{i}. {result['title']}\n"
            if result.get("snippet"):
                formatted_text += f"   {result['snippet']}\n"
            if result.get("url"):
                formatted_text += f"   Ссылка: {result['url']}\n"
        formatted_text += "\n"

    # Обработка результатов универсального поиска
    if "search_results" in web_data and web_data["search_results"]:
        search_data = web_data["search_results"]
        formatted_text += (
            f"🌐 УНИВЕРСАЛЬНЫЙ ПОИСК ПО ЗАПРОСУ '{search_data.get('query', '')}':\n"
        )

        for i, result in enumerate(search_data["results"][:3], 1):
            formatted_text += f"{i}. {result['title']}\n"
            if result.get("snippet"):
                formatted_text += f"   {result['snippet']}\n"
            if result.get("url"):
                formatted_text += f"   Ссылка: {result['url']}\n"

            # Добавляем извлеченный контент, если есть
            if result.get("parsed_content") and "error" not in result["parsed_content"]:
                parsed = result["parsed_content"]
                if parsed.get("description"):
                    formatted_text += f"   Описание: {parsed['description'][:200]}...\n"
                if parsed.get("headings", {}).get("h1"):
                    formatted_text += (
                        f"   Заголовки: {', '.join(parsed['headings']['h1'][:3])}\n"
                    )
        formatted_text += "\n"

    # Wrap markdown tables in code fences for better readability
    lines = formatted_text.split("\n")
    wrapped_lines = []
    in_table = False
    for line in lines:
        if line.strip().startswith("|"):
            if not in_table:
                wrapped_lines.append("```markdown")
                in_table = True
            wrapped_lines.append(line)
        else:
            if in_table:
                wrapped_lines.append("```")
                in_table = False
            wrapped_lines.append(line)
    if in_table:
        wrapped_lines.append("```")
    formatted_text = "\n".join(wrapped_lines)

    return formatted_text


# Models for connection functionality
class ConnectionTestRequest(BaseModel):
    connectionCode: str


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    chatName: Optional[str] = None


class ConnectionRequest(BaseModel):
    connectionCode: str


class ConnectionResponse(BaseModel):
    success: bool
    message: str
    chatName: Optional[str] = None


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(
    request: ConnectionTestRequest, current_user: User = Depends(get_current_user)
):
    """Test connection to external chat"""

    # Валидация кода подключения
    if not request.connectionCode or len(request.connectionCode) < 4:
        return ConnectionTestResponse(
            success=False, message="Код подключения должен содержать минимум 4 символа"
        )

    # Проверяем формат кода (только буквы и цифры)
    if not re.match(r"^[a-zA-Z0-9]+$", request.connectionCode):
        return ConnectionTestResponse(
            success=False,
            message="Код подключения должен содержать только буквы и цифры",
        )

    # Симулируем проверку подключения
    # В реальном приложении здесь была бы проверка с внешним сервисом
    try:
        # Пример проверки: если код содержит "test", то это тестовый чат
        if "test" in request.connectionCode.lower():
            return ConnectionTestResponse(
                success=True,
                message="Тестовый чат доступен для подключения",
                chatName="Тестовый чат",
            )

        # Пример проверки: если код содержит "demo", то это демо чат
        if "demo" in request.connectionCode.lower():
            return ConnectionTestResponse(
                success=True,
                message="Демо чат доступен для подключения",
                chatName="Демо чат",
            )

        # Для других кодов симулируем случайный результат
        import random

        if random.random() > 0.3:  # 70% шанс успеха
            return ConnectionTestResponse(
                success=True,
                message="Чат доступен для подключения",
                chatName=f"Чат {request.connectionCode[:8]}",
            )
        else:
            return ConnectionTestResponse(
                success=False, message="Чат недоступен или код подключения неверный"
            )

    except Exception as e:
        return ConnectionTestResponse(
            success=False, message=f"Ошибка при проверке подключения: {str(e)}"
        )


@router.post("/connect", response_model=ConnectionResponse)
async def connect_to_chat(
    request: ConnectionRequest, current_user: User = Depends(get_current_user)
):
    """Connect to external chat"""

    # Валидация кода подключения
    if not request.connectionCode or len(request.connectionCode) < 4:
        return ConnectionResponse(
            success=False, message="Код подключения должен содержать минимум 4 символа"
        )

    # Проверяем формат кода (только буквы и цифры)
    if not re.match(r"^[a-zA-Z0-9]+$", request.connectionCode):
        return ConnectionResponse(
            success=False,
            message="Код подключения должен содержать только буквы и цифры",
        )

    try:
        # Симулируем подключение к чату
        # В реальном приложении здесь была бы интеграция с внешним сервисом

        # Пример подключения: если код содержит "test", то это тестовый чат
        if "test" in request.connectionCode.lower():
            return ConnectionResponse(
                success=True,
                message="Подключение к тестовому чату установлено",
                chatName="Тестовый чат",
            )

        # Пример подключения: если код содержит "demo", то это демо чат
        if "demo" in request.connectionCode.lower():
            return ConnectionResponse(
                success=True,
                message="Подключение к демо чату установлено",
                chatName="Демо чат",
            )

        # Для других кодов симулируем случайный результат
        import random

        if random.random() > 0.2:  # 80% шанс успеха
            return ConnectionResponse(
                success=True,
                message="Подключение к чату установлено",
                chatName=f"Чат {request.connectionCode[:8]}",
            )
        else:
            return ConnectionResponse(
                success=False, message="Не удалось подключиться к чату"
            )

    except Exception as e:
        return ConnectionResponse(
            success=False, message=f"Ошибка при подключении: {str(e)}"
        )
