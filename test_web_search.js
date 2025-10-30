// Тест функций автоматического поиска
const testMessages = [
    "Какая погода в Москве сегодня?",
    "Курс доллара к рублю",
    "Расскажи про искусственный интеллект",
    "Сколько стоит iPhone 15?",
    "Что происходит в мире новостей?",
    "Лучшие рестораны в СПб",
    "Как приготовить борщ?",
    "Курс биткоина сегодня",
    "Новости технологий",
    "Где купить квартиру в Москве?"
];

// Функция проверки поиска (копия из основного кода)
function shouldSearchWeb(message) {
    const message_lower = message.toLowerCase();

    const search_keywords = [
        "найди", "поиск", "актуальн", "новости", "сейчас", "сегодня",
        "последние", "тренд", "курс", "погода", "цены", "события",
        "что происходит", "статистика", "данные", "информация о",
        "расскажи про", "что нового", "какая погода", "биткоин",
        "bitcoin", "btc", "криптовалют", "крипто", "ethereum",
        "доллар", "евро", "рубль", "валюта", "обмен", "exchange",
        "котировки", "котировка", "цена", "стоимость", "курс валют",
        "узнай", "проверь", "посмотри", "сколько стоит", "где купить",
        "рейтинг", "топ", "лучший", "популярный"
    ];

    const current_info_keywords = [
        "текущий", "теперь", "на данный момент", "в настоящее время",
        "последние новости", "свежие данные", "актуальные цены",
        "сегодняшний", "завтрашний", "на этой неделе", "в этом месяце"
    ];

    const question_words = [
        "сколько", "какой", "где", "когда", "почему", "как", "кто",
        "что такое", "что значит", "как работает", "как использовать"
    ];

    const topics_needing_search = [
        "курс валют", "погода", "новости", "цены", "акции", "криптовалюта",
        "спорт", "политика", "экономика", "технологии", "наука",
        "здоровье", "медицина", "образование", "работа", "вакансии"
    ];

    if (search_keywords.some(keyword => message_lower.includes(keyword))) {
        return true;
    }

    if (current_info_keywords.some(keyword => message_lower.includes(keyword))) {
        return true;
    }

    const has_question = question_words.some(q_word => message_lower.includes(q_word));
    const has_topic = topics_needing_search.some(topic => message_lower.includes(topic));

    if (has_question && has_topic) {
        return true;
    }

    const words = message.split();
    if (words.length <= 8 && has_question) {
        return true;
    }

    const yearPattern = /\b(20\d{2}|19\d{2})\b/;
    const ratingPattern = /\b(топ|рейтинг|лучш|популярн|самый)\b/;
    const pricePattern = /\b(цена|стоимость|стоит|купить|продажа)\b/;

    if (yearPattern.test(message) || ratingPattern.test(message_lower) || pricePattern.test(message_lower)) {
        return true;
    }

    return false;
}

console.log("Тестирование автоматического поиска в интернете:\n");

testMessages.forEach((message, index) => {
    const willSearch = shouldSearchWeb(message);
    console.log(`${index + 1}. "${message}"`);
    console.log(`   Будет искать в интернете: ${willSearch ? '✅ ДА' : '❌ НЕТ'}\n`);
});




