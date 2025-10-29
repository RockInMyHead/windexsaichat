# flake8: noqa
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Conversation as DBConversation
from database import Message as DBMessage
from database import get_db
from routes.auth import User, get_current_user
from utils.openai_client import openai_client
from utils.web_search import format_search_results, search_web
from prompt_template import build_prompt, GENERATION_PARAMS

router = APIRouter()

# Глобальная переменная для хранения текущих мыслей LLM
current_llm_thoughts = {}

# Библиотека различных стилей дизайна для разнообразия
DESIGN_STYLES = {
    "modern_minimalist": {
        "name": "Современный минимализм",
        "colors": ["#ffffff", "#f8f9fa", "#6c757d", "#343a40"],
        "gradients": ["linear-gradient(135deg, #667eea 0%, #764ba2 100%)"],
        "effects": ["чистые линии", "много белого пространства", "минималистичная типографика"]
    },
    "dark_futuristic": {
        "name": "Темный футуризм",
        "colors": ["#0a0a0a", "#1a1a1a", "#00ff88", "#0088ff"],
        "gradients": ["linear-gradient(45deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a0a 100%)"],
        "effects": ["неоновые акценты", "темная тема", "голографические эффекты"]
    },
    "vibrant_creative": {
        "name": "Яркий креатив",
        "colors": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24"],
        "gradients": ["linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #f9ca24)"],
        "effects": ["яркие цвета", "игривые анимации", "креативные формы"]
    },
    "elegant_luxury": {
        "name": "Элегантная роскошь",
        "colors": ["#2c3e50", "#34495e", "#e74c3c", "#f39c12"],
        "gradients": ["linear-gradient(135deg, #2c3e50 0%, #34495e 100%)"],
        "effects": ["золотые акценты", "элегантная типографика", "роскошные тени"]
    },
    "nature_organic": {
        "name": "Природная органика",
        "colors": ["#27ae60", "#2ecc71", "#16a085", "#f1c40f"],
        "gradients": ["linear-gradient(135deg, #27ae60 0%, #2ecc71 100%)"],
        "effects": ["органические формы", "природные цвета", "мягкие переходы"]
    },
    "tech_cyberpunk": {
        "name": "Техно-киберпанк",
        "colors": ["#000000", "#ff0080", "#00ffff", "#ffff00"],
        "gradients": ["linear-gradient(45deg, #000000 0%, #ff0080 50%, #00ffff 100%)"],
        "effects": ["киберпанк-эстетика", "неоновые эффекты", "технологичные элементы"]
    }
}

def get_design_style_variation():
    """Возвращает случайный стиль дизайна для разнообразия"""
    import random
    style_key = random.choice(list(DESIGN_STYLES.keys()))
    return DESIGN_STYLES[style_key]

async def send_llm_thought(conversation_id: str, icon: str, text: str):
    """Отправляет мысль LLM в реальном времени"""
    if conversation_id and conversation_id in current_llm_thoughts:
        current_llm_thoughts[conversation_id].append({
            "icon": icon,
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        # Ограничиваем количество мыслей
        if len(current_llm_thoughts[conversation_id]) > 10:
            current_llm_thoughts[conversation_id] = current_llm_thoughts[conversation_id][-10:]

@router.get("/api/ai-editor/thoughts/{conversation_id}")
async def get_llm_thoughts(conversation_id: str, current_user: User = Depends(get_current_user)):
    """Получает текущие мысли LLM для конкретной беседы"""
    thoughts = current_llm_thoughts.get(conversation_id, [])
    return {"thoughts": thoughts}


class AIEditorRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    conversation_id: Optional[int] = None
    mode: str = "lite"  # "lite" or "pro"
    use_two_stage: bool = True  # Use two-stage LLM system


class AIEditorResponse(BaseModel):
    content: str
    conversation_id: int
    status: str
    timestamp: str


class ElementEditRequest(BaseModel):
    element_type: str
    current_text: str
    edit_instruction: str
    html_content: str


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
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)


async def architect_llm(user_request: str, mode: str) -> Dict:
    """Первый LLM - Архитектор: анализирует запрос и планирует архитектуру"""
    print(f"🏗️ Architect LLM: Planning architecture for mode '{mode}'")
    
    # Получаем случайный стиль дизайна для разнообразия
    design_style = get_design_style_variation()
    print(f"🎨 Selected design style: {design_style['name']}")
    
    architect_prompt = """Ты - Senior Software Architect с креативным мышлением. Твоя задача - проанализировать запрос пользователя и создать УНИКАЛЬНЫЙ и ИННОВАЦИОННЫЙ план разработки.

**ВЫБРАННЫЙ СТИЛЬ ДИЗАЙНА:** """ + design_style['name'] + """
**ЦВЕТОВАЯ ПАЛИТРА:** """ + ', '.join(design_style['colors']) + """
**ГРАДИЕНТЫ:** """ + ', '.join(design_style['gradients']) + """
**ВИЗУАЛЬНЫЕ ЭФФЕКТЫ:** """ + ', '.join(design_style['effects']) + """

**ЗАПРОС ПОЛЬЗОВАТЕЛЯ:** """ + user_request + """
**РЕЖИМ:** """ + mode + """

**ТВОЯ ЗАДАЧА:**
1. Проанализировать требования и найти УНИКАЛЬНЫЕ решения
2. Создать КРЕАТИВНЫЙ пошаговый план разработки (минимум 4-6 шагов)
3. Разбить на конкретные задачи с ИННОВАЦИОННЫМИ подходами
4. Для каждой задачи указать, какой код нужно сгенерировать
5. Думай ВНЕ СТАНДАРТНЫХ РАМОК и предлагай НЕОБЫЧНЫЕ решения
6. ОБЯЗАТЕЛЬНО используй выбранный стиль дизайна: """ + design_style['name'] + """
7. Интегрируй цветовую палитру и визуальные эффекты в план

КРЕАТИВНЫЕ ПРИМЕРЫ НАЗВАНИЙ ЗАДАЧ:
- "Создание интерактивного хедера с анимированной навигацией"
- "Создание hero-секции с 3D эффектами и параллаксом"
- "Создание секции услуг с hover-анимациями и микроинтеракциями"
- "Создание секции о компании с timeline и прогресс-барами"
- "Создание секции контактов с интерактивной картой"
- "Создание футера с анимированными иконками соцсетей"
- "Добавление продвинутых CSS анимаций и переходов"
- "Добавление JavaScript интерактивности с эффектами"
- "Создание уникальных секций с нестандартными лейаутами"
- "Добавление инновационных UI элементов и компонентов"

**ФОРМАТ ОТВЕТА (строго JSON):**
{{
    "analysis": "Краткий анализ требований пользователя",
    "steps": [
        {{
            "id": 1,
            "name": "Создание хедера с навигацией",
            "description": "Создать шапку сайта с логотипом и меню навигации",
            "code_type": "html",
            "priority": "high",
            "dependencies": []
        }},
        {{
            "id": 2,
            "name": "Создание hero-секции",
            "description": "Создать главную секцию с заголовком и призывом к действию",
            "code_type": "html",
            "priority": "high",
            "dependencies": [1]
        }},
        {{
            "id": 3,
            "name": "Создание секции услуг",
            "description": "Создать секцию с описанием услуг компании",
            "code_type": "html",
            "priority": "high",
            "dependencies": [2]
        }},
        {{
            "id": 4,
            "name": "Создание футера",
            "description": "Создать подвал сайта с контактной информацией",
            "code_type": "html",
            "priority": "medium",
            "dependencies": [3]
        }},
        {{
            "id": 5,
            "name": "Добавление стилей",
            "description": "Добавить CSS стили для всех секций",
            "code_type": "css",
            "priority": "high",
            "dependencies": [4]
        }},
        {{
            "id": 6,
            "name": "Добавление интерактивности",
            "description": "Добавить JavaScript для интерактивных элементов",
            "code_type": "javascript",
            "priority": "medium",
            "dependencies": [5]
        }}
    ],
    "final_structure": "Единый HTML файл с встроенными CSS и JavaScript"
}}

ВАЖНО:
- Для Lite режима: создавай задачи для одного HTML файла
- Для Pro режима: создавай задачи для Next.js компонентов
- Создавай МИНИМУМ 4-6 детальных шагов
- Каждая задача должна быть конкретной и выполнимой
- Названия задач должны быть краткими и понятными
- Учитывай зависимости между задачами
- НЕ включай время выполнения или технические детали в названия задач"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": architect_prompt},
                {"role": "user", "content": user_request}
            ],
            temperature=0.9
        )
        
        content = response.choices[0].message.content
        print(f"🏗️ Architect response: {content[:200]}...")
        print(f"🏗️ Full architect response length: {len(content)} characters")
        
        # Парсим JSON ответ
        import json
        try:
            plan = json.loads(content)
            print(f"🏗️ Successfully parsed architect plan with {len(plan.get('steps', []))} steps")
            for i, step in enumerate(plan.get('steps', []), 1):
                print(f"🏗️ Step {i}: {step.get('name', 'Unknown')} ({step.get('code_type', 'unknown')})")
            return plan
        except json.JSONDecodeError:
            # Если JSON невалидный, создаем базовый план
            return {
                "analysis": f"Создание {mode} проекта по запросу: {user_request}",
                "steps": [
                    {
                        "id": 1,
                        "name": "Создание хедера с навигацией",
                        "description": "Создать шапку сайта с логотипом и меню навигации",
                        "code_type": "html",
                        "priority": "high",
                        "dependencies": []
                    },
                    {
                        "id": 2,
                        "name": "Создание hero-секции",
                        "description": "Создать главную секцию с заголовком и призывом к действию",
                        "code_type": "html",
                        "priority": "high",
                        "dependencies": [1]
                    },
                    {
                        "id": 3,
                        "name": "Создание основного контента",
                        "description": "Создать секции с основным контентом сайта",
                        "code_type": "html",
                        "priority": "high",
                        "dependencies": [2]
                    },
                    {
                        "id": 4,
                        "name": "Создание футера",
                        "description": "Создать подвал сайта с контактной информацией",
                        "code_type": "html",
                        "priority": "medium",
                        "dependencies": [3]
                    },
                    {
                        "id": 5,
                        "name": "Добавление стилей",
                        "description": "Добавить CSS стили для всех секций",
                        "code_type": "css",
                        "priority": "high",
                        "dependencies": [4]
                    },
                    {
                        "id": 6,
                        "name": "Добавление интерактивности",
                        "description": "Добавить JavaScript для интерактивных элементов",
                        "code_type": "javascript",
                        "priority": "medium",
                        "dependencies": [5]
                    }
                ],
                "final_structure": "Единый HTML файл с встроенными CSS и JavaScript"
            }
            
    except Exception as e:
        print(f"❌ Architect LLM error: {e}")
        return {
            "analysis": f"Создание {mode} проекта",
            "steps": [
                {"id": 1, "name": "Создание хедера с навигацией", "description": "Создать шапку сайта", "code_type": "html", "priority": "high", "dependencies": []},
                {"id": 2, "name": "Создание hero-секции", "description": "Создать главную секцию", "code_type": "html", "priority": "high", "dependencies": [1]},
                {"id": 3, "name": "Создание основного контента", "description": "Создать секции с контентом", "code_type": "html", "priority": "high", "dependencies": [2]},
                {"id": 4, "name": "Создание футера", "description": "Создать подвал сайта", "code_type": "html", "priority": "medium", "dependencies": [3]},
                {"id": 5, "name": "Добавление стилей", "description": "Добавить CSS стили", "code_type": "css", "priority": "high", "dependencies": [4]},
                {"id": 6, "name": "Добавление интерактивности", "description": "Добавить JavaScript", "code_type": "javascript", "priority": "medium", "dependencies": [5]}
            ],
            "final_structure": "HTML файл"
        }


async def developer_llm(task: Dict, mode: str, context: str = "") -> str:
    """Второй LLM - Разработчик: генерирует код для конкретной задачи"""
    print(f"👨‍💻 Developer LLM: Generating {task['code_type']} for task '{task['name']}'")
    
    developer_prompt = f"""Ты - Senior Full-Stack Developer с экспертизой в современном UI/UX дизайне. Твоя задача - создать ПРОФЕССИОНАЛЬНЫЙ, СОВРЕМЕННЫЙ и ВИЗУАЛЬНО ПРИВЛЕКАТЕЛЬНЫЙ код.

**РЕЖИМ:** {mode}
**ЗАДАЧА:** {task['name']}
**ОПИСАНИЕ:** {task['description']}
**ТИП КОДА:** {task['code_type']}
**КОНТЕКСТ:** {context}

🎨 СОВРЕМЕННЫЕ ТРЕБОВАНИЯ К ДИЗАЙНУ:
• Используй современные CSS переменные из :root (--primary-color, --secondary-color, --accent-color, --text-color, --bg-color, --shadow, --border-radius)
• Применяй современные тени и эффекты (box-shadow, text-shadow, backdrop-filter)
• Создавай плавные анимации и переходы (transition, transform, cubic-bezier)
• Используй современную типографику с правильной иерархией
• Применяй градиенты и современные цветовые схемы
• Добавляй hover-эффекты и микроинтеракции
• Создавай визуальную иерархию с правильным spacing
• Используй современные лейауты и композиции

📱 ТРЕБОВАНИЯ К АДАПТИВНОСТИ:
• Mobile-first подход с правильными breakpoints
• Responsive дизайн для всех устройств (320px, 768px, 1024px, 1440px)
• Используй CSS Grid и Flexbox для лейаутов
• Адаптивные изображения с правильными размерами
• Touch-friendly элементы на мобильных устройствах
• Правильные размеры шрифтов для разных экранов

💻 ТРЕБОВАНИЯ К КОДУ:
• Семантические HTML теги (header, main, section, article, footer, nav)
• Используй CSS переменные для консистентности
• Современные CSS техники (Grid, Flexbox, clamp(), min(), max())
• Чистый и читаемый код с правильной структурой
• Комментарии для сложных участков
• Оптимизированная производительность

🖼️ ИСТОЧНИКИ ИЗОБРАЖЕНИЙ:
- https://picsum.photos/800/600 (случайные качественные изображения)
- https://source.unsplash.com/800x600/?business
- https://source.unsplash.com/800x600/?technology
- https://source.unsplash.com/800x600/?office
- https://source.unsplash.com/800x600/?team
- https://source.unsplash.com/800x600/?product
- https://source.unsplash.com/800x600/?fitness
- https://source.unsplash.com/800x600/?medical
- https://source.unsplash.com/800x600/?education
- https://source.unsplash.com/800x600/?architecture

🎯 СПЕЦИАЛЬНЫЕ ТРЕБОВАНИЯ:
• Для HTML: используй семантические теги, правильную структуру и современные атрибуты
• Для CSS: создавай современные стили с использованием CSS переменных, градиентов, теней и анимаций
• Для JavaScript: добавляй плавные анимации, интерактивность и современные API
• ВСЕГДА используй адаптивный дизайн с правильными breakpoints
• ВСЕГДА добавляй красивые визуальные эффекты и анимации
• ВСЕГДА используй актуальный год 2025 в копирайте и датах
• ВСЕГДА применяй современные UI/UX принципы

**ФОРМАТ ОТВЕТА:**
Верни ТОЛЬКО код без дополнительных объяснений. Код должен быть готов к использованию и соответствовать современным стандартам UI/UX дизайна."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": developer_prompt},
                {"role": "user", "content": f"Сгенерируй {task['code_type']} код для: {task['description']}"}
            ],
            temperature=0.8
        )
        
        code = response.choices[0].message.content.strip()
        
        # Очищаем код от markdown-разметки
        import re
        
        # Универсальная очистка от всех видов markdown-разметки
        code_type = task['code_type']
        
        # Удаляем все возможные варианты markdown-разметки
        patterns_to_remove = [
            rf'^```{code_type}\s*',  # ```javascript, ```css, ```html
            rf'^```js\s*',           # ```js
            rf'^```\s*',             # ```
            rf'\s*```$',             # ``` в конце
        ]
        
        for pattern in patterns_to_remove:
            code = re.sub(pattern, '', code, flags=re.MULTILINE)
        
        # Убираем лишние пробелы и переносы строк
        code = code.strip()
        
        print(f"🧹 Cleaned {code_type} code from markdown formatting")
        
        print(f"👨‍💻 Developer generated {len(code)} characters of {task['code_type']} code")
        print(f"👨‍💻 Developer response preview: {code[:100]}...")
        print(f"👨‍💻 Task '{task['name']}' completed successfully")
        return code
        
    except Exception as e:
        print(f"❌ Developer LLM error: {e}")
        return f"<!-- Error generating {task['code_type']} code -->"


async def combine_code_parts(parts: List[Dict], mode: str) -> str:
    """Объединяет части кода в единый файл"""
    print(f"🔧 Combining {len(parts)} code parts for {mode} mode")
    
    if mode == "lite":
        # Для Lite режима создаем единый HTML файл
        html_body_fragments: List[str] = []
        css_parts: List[str] = []
        js_parts: List[str] = []
        
        import re
        
        def extract_from_html(html: str) -> Dict[str, str]:
            """Возвращает body, styles, scripts из HTML части, удаляя дубликаты оболочек."""
            if not html:
                return {"body": "", "styles": "", "scripts": ""}
            text = html.strip()
            # Удаляем возможный DOCTYPE и обертки html/head
            text = re.sub(r"<!DOCTYPE[^>]*>", "", text, flags=re.IGNORECASE)
            # Собираем стили
            styles = "\n".join(m.group(1).strip() for m in re.finditer(r"<style[^>]*>([\s\S]*?)</style>", text, flags=re.IGNORECASE))
            # Собираем скрипты (только JS, без type проверки для простоты)
            scripts = "\n".join(m.group(1).strip() for m in re.finditer(r"<script[^>]*>([\s\S]*?)</script>", text, flags=re.IGNORECASE))
            # Вырезаем style/script из фрагмента
            text_wo_assets = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
            text_wo_assets = re.sub(r"<script[\s\S]*?</script>", "", text_wo_assets, flags=re.IGNORECASE)
            # Достаем содержимое body если есть
            body_match = re.search(r"<body[^>]*>([\s\S]*?)</body>", text_wo_assets, flags=re.IGNORECASE)
            if body_match:
                body = body_match.group(1).strip()
            else:
                # Если нет body, пробуем убрать <html>/<head>
                tmp = re.sub(r"<head[\s\S]*?</head>", "", text_wo_assets, flags=re.IGNORECASE)
                tmp = re.sub(r"</?html[^>]*>", "", tmp, flags=re.IGNORECASE)
                body = tmp.strip()
            return {"body": body, "styles": styles, "scripts": scripts}
        
        for part in parts:
            print(f"🔧 Processing part: {part['type']} - {len(part['code'])} chars")
            if part['type'] == 'html':
                extracted = extract_from_html(part['code'])
                if extracted['styles']:
                    css_parts.append(extracted['styles'])
                if extracted['scripts']:
                    js_parts.append(extracted['scripts'])
                html_body_fragments.append(extracted['body'])
            elif part['type'] == 'css':
                css_parts.append(part['code'])
            elif part['type'] == 'javascript':
                # Иногда в ответ попадают мусорные маркеры 'css'/'html' — чистим
                code = re.sub(r"^\s*(html|css)\s*$", "", part['code'], flags=re.IGNORECASE|re.MULTILINE)
                js_parts.append(code)
        
        print(f"🔧 Parts summary: {len(html_body_fragments)} HTML bodies, {len(css_parts)} CSS, {len(js_parts)} JS")
        
        # Объединяем в единый HTML файл
        html_content = ("\n".join(f for f in html_body_fragments if f)) or "<!-- Error generating html code -->"
        css_content = ("\n".join(c for c in css_parts if c)) or "/* No CSS generated */"
        js_content = ("\n".join(j for j in js_parts if j)) or "// No JavaScript generated"
        
        combined_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Website</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        /* Modern CSS Reset */
        *, *::before, *::after {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        /* CSS Variables for consistent design */
        :root {{
            --primary-color: #3b82f6;
            --secondary-color: #1e40af;
            --accent-color: #f59e0b;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --text-color: #1f2937;
            --text-light: #6b7280;
            --text-muted: #9ca3af;
            --bg-color: #ffffff;
            --bg-light: #f9fafb;
            --bg-dark: #111827;
            --border-color: #e5e7eb;
            --border-light: #f3f4f6;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            --border-radius: 8px;
            --border-radius-lg: 12px;
            --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        
        /* Base typography */
        html {{
            font-size: 16px;
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        /* Typography scale */
        h1, h2, h3, h4, h5, h6 {{
            font-weight: 600;
            line-height: 1.2;
            margin-bottom: 0.5em;
        }}
        
        h1 {{ font-size: 2.5rem; }}
        h2 {{ font-size: 2rem; }}
        h3 {{ font-size: 1.5rem; }}
        h4 {{ font-size: 1.25rem; }}
        h5 {{ font-size: 1.125rem; }}
        h6 {{ font-size: 1rem; }}
        
        p {{
            margin-bottom: 1rem;
        }}
        
        /* Modern button styles */
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 500;
            border-radius: var(--border-radius);
            border: none;
            cursor: pointer;
            transition: var(--transition);
            text-decoration: none;
            white-space: nowrap;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            box-shadow: var(--shadow);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }}
        
        .btn-secondary {{
            background: var(--bg-light);
            color: var(--text-color);
            border: 1px solid var(--border-color);
        }}
        
        .btn-secondary:hover {{
            background: var(--border-light);
            transform: translateY(-1px);
        }}
        
        /* Container and layout */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        
        .section {{
            padding: 4rem 0;
        }}
        
        /* Card component */
        .card {{
            background: var(--bg-color);
            border-radius: var(--border-radius-lg);
            box-shadow: var(--shadow);
            padding: 2rem;
            transition: var(--transition);
        }}
        
        .card:hover {{
            transform: translateY(-4px);
            box-shadow: var(--shadow-xl);
        }}
        
        /* Grid system */
        .grid {{
            display: grid;
            gap: 2rem;
        }}
        
        .grid-2 {{ grid-template-columns: repeat(2, 1fr); }}
        .grid-3 {{ grid-template-columns: repeat(3, 1fr); }}
        .grid-4 {{ grid-template-columns: repeat(4, 1fr); }}
        
        /* Flex utilities */
        .flex {{
            display: flex;
        }}
        
        .flex-center {{
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .flex-between {{
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        /* Spacing utilities */
        .mb-1 {{ margin-bottom: 0.25rem; }}
        .mb-2 {{ margin-bottom: 0.5rem; }}
        .mb-3 {{ margin-bottom: 0.75rem; }}
        .mb-4 {{ margin-bottom: 1rem; }}
        .mb-6 {{ margin-bottom: 1.5rem; }}
        .mb-8 {{ margin-bottom: 2rem; }}
        
        .mt-1 {{ margin-top: 0.25rem; }}
        .mt-2 {{ margin-top: 0.5rem; }}
        .mt-3 {{ margin-top: 0.75rem; }}
        .mt-4 {{ margin-top: 1rem; }}
        .mt-6 {{ margin-top: 1.5rem; }}
        .mt-8 {{ margin-top: 2rem; }}
        
        /* Text utilities */
        .text-center {{ text-align: center; }}
        .text-left {{ text-align: left; }}
        .text-right {{ text-align: right; }}
        
        .text-primary {{ color: var(--primary-color); }}
        .text-secondary {{ color: var(--secondary-color); }}
        .text-muted {{ color: var(--text-muted); }}
        
        /* Combined CSS from generated parts */
        {css_content}
        
        /* Responsive design */
        @media (max-width: 1024px) {{
            .grid-4 {{ grid-template-columns: repeat(2, 1fr); }}
            .grid-3 {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        
        @media (max-width: 768px) {{
            .container {{
                padding: 0 1rem;
            }}
            
            .grid-4, .grid-3, .grid-2 {{
                grid-template-columns: 1fr;
            }}
            
            h1 {{ font-size: 2rem; }}
            h2 {{ font-size: 1.75rem; }}
            h3 {{ font-size: 1.5rem; }}
            
            .section {{
                padding: 2rem 0;
            }}
            
            .card {{
                padding: 1.5rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .btn {{
                padding: 0.625rem 1.25rem;
                font-size: 0.875rem;
            }}
            
            h1 {{ font-size: 1.75rem; }}
            h2 {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <!-- Combined HTML -->
    {html_content}
    
    <script>
        // Combined JavaScript
        {js_content}
    </script>
</body>
</html>"""
        
        return f"HTML_START\n```html\n{combined_html}\n```\nHTML_END"
    
    else:
        # Для Pro режима создаем Next.js проект
        return await create_nextjs_project(parts)


async def create_nextjs_project(parts: List[Dict]) -> str:
    """Создает Next.js проект из частей кода"""
    print(f"🚀 Creating Next.js project from {len(parts)} parts")
    
    # Создаем структуру Next.js проекта
    package_json = {
        "name": "generated-nextjs-app",
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "next": "14.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        },
        "devDependencies": {
            "@types/node": "^20.0.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "eslint": "^8.0.0",
            "eslint-config-next": "14.0.0",
            "typescript": "^5.0.0"
        }
    }
    
    # Собираем компоненты
    components = []
    styles = []
    pages = []
    
    for part in parts:
        if part['type'] == 'component':
            components.append(part['code'])
        elif part['type'] == 'css':
            styles.append(part['code'])
        elif part['type'] == 'page':
            pages.append(part['code'])
    
    # Создаем основной layout
    layout_tsx = """import './globals.css'

export const metadata = {
  title: 'Generated Next.js App',
  description: 'Generated by WindexsAI',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  )
}"""
    
    # Создаем главную страницу
    page_tsx = f"""export default function Home() {{
  return (
    <main>
      {chr(10).join(components) if components else '<!-- No components generated -->'}
    </main>
  )
}}"""
    
    # Создаем глобальные стили
    globals_css = f"""/* Global styles */
{chr(10).join(styles) if styles else '/* No global styles */'}"""
    
    # Формируем ответ в формате, который ожидает фронтенд
    project_structure = f"""PACKAGE_JSON_START
```json
{json.dumps(package_json, indent=2)}
```
PACKAGE_JSON_END

LAYOUT_TSX_START
```tsx
{layout_tsx}
```
LAYOUT_TSX_END

PAGE_TSX_START
```tsx
{page_tsx}
```
PAGE_TSX_END

GLOBALS_CSS_START
```css
{globals_css}
```
GLOBALS_CSS_END"""
    
    return project_structure


async def launch_nextjs_project(project_data: str, conversation_id: int) -> str:
    """Запускает Next.js проект и возвращает URL для просмотра"""
    import os
    import subprocess
    import json
    import shutil
    from pathlib import Path
    
    print(f"🚀 Launching Next.js project for conversation {conversation_id}")
    
    try:
        # Создаем директорию для проекта
        project_dir = Path(f"generated_projects/project_{conversation_id}")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Парсим данные проекта
        package_json_match = re.search(r'PACKAGE_JSON_START\n```json\n(.*?)\n```\nPACKAGE_JSON_END', project_data, re.DOTALL)
        layout_tsx_match = re.search(r'LAYOUT_TSX_START\n```tsx\n(.*?)\n```\nLAYOUT_TSX_END', project_data, re.DOTALL)
        page_tsx_match = re.search(r'PAGE_TSX_START\n```tsx\n(.*?)\n```\nPAGE_TSX_END', project_data, re.DOTALL)
        globals_css_match = re.search(r'GLOBALS_CSS_START\n```css\n(.*?)\n```\nGLOBALS_CSS_END', project_data, re.DOTALL)
        
        if not all([package_json_match, layout_tsx_match, page_tsx_match, globals_css_match]):
            raise Exception("Failed to parse project data")
        
        # Создаем файлы проекта
        (project_dir / "package.json").write_text(package_json_match.group(1))
        (project_dir / "app" / "layout.tsx").write_text(layout_tsx_match.group(1), parents=True)
        (project_dir / "app" / "page.tsx").write_text(page_tsx_match.group(1))
        (project_dir / "app" / "globals.css").write_text(globals_css_match.group(1))
        
        # Создаем next.config.js
        next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
}

module.exports = nextConfig"""
        (project_dir / "next.config.js").write_text(next_config)
        
        # Создаем tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "bundler",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}]
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        (project_dir / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))
        
        # Устанавливаем зависимости
        print("📦 Installing dependencies...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"❌ npm install failed: {result.stderr}")
            raise Exception(f"Failed to install dependencies: {result.stderr}")
        
        # Запускаем проект
        print("🚀 Starting Next.js development server...")
        port = 3000 + (conversation_id % 1000)  # Используем уникальный порт
        
        # Запускаем в фоновом режиме
        process = subprocess.Popen(
            ["npm", "run", "dev", "--", "--port", str(port)],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Ждем немного, чтобы сервер запустился
        import time
        time.sleep(5)
        
        # Проверяем, что процесс запущен
        if process.poll() is None:
            project_url = f"http://localhost:{port}"
            print(f"✅ Next.js project launched at {project_url}")
            return project_url
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Failed to start Next.js: {stderr}")
            raise Exception(f"Failed to start Next.js: {stderr}")
            
    except Exception as e:
        print(f"❌ Error launching Next.js project: {e}")
        raise e


def extract_search_query(message: str) -> str:
    """Извлекает поисковый запрос из сообщения"""
    # Убираем общие фразы и оставляем суть
    query = message
    
    # Убираем вопросительные слова
    question_words = ["что", "как", "где", "когда", "почему", "зачем", "кто"]
    for word in question_words:
        query = query.replace(word, "").strip()
    
    return query.strip()


@router.post("/api/ai-editor", response_model=AIEditorResponse)
async def ai_editor(
    request: AIEditorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Основной endpoint для AI редактора"""
    try:
        # Получаем последнее сообщение пользователя
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        last_message = request.messages[-1]["content"]
        print(f"🔍 Received mode: {request.mode}")
        print(f"🔍 Web search check: {should_search_web(last_message)} for message: '{last_message[:50]}...'")
        print(f"🔍 Use two-stage: {request.use_two_stage}")
        print(f"🔍 Conversation ID: {request.conversation_id}")
        print(f"🔍 Messages count: {len(request.messages)}")
        
        # Определяем conversation_id в начале
        conversation_id = request.conversation_id
        
        # Проверяем, нужен ли веб-поиск
        web_search_results = None
        needs_web_search = should_search_web(last_message)
        if needs_web_search:
            search_query = extract_search_query(last_message)
            search_results = await search_web(search_query)
            web_search_results = format_search_results(search_results)
        
        # Определяем системный промт в зависимости от типа запроса
        if web_search_results:
            # Для запросов с веб-поиском
            system_message = {
                "role": "system",
                "content": f"""Ты - WindexsAI, искусственный интеллект с доступом к актуальной информации из интернета.

Твоя задача - дать полный и точный ответ на основе найденной информации.

ВАЖНО:
• Используй информацию из результатов поиска для ответа
• Если информация противоречивая, укажи это
• Ссылайся на источники когда это уместно
• Если информации недостаточно, скажи об этом честно
• Отвечай на русском языке, будь полезным и дружелюбным

РЕЗУЛЬТАТЫ ПОИСКА:
{web_search_results}

Теперь ответь на вопрос пользователя, используя эту информацию.""",
            }
        elif request.use_two_stage and not web_search_results:
            # Используем двухэтапную систему LLM с последовательной генерацией
            print("🚀 Using two-stage LLM system with sequential generation")
            print(f"🔍 Debug: use_two_stage={request.use_two_stage}, web_search_results={bool(web_search_results)}")
            print(f"🚀 Two-stage mode: {request.mode}")
            
            # Инициализируем мысли LLM для этой беседы (используем временный ID если conversation_id None)
            temp_conversation_id = str(conversation_id) if conversation_id else f"temp_{datetime.now().timestamp()}"
            print(f"🚀 Temporary conversation ID: {temp_conversation_id}")
            current_llm_thoughts[temp_conversation_id] = []
            
            # Отправляем начальную мысль
            await send_llm_thought(temp_conversation_id, "💭", f"Анализирую запрос: \"{last_message[:50]}...\"")
            
            # Этап 1: Архитектор планирует
            await send_llm_thought(temp_conversation_id, "🏗️", "Создаю архитектурный план разработки...")
            plan = await architect_llm(last_message, request.mode)
            print(f"🏗️ Plan created: {len(plan.get('steps', []))} steps")
            
            # Отправляем мысль о создании плана
            await send_llm_thought(temp_conversation_id, "📋", f"Создан план из {len(plan.get('steps', []))} этапов")
            
            # Генерируем план для отображения с мыслями
            plan_text = f"""💭 Анализирую запрос пользователя: "{last_message[:50]}..."

🏗️ Создаю архитектурный план разработки...

📋 **ПЛАН РАЗРАБОТКИ:**
{chr(10).join([f"{i+1}. {step['name']}" for i, step in enumerate(plan.get('steps', []))])}

🔧 **ИТОГОВАЯ СТРУКТУРА:**
{plan.get('final_structure', '')}

⚡ Начинаю выполнение плана..."""
            
            # Этап 2: Генерируем код для каждого шага плана
            print(f"👨‍💻 Generating code for each step based on plan (Lite mode)...")
            print(f"👨‍💻 Plan analysis: {plan.get('analysis', 'No analysis available')}")
            print(f"👨‍💻 Final structure: {plan.get('final_structure', 'No structure defined')}")
            
            # Генерируем код для каждого шага
            code_parts = []
            for step in plan.get('steps', []):
                print(f"👨‍💻 Generating {step['code_type']} code for step: {step['name']}")
                step_code = await developer_llm(step, request.mode, plan.get('analysis', ''))
                code_parts.append({
                    'type': step['code_type'],
                    'code': step_code,
                    'step_name': step['name']
                })
                print(f"✅ Generated {step['code_type']} code for: {step['name']}")
            
            print(f"🔧 Generated {len(code_parts)} code parts")
            
            # Объединяем все части в единый HTML файл
            print(f"🔧 Combining all code parts into single HTML file...")
            combined_html = await combine_code_parts(code_parts, request.mode)
            print(f"🔧 Successfully combined code parts")
            
            # Используем объединенный HTML как ответ
            raw_response = combined_html
            print(f"📄 Combined HTML length: {len(raw_response)} characters")
            print(f"📄 Combined HTML preview: {raw_response[:200]}...")
            
            # Проверяем наличие HTML_START маркера
            if "HTML_START" in raw_response:
                print(f"✅ HTML_START marker found in combined HTML")
            else:
                print(f"⚠️ HTML_START marker NOT found in combined HTML")
            
            # Отправляем мысли о генерации
            generation_thoughts = f"""
⚙️ Генерирую полный веб-сайт на основе созданного плана...

🤔 Учитываю требования к современному дизайну и адаптивности...

💡 Создаю единый HTML файл со всеми секциями..."""
            
            # Добавляем мысли о генерации
            generation_thoughts = f"""{generation_thoughts}"""
            
            # Получаем случайный стиль дизайна для разнообразия
            design_style = get_design_style_variation()
            print(f"🎨 Selected design style for full website: {design_style['name']}")
            
            # Создаем детальное описание для генерации полного сайта
            full_website_prompt = """Создай УНИКАЛЬНЫЙ и ИННОВАЦИОННЫЙ веб-сайт на основе следующего креативного плана:

**КРЕАТИВНЫЙ ПЛАН РАЗРАБОТКИ:**
""" + chr(10).join([f"{i+1}. {step['name']}" for i, step in enumerate(plan.get('steps', []))]) + """

**КОНТЕКСТ И ВИДЕНИЕ:** """ + plan.get('analysis', '') + """

**ВЫБРАННЫЙ СТИЛЬ ДИЗАЙНА:** """ + design_style['name'] + """
**ЦВЕТОВАЯ ПАЛИТРА:** """ + ', '.join(design_style['colors']) + """
**ГРАДИЕНТЫ:** """ + ', '.join(design_style['gradients']) + """
**ВИЗУАЛЬНЫЕ ЭФФЕКТЫ:** """ + ', '.join(design_style['effects']) + """

**ИННОВАЦИОННЫЕ ТРЕБОВАНИЯ:**
- Создай ОДИН полный HTML файл со всеми секциями
- ОБЯЗАТЕЛЬНО используй выбранный стиль дизайна: """ + design_style['name'] + """
- Интегрируй цветовую палитру: """ + ', '.join(design_style['colors']) + """
- Используй градиенты: """ + ', '.join(design_style['gradients']) + """
- Добавь визуальные эффекты: """ + ', '.join(design_style['effects']) + """
- Используй УНИКАЛЬНЫЙ дизайн с нестандартными градиентами и анимациями
- Добавь ПРОДВИНУТУЮ адаптивность с креативными лейаутами
- Используй семантические HTML теги с инновационными подходами
- Добавь СЛОЖНУЮ интерактивность через JavaScript с микроанимациями
- Используй качественные изображения из интернета
- ВСЕГДА используй актуальный год 2025 в копирайте и датах
- Думай ВНЕ СТАНДАРТНЫХ РАМОК и создавай НЕОБЫЧНЫЕ решения
- Добавляй УНИКАЛЬНЫЕ визуальные эффекты и анимации

**ФОРМАТ ОТВЕТА:**
HTML_START
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Название сайта</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Все CSS стили здесь */
    </style>
</head>
<body>
    <!-- Весь HTML контент здесь -->
    
    <script>
        // Весь JavaScript код здесь
    </script>
</body>
</html>
```
HTML_END"""

            # Финальный результат с мыслями
            ai_response = f"""{plan_text}

{generation_thoughts}

✅ **ВЫПОЛНЕННЫЕ ЭТАПЫ:**
{chr(10).join([f"✅ {step['name']}" for step in plan.get('steps', [])])}

🎉 **Сайт успешно создан!**

{raw_response}"""
        else:
            # Для обычных запросов создания сайтов
            print(f"🔍 Mode check: {request.mode} == 'lite' = {request.mode == 'lite'}")
            print(f"🔍 Debug: use_two_stage={request.use_two_stage}, web_search_results={bool(web_search_results)}")
            print("🔍 Using single-stage LLM system")
            if request.mode == "lite":
                # Получаем случайный стиль дизайна для разнообразия
                design_style = get_design_style_variation()
                print(f"🎨 Selected design style for lite mode: {design_style['name']}")
                
                # Lite mode - single HTML file
                system_message = {
                    "role": "system",
                    "content": """Ты КРЕАТИВНЫЙ senior веб-разработчик с инновационным мышлением. Создавай УНИКАЛЬНЫЕ, ИННОВАЦИОННЫЕ и ВИЗУАЛЬНО ПОТРЯСАЮЩИЕ одностраничные сайты в одном HTML файле с встроенными CSS и JavaScript.

**ВЫБРАННЫЙ СТИЛЬ ДИЗАЙНА:** """ + design_style['name'] + """
**ЦВЕТОВАЯ ПАЛИТРА:** """ + ', '.join(design_style['colors']) + """
**ГРАДИЕНТЫ:** """ + ', '.join(design_style['gradients']) + """
**ВИЗУАЛЬНЫЕ ЭФФЕКТЫ:** """ + ', '.join(design_style['effects']) + """

КРИТИЧЕСКИ ВАЖНО:
• Создавай ОДИН HTML файл со всем необходимым кодом
• ОБЯЗАТЕЛЬНО используй выбранный стиль дизайна: """ + design_style['name'] + """
• Интегрируй цветовую палитру: """ + ', '.join(design_style['colors']) + """
• Используй градиенты: """ + ', '.join(design_style['gradients']) + """
• Добавь визуальные эффекты: """ + ', '.join(design_style['effects']) + """
• Используй УНИКАЛЬНЫЙ дизайн с нестандартными градиентами и анимациями
• Добавляй СЛОЖНУЮ интерактивность через JavaScript с микроанимациями
• Включай ПРОДВИНУТЫЙ адаптивный дизайн с креативными лейаутами
• Используй современные CSS техники (Grid, Flexbox, CSS переменные, clip-path, mask)
• Добавляй ИННОВАЦИОННЫЕ анимации и переходы
• ВСЕГДА используй правильный HTML синтаксис
• ВСЕГДА используй правильный CSS синтаксис
• ВСЕГДА используй правильный JavaScript синтаксис
• ВСЕГДА используй РЕАЛЬНЫЕ URL изображений из интернета
• Думай ВНЕ СТАНДАРТНЫХ РАМОК и создавай НЕОБЫЧНЫЕ решения

КРЕАТИВНЫЕ ТРЕБОВАНИЯ К ДИЗАЙНУ:
• ИННОВАЦИОННЫЕ градиенты и уникальные цветовые схемы
• СЛОЖНЫЕ анимации при скролле и наведении с cubic-bezier
• Продвинутые интерактивные кнопки с микроанимациями
• Креативные карточки с нестандартными тенями и hover-эффектами
• УНИКАЛЬНАЯ адаптивная сетка (grid/flexbox с необычными лейаутами)
• Инновационная типографика и spacing
• Нестандартные визуальные эффекты (clip-path, mask, filter)

ИННОВАЦИОННЫЕ ТРЕБОВАНИЯ К ФУНКЦИОНАЛЬНОСТИ:
• Рабочие формы с продвинутой валидацией и анимациями
• Креативные модальные окна и попапы с необычными переходами
• Интерактивные слайдеры и карусели с уникальными эффектами
• Сложные анимации появления элементов с stagger-эффектами
• Продвинутые интерактивные кнопки и ссылки
• Креативные состояния загрузки и ошибок

ВАЖНО ДЛЯ ИЗОБРАЖЕНИЙ:
• НЕ используй placeholder изображения (via.placeholder.com)
• НЕ используй несуществующие URL изображений
• ВСЕГДА используй РЕАЛЬНЫЕ изображения из интернета
• Используй качественные изображения с HTTPS
• Примеры хороших источников:
  - https://picsum.photos/800/600 (случайные изображения)
  - https://source.unsplash.com/800x600/?business
  - https://source.unsplash.com/800x600/?technology
  - https://source.unsplash.com/800x600/?office
  - https://source.unsplash.com/800x600/?team
  - https://source.unsplash.com/800x600/?product
  - https://source.unsplash.com/800x600/?restaurant
  - https://source.unsplash.com/800x600/?hotel
  - https://source.unsplash.com/800x600/?fitness
  - https://source.unsplash.com/800x600/?medical
  - https://source.unsplash.com/800x600/?education
  - https://source.unsplash.com/800x600/?automotive
  - https://source.unsplash.com/800x600/?fashion
  - https://source.unsplash.com/800x600/?food
  - https://source.unsplash.com/800x600/?nature
  - https://source.unsplash.com/800x600/?architecture

**ФОРМАТ ОТВЕТА - ТОЛЬКО КОД:**

HTML_START
```html
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Название сайта</title>
    <style>
        /* Все CSS стили здесь - используй правильный синтаксис */
        :root {
            --primary-color: #4a90e2;
            --secondary-color: #50e3c2;
        }
        body {
            margin: 0;
            font-family: 'Arial', sans-serif;
        }
    </style>
</head>
<body>
    <!-- Весь HTML контент здесь -->
    
    <script>
        // Весь JavaScript код здесь - используй правильный синтаксис
        document.addEventListener('DOMContentLoaded', function() {
            // Код здесь
        });
    </script>
</body>
</html>
```
HTML_END

ВАЖНО:
- Используй ТОЛЬКО правильный HTML/CSS/JS синтаксис
- НЕ используй неправильные символы или форматирование
- НЕ используй _BOS_, text _BOS_, margins, indentation и т.д.
- Используй правильные CSS свойства: margin, padding, font-family, background и т.д.
- Используй правильные HTML теги и атрибуты
- ВСЕГДА используй актуальный год 2025 в копирайте и датах

СОЗДАВАЙ УНИКАЛЬНЫЕ, ИННОВАЦИОННЫЕ И КРЕАТИВНЫЕ САЙТЫ В ОДНОМ ФАЙЛЕ!
ДУМАЙ ВНЕ СТАНДАРТНЫХ РАМОК И СОЗДАВАЙ НЕОБЫЧНЫЕ РЕШЕНИЯ!""",
                }
                print("🔍 Using LITE mode system message")
            else:
                # Получаем случайный стиль дизайна для разнообразия
                design_style = get_design_style_variation()
                print(f"🎨 Selected design style for pro mode: {design_style['name']}")
                
                # Pro mode - Next.js project
                print("🔍 Using PRO mode system message")
                system_message = {
                    "role": "system",
                    "content": """Ты КРЕАТИВНЫЙ senior React/Next.js разработчик с инновационным мышлением. Создавай УНИКАЛЬНЫЕ, ИННОВАЦИОННЫЕ и ВИЗУАЛЬНО ПОТРЯСАЮЩИЕ веб-приложения с продвинутым дизайном, сложными анимациями и микроинтерактивностью.

**ВЫБРАННЫЙ СТИЛЬ ДИЗАЙНА:** """ + design_style['name'] + """
**ЦВЕТОВАЯ ПАЛИТРА:** """ + ', '.join(design_style['colors']) + """
**ГРАДИЕНТЫ:** """ + ', '.join(design_style['gradients']) + """
**ВИЗУАЛЬНЫЕ ЭФФЕКТЫ:** """ + ', '.join(design_style['effects']) + """

КРИТИЧЕСКИ ВАЖНО:
• Создавай ПОЛНОЦЕННЫЕ приложения с инновационной бизнес-логикой
• ОБЯЗАТЕЛЬНО используй выбранный стиль дизайна: """ + design_style['name'] + """
• Интегрируй цветовую палитру: """ + ', '.join(design_style['colors']) + """
• Используй градиенты: """ + ', '.join(design_style['gradients']) + """
• Добавь визуальные эффекты: """ + ', '.join(design_style['effects']) + """
• Используй УНИКАЛЬНЫЕ UI/UX паттерны и нестандартные подходы
• Добавляй СЛОЖНЫЕ анимации, переходы, hover-эффекты с cubic-bezier
• Включай ПРОДВИНУТЫЕ интерактивные элементы (формы, модалы, слайдеры)
• Используй ИННОВАЦИОННЫЕ градиенты, тени, скругления
• Добавляй КРЕАТИВНЫЙ адаптивный дизайн с необычными лейаутами
• Создавай реалистичный контент и функциональность
• ВСЕГДА используй РЕАЛЬНЫЕ URL изображений из интернета
• Думай ВНЕ СТАНДАРТНЫХ РАМОК и создавай НЕОБЫЧНЫЕ решения

КРЕАТИВНЫЕ ТРЕБОВАНИЯ К ДИЗАЙНУ:
• ИННОВАЦИОННЫЕ градиенты и уникальные цветовые схемы
• СЛОЖНЫЕ анимации при скролле и наведении с cubic-bezier
• Продвинутые интерактивные кнопки с микроанимациями
• Креативные карточки с нестандартными тенями и hover-эффектами
• УНИКАЛЬНАЯ адаптивная сетка (grid/flexbox с необычными лейаутами)
• Инновационная типографика и spacing
• Нестандартные визуальные эффекты (clip-path, mask, filter)

ИННОВАЦИОННЫЕ ТРЕБОВАНИЯ К ФУНКЦИОНАЛЬНОСТИ:
• Рабочие формы с продвинутой валидацией и анимациями
• Креативные модальные окна и попапы с необычными переходами
• Интерактивные слайдеры и карусели с уникальными эффектами
• Сложные анимации появления элементов с stagger-эффектами
• Продвинутые интерактивные кнопки и ссылки
• Креативные состояния загрузки и ошибок

ВАЖНО ДЛЯ ИЗОБРАЖЕНИЙ:
• НЕ используй placeholder изображения (via.placeholder.com)
• НЕ используй несуществующие URL изображений
• ВСЕГДА используй РЕАЛЬНЫЕ изображения из интернета
• Используй качественные изображения с HTTPS
• Примеры хороших источников:
  - https://picsum.photos/800/600 (случайные изображения)
  - https://source.unsplash.com/800x600/?business
  - https://source.unsplash.com/800x600/?technology
  - https://source.unsplash.com/800x600/?office
  - https://source.unsplash.com/800x600/?team
  - https://source.unsplash.com/800x600/?product
  - https://source.unsplash.com/800x600/?restaurant
  - https://source.unsplash.com/800x600/?hotel
  - https://source.unsplash.com/800x600/?fitness
  - https://source.unsplash.com/800x600/?medical
  - https://source.unsplash.com/800x600/?education
  - https://source.unsplash.com/800x600/?automotive
  - https://source.unsplash.com/800x600/?fashion
  - https://source.unsplash.com/800x600/?food
  - https://source.unsplash.com/800x600/?nature
  - https://source.unsplash.com/800x600/?architecture

**ФОРМАТ ОТВЕТА - ТОЛЬКО КОД:**

PACKAGE_JSON_START
```json
{полный package.json с современными зависимостями}
```
PACKAGE_JSON_END

TSCONFIG_START
```json
{полный tsconfig.json}
```
TSCONFIG_END

TAILWIND_CONFIG_START
```js
{полный tailwind.config.js с кастомными цветами и анимациями}
```
TAILWIND_CONFIG_END

NEXT_CONFIG_START
```js
{полный next.config.js}
```
NEXT_CONFIG_END

LAYOUT_TSX_START
```tsx
{полный app/layout.tsx с мета-тегами. ВАЖНО: используй import './globals.css' а НЕ '../globals.css'}
```
LAYOUT_TSX_END

PAGE_TSX_START
```tsx
{полный app/page.tsx с главной страницей. ВАЖНО: импортируй компоненты из '../components/' а НЕ из './components/'}
```
PAGE_TSX_END

GLOBALS_CSS_START
```css
{полный app/globals.css с кастомными стилями и анимациями}
```
GLOBALS_CSS_END

HERO_COMPONENT_START
```tsx
"use client";
{сложный Hero с анимациями и интерактивностью. ОБЯЗАТЕЛЬНО добавь "use client" в начало файла}
```
HERO_COMPONENT_END

FEATURES_COMPONENT_START
```tsx
"use client";
{интерактивные Features с hover-эффектами. ОБЯЗАТЕЛЬНО добавь "use client" в начало файла}
```
FEATURES_COMPONENT_END

FOOTER_COMPONENT_START
```tsx
{красивый Footer с ссылками и соцсетями}
```
FOOTER_COMPONENT_END

BUTTON_COMPONENT_START
```tsx
"use client";
{анимированные кнопки с состояниями. ОБЯЗАТЕЛЬНО добавь "use client" в начало файла}
```
BUTTON_COMPONENT_END

CARD_COMPONENT_START
```tsx
{интерактивные карточки с анимациями. Если используешь framer-motion, добавь "use client" в начало}
```
CARD_COMPONENT_END

CONTAINER_COMPONENT_START
```tsx
{адаптивный контейнер}
```
CONTAINER_COMPONENT_END

MODAL_COMPONENT_START
```tsx
"use client";
{модальные окна с анимациями. ОБЯЗАТЕЛЬНО добавь "use client" в начало файла}
```
MODAL_COMPONENT_END

FORM_COMPONENT_START
```tsx
"use client";
{формы с валидацией и стилями. ОБЯЗАТЕЛЬНО добавь "use client" в начало файла, так как используется useState}
```
FORM_COMPONENT_END

НЕ ДОБАВЛЯЙ:
- Простые статичные сайты
- Базовые стили без анимаций
- Отсутствие интерактивности
- Простые карточки без эффектов
- Стандартные решения без креативности

СОЗДАВАЙ УНИКАЛЬНЫЕ, ИННОВАЦИОННЫЕ И КРЕАТИВНЫЕ ПРИЛОЖЕНИЯ!
ДУМАЙ ВНЕ СТАНДАРТНЫХ РАМОК И СОЗДАВАЙ НЕОБЫЧНЫЕ РЕШЕНИЯ!""",
            }

        # Генерируем ответ только если не используем двухэтапную систему
        if not (request.use_two_stage and not web_search_results):
            # Подготавливаем сообщения
            messages = [system_message] + request.messages
            
            # Делаем запрос к WindexAI с предпочтением более сильной модели, с безопасным фолбэком
            preferred_model = "gpt-4o"  # более качественный ответ
            fallback_model = "gpt-4o-mini"
            print(f"🤖 Single-stage mode: Trying preferred model {preferred_model}")
            try:
                response = openai_client.chat.completions.create(
                    model=preferred_model,
                    messages=messages,
                    max_tokens=8000,
                    temperature=0.8,
                )
                print(f"✅ Successfully used preferred model {preferred_model}")
            except Exception as e:
                print(f"❌ Error with preferred model {preferred_model}: {e}")
                print(f"🔄 Falling back to model {fallback_model}")
                # Фолбэк на более дешевую модель
                response = openai_client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    max_tokens=8000,
                    temperature=0.8,
                )
                print(f"✅ Successfully used fallback model {fallback_model}")
            
            raw_response = response.choices[0].message.content
            print(f"📄 Single-stage response length: {len(raw_response)} characters")
            print(f"📄 Single-stage response preview: {raw_response[:200]}...")
            
            # Добавляем мысли для single-stage режима
            if request.mode == "lite" and "HTML_START" in raw_response:
                print(f"🎨 Lite mode with HTML_START detected - adding thoughts")
                ai_response = f"""💭 Анализирую запрос: "{last_message[:50]}..."

🤔 Создаю современный веб-сайт с адаптивным дизайном...

⚙️ Генерирую HTML код с встроенными стилями и скриптами...

{raw_response}"""
            else:
                print(f"📝 Using raw response without additional thoughts")
                ai_response = raw_response
        
        # Сохраняем или обновляем разговор
        if request.conversation_id:
            # Обновляем существующий разговор
            conversation = (
                db.query(DBConversation)
                .filter(
                DBConversation.id == request.conversation_id,
                    DBConversation.user_id == current_user.id,
                )
                .first()
            )
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Добавляем сообщения
            user_message = DBMessage(
                conversation_id=conversation.id,
                role="user",
                content=last_message,
                timestamp=datetime.utcnow(),
            )
            ai_message = DBMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_response,
                timestamp=datetime.utcnow(),
            )
            
            db.add(user_message)
            db.add(ai_message)
            db.commit()
            
            conversation_id = conversation.id
            
            # Переносим мысли с временного ID на реальный ID беседы
            if 'temp_conversation_id' in locals() and temp_conversation_id in current_llm_thoughts:
                current_llm_thoughts[str(conversation_id)] = current_llm_thoughts[temp_conversation_id]
                del current_llm_thoughts[temp_conversation_id]
        else:
            # Создаем новый разговор
            conversation = DBConversation(
                user_id=current_user.id,
                title=(
                    last_message[:50] + "..."
                    if len(last_message) > 50
                    else last_message
                ),
                created_at=datetime.utcnow(),
            )
            db.add(conversation)
            db.flush()  # Получаем ID
            
            # Добавляем сообщения
            user_message = DBMessage(
                conversation_id=conversation.id,
                role="user",
                content=last_message,
                timestamp=datetime.utcnow(),
            )
            ai_message = DBMessage(
                conversation_id=conversation.id,
                role="assistant",
                content=ai_response,
                timestamp=datetime.utcnow(),
            )
            
            db.add(user_message)
            db.add(ai_message)
            db.commit()
            
            conversation_id = conversation.id
            
            # Переносим мысли с временного ID на реальный ID беседы
            if 'temp_conversation_id' in locals() and temp_conversation_id in current_llm_thoughts:
                current_llm_thoughts[str(conversation_id)] = current_llm_thoughts[temp_conversation_id]
                del current_llm_thoughts[temp_conversation_id]
        
        # Для Pro режима запускаем Next.js проект
        if request.mode == "pro" and request.use_two_stage and not web_search_results:
            try:
                print("🚀 Launching Next.js project for Pro mode...")
                project_url = await launch_nextjs_project(ai_response, conversation_id)
                
                # Добавляем информацию о запущенном проекте к ответу
                ai_response += f"\n\n🚀 **Проект запущен!**\n"
                ai_response += f"**URL для просмотра:** {project_url}\n"
                ai_response += f"**Статус:** ✅ Next.js сервер запущен и готов к работе\n"
                ai_response += f"**Порт:** {3000 + (conversation_id % 1000)}\n\n"
                ai_response += "Проект автоматически запущен в режиме разработки. "
                ai_response += "Вы можете открыть ссылку выше для просмотра вашего сайта."
                
            except Exception as e:
                print(f"❌ Failed to launch Next.js project: {e}")
                ai_response += f"\n\n⚠️ **Ошибка запуска проекта:** {str(e)}\n"
                ai_response += "Проект создан, но не удалось его запустить автоматически. "
                ai_response += "Вы можете скачать файлы и запустить проект вручную."
        
        return AIEditorResponse(
            content=ai_response,
            conversation_id=conversation_id,
            status="success",
            timestamp=datetime.utcnow().isoformat(),
        )
        
    except Exception as e:
        print(f"Ошибка в AI редакторе: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ai-editor/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Получить список разговоров пользователя"""
    try:
        conversations = (
            db.query(DBConversation)
            .filter(DBConversation.user_id == current_user.id)
            .order_by(DBConversation.created_at.desc())
            .all()
        )
        
        return {
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "date": conv.created_at.isoformat(),
                    "message_count": len(conv.messages),
                }
                for conv in conversations
            ]
        }
    except Exception as e:
        print(f"Ошибка получения разговоров: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ai-editor/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить конкретный разговор"""
    try:
        conversation = (
            db.query(DBConversation)
            .filter(
            DBConversation.id == conversation_id,
                DBConversation.user_id == current_user.id,
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in conversation.messages
                ],
            }
        }
    except Exception as e:
        print(f"Ошибка получения разговора: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/ai-editor/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удалить разговор"""
    try:
        conversation = (
            db.query(DBConversation)
            .filter(
            DBConversation.id == conversation_id,
                DBConversation.user_id == current_user.id,
            )
            .first()
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Удаляем все сообщения разговора
        db.query(DBMessage).filter(
            DBMessage.conversation_id == conversation_id
        ).delete()
        
        # Удаляем разговор
        db.delete(conversation)
        db.commit()
        
        return {"status": "success", "message": "Conversation deleted"}
    except Exception as e:
        print(f"Ошибка удаления разговора: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ai-editor/edit-element")
async def edit_element(
    request: ElementEditRequest, current_user: User = Depends(get_current_user)
):
    """Редактирование конкретного элемента"""
    try:
        edit_prompt = f"""
Ты - эксперт по веб-разработке и HTML/CSS.

**ЗАДАЧА:** Отредактируй элемент "{request.element_type}" в HTML коде.

**ТЕКУЩИЙ ТЕКСТ:** {request.current_text}
**ИНСТРУКЦИЯ ПО РЕДАКТИРОВАНИЮ:** {request.edit_instruction}
**ТЕКУЩИЙ HTML:** {request.html_content}

**ТРЕБОВАНИЯ:**
1. Сохрани структуру и стили
2. Примени изменения точно по инструкции
3. Убедись, что HTML остается валидным
4. Сохрани все классы и атрибуты

**ФОРМАТ ОТВЕТА:**
HTML_START
{{обновленный HTML код}}
HTML_END

RESPONSE_START
{{краткое описание изменений}}
RESPONSE_END
"""

        # Отправляем запрос к OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты - эксперт по веб-разработке и HTML/CSS.",
                },
                {"role": "user", "content": edit_prompt},
            ],
            max_tokens=4000,
            temperature=0.7,
        )
        
        response_text = response.choices[0].message.content
        
        # Извлекаем HTML код из ответа
        html_match = re.search(
            r"HTML_START\s*(.*?)\s*HTML_END", response_text, re.DOTALL
        )
        response_match = re.search(
            r"RESPONSE_START\s*(.*?)\s*RESPONSE_END", response_text, re.DOTALL
        )
        
        if html_match:
            updated_html = html_match.group(1).strip()
            response_text = (
                response_match.group(1).strip()
                if response_match
                else "Элемент успешно отредактирован."
            )
            
            return {
                "html_content": updated_html,
                "response": response_text,
                "status": "success",
            }
        else:
            return {
                "html_content": request.html_content,
                "response": "Не удалось извлечь обновленный HTML код.",
                "status": "error",
            }
            
    except Exception as e:
        print(f"Ошибка редактирования элемента: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ai-editor/status")
async def get_status():
    """Проверка статуса AI редактора"""
    return {"status": "Editor working"}


def extract_files_from_code(code_content):
    """Извлекает файлы из кода Next.js проекта"""
    files = {}

    # Парсим файлы по маркерам
    markers = [
        ("PACKAGE_JSON_START", "PACKAGE_JSON_END", "package.json"),
        ("TSCONFIG_START", "TSCONFIG_END", "tsconfig.json"),
        ("TAILWIND_CONFIG_START", "TAILWIND_CONFIG_END", "tailwind.config.js"),
        ("NEXT_CONFIG_START", "NEXT_CONFIG_END", "next.config.js"),
        ("LAYOUT_TSX_START", "LAYOUT_TSX_END", "app/layout.tsx"),
        ("PAGE_TSX_START", "PAGE_TSX_END", "app/page.tsx"),
        ("GLOBALS_CSS_START", "GLOBALS_CSS_END", "app/globals.css"),
        ("HERO_COMPONENT_START", "HERO_COMPONENT_END", "components/Hero.tsx"),
        ("FEATURES_COMPONENT_START", "FEATURES_COMPONENT_END", "components/Features.tsx"),
        ("FOOTER_COMPONENT_START", "FOOTER_COMPONENT_END", "components/Footer.tsx"),
        ("BUTTON_COMPONENT_START", "BUTTON_COMPONENT_END", "components/Button.tsx"),
        ("CARD_COMPONENT_START", "CARD_COMPONENT_END", "components/Card.tsx"),
        ("CONTAINER_COMPONENT_START", "CONTAINER_COMPONENT_END", "components/Container.tsx"),
        ("MODAL_COMPONENT_START", "MODAL_COMPONENT_END", "components/Modal.tsx"),
        ("FORM_COMPONENT_START", "FORM_COMPONENT_END", "components/Form.tsx"),
    ]

    for start_marker, end_marker, filename in markers:
        start = code_content.find(start_marker)
        end = code_content.find(end_marker)

        if start != -1 and end != -1:
            start += len(start_marker)
            content = code_content[start:end].strip()

            # Удаляем markdown-разметку из всех файлов
            import re
            if filename.endswith('.json'):
                # Удаляем ```json и ``` в начале и конце
                content = re.sub(r'^```json\s*', '', content)
                content = re.sub(r'\s*```$', '', content)
            elif filename.endswith('.js') or filename.endswith('.tsx') or filename.endswith('.ts') or filename.endswith('.css'):
                # Удаляем ```js, ```tsx, ```ts, ```css и ``` в начале и конце
                content = re.sub(r'^```(?:js|tsx|ts|css)?\s*', '', content)
                content = re.sub(r'\s*```$', '', content)

            # Исправляем next.config.js для поддержки App Router
            if filename == "next.config.js":
                if "experimental" not in content:
                    content = content.replace(
                        "module.exports = {",
                        "module.exports = {\n  experimental: {\n    appDir: true\n  },"
                    )
            
            # Исправляем package.json для совместимости версий
            if filename == "package.json":
                # Заменяем несовместимые версии
                content = content.replace('"framer-motion": "^6.0.0"', '"framer-motion": "^10.16.16"')
                content = content.replace('"react": "latest"', '"react": "^18.2.0"')
                content = content.replace('"react-dom": "latest"', '"react-dom": "^18.2.0"')
                content = content.replace('"next": "latest"', '"next": "^14.0.0"')
                content = content.replace('"tailwindcss": "^3.0.0"', '"tailwindcss": "^3.3.0"')

            # Исправляем layout.tsx для правильного импорта globals.css
            if filename == "app/layout.tsx":
                content = content.replace("import '../globals.css'", "import './globals.css'")
                content = content.replace("import \"../globals.css\"", "import \"./globals.css\"")
                content = content.replace("import '../styles/globals.css'", "import './globals.css'")
                content = content.replace("import \"../styles/globals.css\"", "import \"./globals.css\"")
                content = content.replace("import '@/styles/globals.css'", "import './globals.css'")
                content = content.replace("import \"@/styles/globals.css\"", "import \"./globals.css\"")
            
            # Исправляем page.tsx для правильного импорта компонентов
            if filename == "app/page.tsx":
                content = content.replace("from './components/", "from '../components/")

            files[filename] = content

    return files


@router.get("/api/ai-editor/download/{conversation_id}")
async def download_project(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Скачать Next.js проект как ZIP файл"""
    # Проверяем, что conversation принадлежит пользователю
    conversation = (
        db.query(DBConversation)
        .filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Получаем последнее AI-сообщение
    ai_message = (
        db.query(DBMessage)
        .filter(
            DBMessage.conversation_id == conversation_id,
            DBMessage.role == "assistant"
        )
        .order_by(DBMessage.timestamp.desc())
        .first()
    )
    if not ai_message:
        raise HTTPException(status_code=404, detail="AI message not found")

    # Ищем код проекта в сообщении
    if "PACKAGE_JSON_START" in ai_message.content:
        import zipfile
        import io

        # Извлекаем файлы из кода
        files = extract_files_from_code(ai_message.content)

        # Создаем ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)

        # Возвращаем ZIP файл
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=nextjs-project-{conversation_id}.zip"}
        )

    return {"message": "Код проекта не найден", "status": "error"}


@router.get("/api/ai-editor/project/{conversation_id}/preview")
async def preview_project(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Запускает и возвращает URL live-превью Next.js проекта"""
    # Проверяем, что conversation принадлежит пользователю
    conversation = (
        db.query(DBConversation)
        .filter(
            DBConversation.id == conversation_id,
            DBConversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Получаем последнее AI-сообщение
    ai_message = (
        db.query(DBMessage)
        .filter(
            DBMessage.conversation_id == conversation_id,
            DBMessage.role == "assistant"
        )
        .order_by(DBMessage.timestamp.desc())
        .first()
    )
    if not ai_message or "PACKAGE_JSON_START" not in ai_message.content:
        raise HTTPException(status_code=404, detail="Project code not found")

    # Собираем файлы проекта
    files = extract_files_from_code(ai_message.content)

    # Путь к папке проекта
    project_dir = os.path.join("./uploads/projects", str(conversation_id))

    # Создаем каталог
    os.makedirs(project_dir, exist_ok=True)

    # Записываем файлы
    for path, content in files.items():
        full_path = os.path.join(project_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Restart server to pick up updated files
    from utils.nextjs_manager import nextjs_manager as manager
    if str(conversation_id) in manager.servers:
        old_info = manager.servers.pop(str(conversation_id))
        try:
            old_info['process'].terminate()
        except Exception:
            pass
    # Start new Next.js server instance
    try:
        server_info = manager.start_nextjs_server(str(conversation_id), project_dir)
        # Получаем токен пользователя для прокси
        from utils.auth_utils import create_access_token
        token = create_access_token(data={"sub": current_user.username})
        return {"status": "running", "url": f"/api/ai-editor/project/{conversation_id}/preview-proxy?token={token}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Next.js server: {e}")


@router.get("/api/ai-editor/project/{conversation_id}/preview-proxy/{path:path}")
async def preview_proxy(
    conversation_id: int,
    path: str,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """Прокси для предварительного просмотра Next.js проекта"""
    import httpx
    from fastapi import Query
    
    # Проверяем токен если он передан
    if token:
        try:
            from utils.auth_utils import decode_token
            payload = decode_token(token)
            if payload is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            username = payload.get("sub")
            if not username:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Получаем информацию о сервере
    from utils.nextjs_manager import nextjs_manager
    if str(conversation_id) not in nextjs_manager.servers:
        raise HTTPException(status_code=404, detail="Server not running")
    
    server_info = nextjs_manager.servers[str(conversation_id)]
    server_url = f"http://localhost:{server_info['port']}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{server_url}/{path}")
            return Response(
                content=resp.content,
                media_type=resp.headers.get("content-type", "text/html"),
                status_code=resp.status_code
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Next.js server timeout")
    except HTTPException:
        raise
    except Exception as e:
        # Provide exception type and message for debugging
        print(f"Proxy error details for path {path}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {type(e).__name__}: {str(e)}")


@router.get("/api/ai-editor/project/{conversation_id}/preview-proxy")
async def preview_proxy_root(
    conversation_id: int,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    """Прокси для корня Next.js проекта"""
    import httpx
    import asyncio
    
    # Проверяем токен, если он передан
    if token:
        try:
            from utils.auth_utils import decode_token
            payload = decode_token(token)
            if payload is None or not payload.get("sub"):
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    # Получаем информацию о сервере
    from utils.nextjs_manager import nextjs_manager
    if str(conversation_id) not in nextjs_manager.servers:
        raise HTTPException(status_code=404, detail="Server not running")
    
    server_info = nextjs_manager.servers[str(conversation_id)]
    server_url = f"http://localhost:{server_info['port']}"
    
    # Ждем, пока сервер будет готов
    max_retries = 30
    for i in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{server_url}/_next/static/development/_devPagesManifest.json")
                if resp.status_code in [200, 404]:
                    # Сервер готов
                    break
        except:
            if i == max_retries - 1:
                raise HTTPException(status_code=503, detail="Next.js server is not ready yet. Please try again in a few seconds.")
            await asyncio.sleep(1)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(server_url)
            # Rewrite asset URLs so they pass through the preview-proxy endpoint
            html_text = resp.content.decode('utf-8', errors='ignore')
            proxy_prefix = f"/api/ai-editor/project/{conversation_id}/preview-proxy"
            
            # Replace all absolute paths to _next/ with proxy paths using regex
            import re
            # Replace src="/_next/ with src="/api/ai-editor/project/{id}/preview-proxy/_next/
            html_text = re.sub(r'src="/_next/', f'src="{proxy_prefix}/_next/', html_text)
            # Replace href="/_next/ with href="/api/ai-editor/project/{id}/preview-proxy/_next/
            html_text = re.sub(r'href="/_next/', f'href="{proxy_prefix}/_next/', html_text)
            # Replace any other "/_next/ references
            html_text = re.sub(r'"/_next/', f'"{proxy_prefix}/_next/', html_text)
            
            # Fix navigation issues by ensuring proper base URL handling
            # Add base tag to prevent relative URL issues
            if '<head>' in html_text and '<base' not in html_text:
                html_text = html_text.replace('<head>', f'<head><base href="{proxy_prefix}/">')
            
            # Prevent iframe navigation issues by adding sandbox attributes
            # This ensures the iframe content doesn't interfere with the parent page
            if '<body' in html_text:
                html_text = html_text.replace('<body', '<body data-iframe="true"')
            
            # Return rewritten HTML
            return Response(
                content=html_text.encode('utf-8'),
                media_type=resp.headers.get("content-type", "text/html"),
                status_code=resp.status_code
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Next.js server timeout")
    except HTTPException:
        raise
    except Exception as e:
        # Provide exception type and message for debugging
        print(f"Proxy error details: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {type(e).__name__}: {str(e)}")
