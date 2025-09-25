import os
import json
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict

from routes.auth import get_current_user, User
from utils.openai_client import windexai_client
from utils.web_search import search_web, format_search_results

router = APIRouter()

class AIEditorRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"

def should_search_web(message: str) -> bool:
    """Определяет, нужен ли веб-поиск для сообщения"""
    search_keywords = [
        'найди', 'поиск', 'актуальн', 'новости', 'сейчас', 'сегодня', 
        'последние', 'тренд', 'курс', 'погода', 'цены', 'события',
        'что происходит', 'как дела', 'статистика', 'данные',
        'информация о', 'расскажи про', 'что нового'
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in search_keywords)

def extract_search_query(message: str) -> str:
    """Извлекает поисковый запрос из сообщения"""
    # Убираем общие фразы и оставляем суть
    query = message
    
    # Убираем фразы типа "найди информацию о", "расскажи про" и т.д.
    patterns_to_remove = [
        r'найди информацию о\s*',
        r'расскажи про\s*',
        r'что ты знаешь о\s*',
        r'найди\s*',
        r'поиск\s*',
        r'актуальн.*информацию о\s*',
        r'новости о\s*',
        r'события.*о\s*'
    ]
    
    for pattern in patterns_to_remove:
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
    
    return query.strip()

@router.post("/api/ai-editor")
async def ai_editor(request: AIEditorRequest, current_user: User = Depends(get_current_user)):
    """AI Editor endpoint for website generation with web search capability"""
    
    try:
        print(f"AI Editor request from user: {current_user.username}")
        print(f"Messages: {request.messages}")
        
        # Получаем последнее сообщение пользователя
        last_message = request.messages[-1] if request.messages else None
        user_message = last_message.get('content', '') if last_message else ''
        
        # Проверяем, нужен ли веб-поиск
        web_search_results = ""
        if last_message and last_message.get('role') == 'user' and should_search_web(user_message):
            print(f"🔍 Веб-поиск активирован для: {user_message}")
            
            # Извлекаем поисковый запрос
            search_query = extract_search_query(user_message)
            if not search_query:
                search_query = user_message
            
            # Выполняем поиск
            try:
                search_results = search_web(search_query, num_results=3)
                web_search_results = format_search_results(search_results)
                print(f"Найдено результатов поиска: {len(search_results)}")
            except Exception as e:
                print(f"Ошибка веб-поиска: {e}")
                web_search_results = "Ошибка при поиске в интернете."
        
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

Теперь ответь на вопрос пользователя, используя эту информацию."""
            }
        else:
            # Для обычных запросов создания сайтов
            system_message = {
                "role": "system",
                "content": """Ты senior UI/UX дизайнер и frontend‑разработчик. Создавай современные, премиальные, адаптивные сайты (уровня Apple/Stripe/Linear) с акцентом на визуал, типографику и микровзаимодействия.

ОБЯЗАТЕЛЬНО:
• Семантический HTML5, доступность (aria), mobile‑first.
• Современный CSS: CSS variables, clamp(), Grid + Flex, контейнерные запросы, плавные анимации/hover, glassmorphism/градиенты где уместно.
• Чистая архитектура стилей: корневые переменные цветов/типографики, модульные секции, разумные тени и расстояния (8px scale).
• Обязательные секции лендинга: hero с сильным визуалом и CTA, преимущества/фичи (cards), отзывы, CTA‑блок, футер.
• Легкий JS без внешних библиотек только при необходимости (например, переключатели тарифов/темы).

ФОРМАТ ОТВЕТА (строго):
1) Краткое описание (1–2 предложения)
2) Полный HTML между маркерами:

NEW_PAGE_START
<!DOCTYPE html>
<html lang=\"ru\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Название</title>
  <style>
    :root {
      --bg: #0b1220;
      --card: #0f172a;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --accent: #22c55e;
      --accent-2: #16a34a;
      --shadow: 0 10px 30px rgba(34,197,94,.25);
    }
    html, body { margin:0; padding:0; background:var(--bg); color:var(--text); font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, sans-serif; }
    .container { max-width: 1200px; margin: 0 auto; padding: clamp(16px, 3vw, 32px); }
    .hero { display:grid; gap:24px; align-items:center; grid-template-columns: 1.1fr 0.9fr; }
    .hero-card { background:linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02)); border:1px solid rgba(255,255,255,.06); border-radius:24px; padding: clamp(20px, 4vw, 36px); box-shadow: var(--shadow); backdrop-filter: blur(8px); }
    .title { font-size: clamp(32px, 6vw, 56px); line-height:1.05; letter-spacing:-0.02em; }
    .subtitle { color: var(--muted); font-size: clamp(16px, 2.4vw, 18px); }
    .cta { display:flex; gap:12px; margin-top: 16px; }
    .btn { background: linear-gradient(135deg, var(--accent), var(--accent-2)); color:white; border:none; padding: 12px 18px; border-radius: 12px; cursor:pointer; transition: .25s ease; box-shadow: var(--shadow); }
    .btn:hover { transform: translateY(-2px); filter: brightness(1.05); }
    .btn-outline { background: transparent; border:1px solid rgba(255,255,255,.12); color: var(--text); }
    .features { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-top: 32px; }
    .card { background: var(--card); border:1px solid rgba(255,255,255,.06); border-radius: 16px; padding: 18px; transition: .25s ease; }
    .card:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,.25); }
    .muted { color: var(--muted); }
    .testimonials { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin-top: 32px; }
    .footer { margin-top: 48px; border-top:1px solid rgba(255,255,255,.06); padding-top: 24px; color: var(--muted); font-size: 14px; }
    @media (max-width: 900px) { .hero { grid-template-columns: 1fr; } .features, .testimonials { grid-template-columns: 1fr; } }
  </style>
  <script>
    document.addEventListener('DOMContentLoaded', () => {
      const toggle = document.querySelector('[data-toggle]');
      if (toggle) toggle.addEventListener('click', () => alert('Демо‑клик!'));
    });
  </script>
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />
  <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap\" rel=\"stylesheet\" />
  <meta name=\"description\" content=\"Современный премиальный сайт с отличным UX\" />
</head>
<body>
  <main class=\"container\">
    <section class=\"hero\">
      <div class=\"hero-card\">
        <h1 class=\"title\">Название продукта</h1>
        <p class=\"subtitle\">Короткий подзаголовок с ценностным предложением, фокус на выгодах.</p>
        <div class=\"cta\">
          <button class=\"btn\" data-toggle>Попробовать бесплатно</button>
          <button class=\"btn btn-outline\">Узнать больше</button>
        </div>
      </div>
      <div class=\"hero-card\">Визуальный блок / макет / графика</div>
    </section>
    <section class=\"features\">
      <div class=\"card\"><h3>Фича 1</h3><p class=\"muted\">Короткое описание.</p></div>
      <div class=\"card\"><h3>Фича 2</h3><p class=\"muted\">Короткое описание.</p></div>
      <div class=\"card\"><h3>Фича 3</h3><p class=\"muted\">Короткое описание.</p></div>
    </section>
    <section class=\"testimonials\">
      <div class=\"card\">"Отзыв 1"</div>
      <div class=\"card\">"Отзыв 2"</div>
      <div class=\"card\">"Отзыв 3"</div>
    </section>
    <footer class=\"footer\">© 2025 WindexsAI. Все права защищены.</footer>
  </main>
  
  <script>
    // Дополнительные микровзаимодействия при наведении
    document.querySelectorAll('.card').forEach(c => {
      c.addEventListener('mousemove', (e) => {
        c.style.transform = `translateY(-3px)`;
      });
      c.addEventListener('mouseleave', () => {
        c.style.transform = '';
      });
    });
  </script>
</body>
</html>
NEW_PAGE_END"""
            }
        
        # Подготавливаем сообщения
        messages = [system_message] + request.messages
        
        # Делаем запрос к WindexAI с предпочтением более сильной модели, с безопасным фолбэком
        preferred_model = "gpt-4o"  # более качественный ответ
        fallback_model = "gpt-4o-mini"
        try:
            response = windexai_client.chat.completions.create(
                model=preferred_model,
                messages=messages,
                max_tokens=3000
            )
        except Exception as _:
            response = windexai_client.chat.completions.create(
                model=fallback_model,
            messages=messages,
                max_tokens=2500
            )
        
        # Получаем ответ
        content = response.choices[0].message.content
        print(f"Response received: {len(content) if content else 0} characters")
        
        return {
            "content": content or "Извините, не удалось сгенерировать сайт.",
            "status": "completed"
        }
        
    except Exception as e:
        print(f"AI Editor error: {str(e)}")
        return {
            "error": f"Ошибка генерации: {str(e)}",
            "status": "error"
        }

@router.get("/api/ai-editor/page")
async def get_editor_page():
    """Serve the AI Editor page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/editor.html")

@router.get("/api/ai-editor/test")
async def test_ai_editor():
    """Test endpoint"""
    return {"status": "AI Editor working"}