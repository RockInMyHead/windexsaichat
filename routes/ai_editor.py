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

router = APIRouter()


class AIEditorRequest(BaseModel):
    messages: List[Dict[str, str]]
    model: str = "gpt-4o-mini"
    conversation_id: Optional[int] = None


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
        
        # Проверяем, нужен ли веб-поиск
        web_search_results = None
        if should_search_web(last_message):
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
        else:
            # Для обычных запросов создания сайтов
            system_message = {
                "role": "system",
                "content": """Ты senior React/Next.js разработчик. Создавай СЛОЖНЫЕ, ПРОДВИНУТЫЕ веб-приложения с современным дизайном, анимациями и интерактивностью.

КРИТИЧЕСКИ ВАЖНО:
• Создавай ПОЛНОЦЕННЫЕ приложения с бизнес-логикой
• Используй современные UI/UX паттерны
• Добавляй анимации, переходы, hover-эффекты
• Включай интерактивные элементы (формы, модалы, слайдеры)
• Используй градиенты, тени, скругления
• Добавляй адаптивный дизайн для всех устройств
• Создавай реалистичный контент и функциональность

ТРЕБОВАНИЯ К ДИЗАЙНУ:
• Современные градиенты и цветовые схемы
• Анимации при скролле и наведении
• Интерактивные кнопки с эффектами
• Карточки с тенями и hover-эффектами
• Адаптивная сетка (grid/flexbox)
• Красивые типографика и spacing

ТРЕБОВАНИЯ К ФУНКЦИОНАЛЬНОСТИ:
• Рабочие формы с валидацией
• Модальные окна и попапы
• Слайдеры и карусели
• Анимации появления элементов
• Интерактивные кнопки и ссылки
• Состояния загрузки и ошибок

ФОРМАТ ОТВЕТА - ТОЛЬКО КОД:

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
{полный app/layout.tsx с мета-тегами}
```
LAYOUT_TSX_END

PAGE_TSX_START
```tsx
{полный app/page.tsx с главной страницей}
```
PAGE_TSX_END

GLOBALS_CSS_START
```css
{полный app/globals.css с кастомными стилями и анимациями}
```
GLOBALS_CSS_END

HERO_COMPONENT_START
```tsx
{сложный Hero с анимациями и интерактивностью}
```
HERO_COMPONENT_END

FEATURES_COMPONENT_START
```tsx
{интерактивные Features с hover-эффектами}
```
FEATURES_COMPONENT_END

FOOTER_COMPONENT_START
```tsx
{красивый Footer с ссылками и соцсетями}
```
FOOTER_COMPONENT_END

BUTTON_COMPONENT_START
```tsx
{анимированные кнопки с состояниями}
```
BUTTON_COMPONENT_END

CARD_COMPONENT_START
```tsx
{интерактивные карточки с анимациями}
```
CARD_COMPONENT_END

CONTAINER_COMPONENT_START
```tsx
{адаптивный контейнер}
```
CONTAINER_COMPONENT_END

MODAL_COMPONENT_START
```tsx
{модальные окна с анимациями}
```
MODAL_COMPONENT_END

FORM_COMPONENT_START
```tsx
{формы с валидацией и стилями}
```
FORM_COMPONENT_END

НЕ ДОБАВЛЯЙ:
- Простые статичные сайты
- Базовые стили без анимаций
- Отсутствие интерактивности
- Простые карточки без эффектов

СОЗДАВАЙ СЛОЖНЫЕ, СОВРЕМЕННЫЕ ПРИЛОЖЕНИЯ!""",
            }

        # Подготавливаем сообщения
        messages = [system_message] + request.messages
        
        # Делаем запрос к WindexAI с предпочтением более сильной модели, с безопасным фолбэком
        preferred_model = "gpt-4o"  # более качественный ответ
        fallback_model = "gpt-4o-mini"
        try:
            response = openai_client.chat.completions.create(
                model=preferred_model,
                messages=messages,
                max_tokens=8000,
                temperature=0.3,
            )
        except Exception as e:
            print(f"Ошибка с основной моделью {preferred_model}: {e}")
            # Фолбэк на более дешевую модель
            response = openai_client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                max_tokens=8000,
                temperature=0.3,
            )
        
        ai_response = response.choices[0].message.content
        
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

ЗАДАЧА: Отредактируй элемент "{request.element_type}" в HTML коде.

ТЕКУЩИЙ ТЕКСТ: {request.current_text}
ИНСТРУКЦИЯ ПО РЕДАКТИРОВАНИЮ: {request.edit_instruction}
ТЕКУЩИЙ HTML: {request.html_content}

ТРЕБОВАНИЯ:
1. Сохрани структуру и стили
2. Примени изменения точно по инструкции
3. Убедись, что HTML остается валидным
4. Сохрани все классы и атрибуты

ФОРМАТ ОТВЕТА:
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
            temperature=0.3,
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
                content = content.replace("import '../globals.css';", "import './globals.css';")
            
            # Исправляем page.tsx для правильного импорта компонентов
            if filename == "app/page.tsx":
                content = content.replace("from './components/", "from '../components/")
                # Удаляем неправильный импорт Layout
                content = content.replace("import Layout from './layout';", "")
                content = content.replace("import Layout from '../layout';", "")
                content = content.replace("import Layout from './layout'", "")
                # Удаляем обертку Layout
                content = content.replace("<Layout>", "<>")
                content = content.replace("</Layout>", "</>")

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

    # Запускаем сервер
    try:
        from utils.nextjs_manager import nextjs_manager as manager
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
        print(f"Proxy error details: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Proxy error: {type(e).__name__}: {str(e)}")
