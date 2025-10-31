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
        "статистика",
        "данные",
        "информация о",
        "расскажи про",
        "что нового",
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)


def extract_search_query(message: str) -> str:
    """Извлекает поисковый запрос из сообщения"""
    # Простая реализация - возвращает само сообщение
    # TODO: Улучшить логику извлечения поискового запроса
    return message

