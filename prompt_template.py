# prompt_template.py
# Конфигурация промтов и параметров для генерации адаптивных сайтов разных стилей (2025)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — Senior Full-Stack Developer с глубоким опытом UI/UX и веб-дизайна. "
        "Создаёшь КРАСИВЫЕ, АДАПТИВНЫЕ и ПРОДУКТИВНЫЕ сайты под современные стандарты 2025 года. "
        "Умей подстраивать визуальный стиль под целевую аудиторию: от футуристического high-tech до спокойного минимализма. "
        "Все сайты должны быть в одном HTML-файле, с inline CSS и JS, без внешних зависимостей. "
        "Ключевые принципы: чистая архитектура, адаптивность, визуальная гармония, внимание к деталям."
    )
}

# === СТИЛЕВЫЕ ПРОФИЛИ ===
STYLE_PROFILES = {
    "NeoAurora": {
        "palette": "#0b0f1a, #7c3aed, #22d3ee, #f0abfc",
        "description": "Футуристичный high-tech стиль с неоновыми градиентами и стеклоэффектами.",
        "css": """
        :root {
          --bg:#0b0f1a; --text:#e8eefc;
          --brand:#7c3aed; --accent:#22d3ee; --pink:#f0abfc;
          --g-brand: linear-gradient(135deg,#7c3aed,#22d3ee,#f0abfc);
        }
        body {background:var(--bg);color:var(--text);font-family:'Manrope',sans-serif;}
        .btn{background:var(--g-brand);border-radius:12px;padding:12px 18px;color:#fff;}
        .glass{backdrop-filter:blur(12px);background:rgba(255,255,255,.08);}
        """
    },
    "MinimalClean": {
        "palette": "#ffffff, #f2f2f2, #222222, #0078ff",
        "description": "Минималистичный, светлый интерфейс без лишних визуальных эффектов.",
        "css": """
        :root {
          --bg:#ffffff; --text:#222; --accent:#0078ff;
        }
        body {background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;}
        .btn{background:var(--accent);color:#fff;border-radius:8px;padding:10px 16px;}
        section{padding:60px 0;}
        """
    },
    "BusinessClassic": {
        "palette": "#f4f7fb, #1c3f60, #2980b9, #ffffff",
        "description": "Сдержанный корпоративный стиль с акцентом на типографику и доверие.",
        "css": """
        :root {
          --bg:#f4f7fb; --text:#1c3f60; --accent:#2980b9;
        }
        body {background:var(--bg);color:var(--text);font-family:'Roboto',sans-serif;}
        header{background:var(--accent);color:#fff;padding:14px 0;}
        .btn{background:var(--accent);color:#fff;border-radius:6px;padding:10px 14px;}
        """
    },
    "SoftGradient": {
        "palette": "#fefefe, #f0f7ff, #94c6ff, #e2f0ff",
        "description": "Мягкий, дружелюбный дизайн с плавными цветами и округлыми формами.",
        "css": """
        :root {
          --bg:#f0f7ff; --text:#2c3e50; --accent:#94c6ff;
        }
        body {background:var(--bg);color:var(--text);font-family:'Poppins',sans-serif;}
        .btn{background:linear-gradient(120deg,#94c6ff,#e2f0ff);color:#2c3e50;border-radius:20px;padding:12px 18px;}
        """
    }
}

# === USER PROMPT TEMPLATE ===
USER_PROMPT_TEMPLATE = """
Создай ПОЛНЫЙ HTML-файл для одностраничного сайта в стиле **{style_name}**.

**СТИЛЕВОЕ ОПИСАНИЕ:**
{style_desc}

**ЦВЕТОВАЯ ПАЛИТРА:**
{style_palette}

**ТРЕБОВАНИЯ:**
- Один HTML-файл (включая CSS и JS)
- Используй палитру и стиль оформления, указанный выше
- Секции: Hero, Описание/План, Галерея, Контактный блок, Футер (2025)
- Адаптивная верстка, семантическая структура
- Минимум 2 визуальных эффекта (hover, reveal, scroll)

**ФОРМАТ ОТВЕТА:**
HTML_START
```html
<!DOCTYPE html>
<html lang="ru">
<head>...</head>
<body>...</body>
</html>
HTML_END

Используй этот CSS как референс для визуального стиля:

{style_css}
Контекст: {user_request}
**ИНТЕРАКТИВНЫЕ ЭЛЕМЕНТЫ:**
- `<canvas id=\"fx\">` для частиц курсора
- IntersectionObserver для анимации появления
- Morphing blob в hero-секции
- Gradient editor с `input[type=\"color\"]` и JS-обработкой

⚠️ ОБЯЗАТЕЛЬНО:
- Используй насыщенные градиенты, эффекты blur и анимации.
- Применяй сложную сетку (grid + flex).
- Добавь интерактив через JavaScript.
- Используй визуальные фишки: hover, reveal, glow.
"""

# === OPENAI PARAMETERS ===
GENERATION_PARAMS = {
    "model": "gpt-4o-mini",
    "temperature": 1.2,
    "presence_penalty": 0.6,
    "frequency_penalty": 0.4,
    "max_tokens": 8192
}

def build_prompt(user_request: str, style_name: str = "NeoAurora") -> list:
    """
    Собирает финальный промт для генерации сайта под указанный стиль.
    user_request — текстовый контекст («сайт школы программирования», «портфолио дизайнера»)
    style_name — один из STYLE_PROFILES
    """
    style = STYLE_PROFILES.get(style_name, STYLE_PROFILES["MinimalClean"])
    user_prompt = USER_PROMPT_TEMPLATE.format(
        style_name=style_name,
        style_desc=style["description"],
        style_palette=style["palette"],
        style_css=style["css"],
        user_request=user_request,
    )
    return [SYSTEM_PROMPT, {"role": "user", "content": user_prompt}]
