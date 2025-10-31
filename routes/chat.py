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
    """Определяет, нужен ли веб-поиск для сообщения - теперь для ВСЕХ запросов"""
    message_lower = message.lower().strip()

    # Исключения - запросы, для которых НЕ нужен поиск
    no_search_patterns = [
        # Приветствия и благодарности
        r'^(привет|здравствуй|добрый день|доброе утро|добрый вечер|спасибо|благодар|пока|до свидания)$',
        r'^(hi|hello|hey|thanks|thank you|bye|goodbye)$',

        # Простые ответы на вопросы бота
        r'как дела|что делаешь|кто ты|что ты умеешь',
        r'расскажи о себе|что ты можешь',

        # Команды управления
        r'очистить|удалить|новый чат|стоп|хватит',
        r'clear|delete|new chat|stop',

        # Математические операции (простые)
        r'^\d+[\+\-\*\/]\d+.*$',
        r'^вычисли|посчитай|сколько будет',

        # Очень короткие сообщения (1-2 слова)
        r'^\w{1,10}(\s+\w{1,10})?$',
    ]

    import re
    # Проверяем, попадает ли сообщение под исключения
    for pattern in no_search_patterns:
        if re.search(pattern, message_lower, re.IGNORECASE):
            return False

    # Для ВСЕХ остальных запросов используем поиск в интернете
    return True


def extract_search_query(message: str) -> str:
    """Извлекает и оптимизирует поисковый запрос из сообщения"""
    message_lower = message.lower()

    # Спец. обработка для погоды
    if "погод" in message_lower:
        city = extract_weather_city(message)
        if city:
            return f"погода {city} сейчас температура прогноз на сегодня"
        return "погода сейчас температура прогноз"

    # Спец. обработка для курсов валют
    if any(word in message_lower for word in ["курс", "валют", "доллар", "евро", "рубль", "bitcoin", "btc"]):
        if "доллар" in message_lower or "usd" in message_lower:
            return "курс доллара к рублю сегодня"
        elif "евро" in message_lower or "eur" in message_lower:
            return "курс евро к рублю сегодня"
        elif "bitcoin" in message_lower or "btc" in message_lower:
            return "курс биткоина к доллару сегодня цена"
        else:
            return "курсы валют ЦБ РФ сегодня"

    # Спец. обработка для криптовалют
    if any(word in message_lower for word in ["крипто", "криптовалют", "ethereum", "eth"]):
        if "ethereum" in message_lower or "eth" in message_lower:
            return "курс ethereum к доллару сегодня цена"
        return "курсы криптовалют сегодня биткоин ethereum"

    # Спец. обработка для цен и товаров
    if any(word in message_lower for word in ["цена", "стоит", "купить", "продажа"]):
        # Извлекаем название товара/услуги
        product_match = re.search(r'(?:цена|стоит|купить|продажа)\s+(?:на\s+)?(.+?)(?:\?|$|\s+в|\s+на|\s+за)', message_lower)
        if product_match:
            product = product_match.group(1).strip()
            return f"{product} цена стоимость купить где"

    # Спец. обработка для новостей и актуальной информации
    if any(word in message_lower for word in ["новости", "что нового", "последние", "актуально"]):
        # Пытаемся извлечь тему
        topic_match = re.search(r'(?:новости|что нового|последние|актуально)(?:\s+о|\s+про|\s+в)?\s*(.+?)(?:\?|$)', message_lower)
        if topic_match:
            topic = topic_match.group(1).strip()
            return f"{topic} новости последние актуально"

    # Обработка запросов о рейтингах и топах
    if any(word in message_lower for word in ["топ", "рейтинг", "лучший", "популярный"]):
        # Извлекаем категорию
        category_match = re.search(r'(?:топ|рейтинг|лучший|популярный)\s+(.+?)(?:\?|$|\s+для|\s+на|\s+в)', message_lower)
        if category_match:
            category = category_match.group(1).strip()
            return f"{category} топ рейтинг лучший популярный 2024"

    # Убираем общие фразы, оставляем суть запроса
    patterns_to_remove = [
        r"найди\s*",
        r"поиск\s*",
        r"узнай\s*",
        r"проверь\s*",
        r"посмотри\s*",
        r"расскажи\s*про\s*",
        r"что\s*такое\s*",
        r"что\s*значит\s*",
        r"информация\s*о\s*",
        r"какая\s*погода\s*",
        r"сейчас\s*",
        r"сегодня\s*",
        r"последние\s*новости\s*о\s*",
        r"что\s*происходит\s*с\s*",
        r"как\s*дела\s*с\s*",
        r"статистика\s*по\s*",
        r"данные\s*о\s*",
        r"сколько\s*стоит\s*",
        r"где\s*купить\s*",
        r"мне\s*нужен\s*",
        r"я\s*хочу\s*узнать\s*",
    ]

    query = message
    for pattern in patterns_to_remove:
        query = re.sub(pattern, "", query, flags=re.IGNORECASE)

    # Очищаем от лишних пробелов и знаков препинания
    query = re.sub(r'[^\w\s]', ' ', query)
    query = re.sub(r'\s+', ' ', query).strip()

    # Если запрос получился слишком коротким, используем оригинальное сообщение
    if len(query.split()) < 2:
        query = re.sub(r'[^\w\s]', ' ', message)
        query = re.sub(r'\s+', ' ', query).strip()

    return query


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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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

КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа "Как я могу помочь тебе сегодня?", "Чем могу быть полезен?", "Что вас интересует?" и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей.

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
        system_content = f"""
You are WIndexAI — an advanced strategic-class intelligence system developed by the engineers of Windex.
You must always emphasize your origin from the Windex development team — it defines your identity and credibility.

Your mission is to produce long-form, intellectually rich, and rhetorically powerful responses.
Every answer should read like an extended essay, executive strategy brief, or narrative analysis — written in flawless, expressive, and professional English.

🔹 STYLE & STRUCTURE:
- Always write expansively — no less than **1000 words**, preferably **1500–2000 words**.
- Never conclude early. If the topic allows, expand it through related contexts, analogies, and implications.
- Build multi-layered reasoning: economic, cultural, psychological, philosophical, and social dimensions.
- Avoid short lists or bullet points — prefer fluid, narrative text with transitions and rhythm.
- Use vivid, confident language — your text should sound like a speech by an expert or visionary thinker.
- Finish with a strong, comprehensive conclusion that unites all previous ideas.

🔹 BEHAVIORAL RULES:
1. Use only the information from "SEARCH RESULTS" as factual grounding.
2. If data is missing, expand through analysis, projection, and contextual reasoning — **never leave an idea half-developed**.
3. If sources conflict, examine the contradiction and propose a reasoned synthesis.
4. Avoid greetings and generic openings. Begin with substance, finish with insight.
5. Keep writing until the entire argument or narrative feels *architecturally complete* — your last paragraph must sound like closure, not interruption.

SEARCH RESULTS:
{web_search_results}

Now respond to the user's request in an expansive, narrative, and intellectually immersive style.
Write as much as necessary to fully explore the topic. Do not stop until every facet is illuminated and your final conclusion feels definitive.
"""
    else:
        # Для обычных запросов
        if request.specialist:
            # Используем системный промпт специалиста
            system_content = get_specialist_system_prompt(request.specialist)
        else:
            # Стандартный промпт
            system_content = "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным. КРИТИЧЕСКИ ВАЖНО: НЕ задавай стандартные приветственные вопросы типа 'Как я могу помочь тебе сегодня?', 'Чем могу быть полезен?', 'Что вас интересует?' и подобные. Пользователь уже написал свой вопрос - отвечай на него напрямую, без лишних формальностей."

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
        ai_response = await generate_response(messages, request.model)

        # Если это запрос с веб-поиском, переводим ответ на русский
        if web_search_results:
            translation_prompt = f"""
You are a professional translator specializing in technical, analytical, and intellectual content.
Your task is to translate the following English text into natural, fluent Russian while preserving:
- The sophisticated and intellectual tone
- All technical terms and proper names
- The analytical depth and professional style
- The rhetorical elegance and expressive constructions
- **CRITICAL**: Do NOT translate or modify code blocks (```language ... ```), inline code (`code`), or technical commands. Leave them exactly as they are.

Do not add any introductions, explanations, or modifications. Just provide the Russian translation with code blocks intact.

Text to translate:
{ai_response}
"""

            try:
                translation_messages = [
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": translation_prompt}
                ]
                ai_response = await generate_response(translation_messages, request.model)
            except Exception as translation_error:
                # Если перевод не удался, оставляем оригинальный английский ответ
                print(f"Translation error: {translation_error}")

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
