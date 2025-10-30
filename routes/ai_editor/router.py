"""
AI Editor Router
HTTP endpoints for AI code generation
"""

import time
from typing import Dict, List, Optional
import psutil
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from .models import (
    AIEditorRequest,
    AIEditorResponse,
    ElementEditRequest,
    LLMThought,
    CodePart,
    CombinedCodeResult,
    ConversationsListResponse,
    ConversationDetailResponse,
    EditElementResponse,
    StatusResponse,
    DownloadResponse,
    PreviewResponse,
)
from .services import (
    ArchitectService,
    DeveloperService,
    CodeCombiner,
    EditService,
    LLMThoughtsManager,
    send_llm_thought
)
from routes.auth import User, get_current_user
from database import Conversation as DBConversation, Message as DBMessage, get_db
from sqlalchemy.orm import Session
from utils.web_search import search_web, format_search_results
from .utils import should_search_web, extract_search_query

router = APIRouter()

# Глобальный менеджер мыслей LLM
llm_thoughts_manager = LLMThoughtsManager()


@router.get("/api/ai-editor/thoughts/{conversation_id}")
async def get_llm_thoughts(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[LLMThought]]:
    """Получает текущие мысли LLM для конкретной беседы"""
    thoughts = llm_thoughts_manager.get_thoughts(conversation_id)
    return {"thoughts": thoughts}


@router.post("/api/ai-editor")
async def ai_editor_endpoint(
    request: AIEditorRequest,
    current_user: User = Depends(get_current_user)
) -> AIEditorResponse:
    """
    Основной endpoint для AI редактора
    Генерирует веб-сайты на основе запросов пользователей
    """
    try:
        # Получаем последнее сообщение пользователя
        if not request.messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No messages provided"
            )

        last_message = request.messages[-1]["content"]

        # Инициализируем сервисы
        architect = ArchitectService()
        developer = DeveloperService()
        combiner = CodeCombiner()

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

            # TODO: Implement web search response handling
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Web search mode not implemented in refactored version"
            )

        elif request.use_two_stage and not web_search_results:
            # Используем двухэтапную систему LLM с последовательной генерацией
            print("🚀 Using two-stage LLM system with sequential generation")
            print(f"🔍 Debug: use_two_stage={request.use_two_stage}, web_search_results={bool(web_search_results)}")
            print(f"🚀 Two-stage mode: {request.mode}")

            # Инициализируем мысли LLM для этой беседы
            temp_conversation_id = str(conversation_id) if conversation_id else f"temp_{datetime.now().timestamp()}"
            print(f"🚀 Temporary conversation ID: {temp_conversation_id}")

            # Отправляем начальную мысль
            await send_llm_thought(temp_conversation_id, "💭", f"Анализирую запрос: \"{last_message[:50]}...\"")

            # Этап 1: Архитектор планирует
            await send_llm_thought(temp_conversation_id, "🏗️", "Создаю архитектурный план разработки...")
            plan = await architect.create_plan(last_message, request.mode)
            print(f"🏗️ Plan created: {len(plan.steps)} steps")

            # Отправляем мысль о создании плана
            await send_llm_thought(temp_conversation_id, "📋", f"Создан план из {len(plan.steps)} этапов")

            # Генерируем план для отображения с мыслями
            plan_steps_text = "\n".join([f"{i+1}. {step.name}" for i, step in enumerate(plan.steps)])
            plan_text = f"""💭 Анализирую запрос пользователя: "{last_message[:50]}..."

🏗️ Создаю архитектурный план разработки...

📋 **ПЛАН РАЗРАБОТКИ:**
{plan_steps_text}

🔧 **ИТОГОВАЯ СТРУКТУРА:**
{plan.final_structure}

⚡ Начинаю выполнение плана..."""

            # Этап 2: Генерируем код для каждого шага плана
            print(f"👨‍💻 Generating code for each step based on plan (Lite mode)...")
            print(f"👨‍💻 Plan analysis: {plan.analysis}")
            print(f"👨‍💻 Final structure: {plan.final_structure}")

            # Генерируем код для каждого шага
            code_parts: List[CodePart] = []
            for step in plan.steps:
                print(f"👨‍💻 Generating {step.code_type} code for step: {step.name}")
                code_part = await developer.generate_code(step, request.mode, plan.analysis)
                code_parts.append(code_part)
                print(f"✅ Generated {step.code_type} code for: {step.name}")

            print(f"🔧 Generated {len(code_parts)} code parts")

            # Объединяем все части в единый HTML файл
            print("🔧 Combining all code parts into single HTML file...")
            combined_result = await combiner.combine_parts(code_parts, request.mode)
            print("🔧 Successfully combined code parts")

            # Используем объединенный HTML как ответ
            raw_response = combined_result.content
            print(f"📄 Combined HTML length: {len(raw_response)} characters")
            print(f"📄 Combined HTML preview: {raw_response[:200]}...")

            # Проверяем наличие HTML_START маркера
            if "HTML_START" in raw_response:
                print("✅ HTML_START marker found in combined HTML")
            else:
                print("⚠️ HTML_START marker NOT found in combined HTML")

            # Отправляем мысли о генерации
            generation_thoughts = """
⚙️ Генерирую полный веб-сайт на основе созданного плана...

🤔 Учитываю требования к современному дизайну и адаптивности...

💡 Создаю единый HTML файл со всеми секциями..."""

            # Добавляем мысли о генерации
            generation_thoughts = f"{generation_thoughts}"

            # Получаем случайный стиль дизайна для разнообразия
            # TODO: Get design style from plan

            # Финальный результат с мыслями
            completed_steps_text = "\n".join([f"✅ {step.name}" for step in plan.steps])
            ai_response = f"""{plan_text}

{generation_thoughts}

✅ **ВЫПОЛНЕННЫЕ ЭТАПЫ:**
{completed_steps_text}

🎉 **Сайт успешно создан!**

{raw_response}"""

            return AIEditorResponse(
                content=ai_response,
                conversation_id=conversation_id or 1,  # TODO: Generate proper conversation ID
                status="completed",
                timestamp=datetime.now().isoformat()
            )

        else:
            # Одноэтапный режим (простые запросы)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Single-stage mode not implemented in refactored version"
            )

    except Exception as e:
        print(f"❌ AI Editor error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Editor error: {str(e)}"
        )


@router.get("/api/ai-editor/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ConversationsListResponse:
    """Получить список разговоров пользователя"""
    try:
        conversations = (
            db.query(DBConversation)
            .filter(DBConversation.user_id == current_user.id)
            .order_by(DBConversation.created_at.desc())
            .all()
        )

        return ConversationsListResponse(
            conversations=[
                {
                    "id": conv.id,
                    "title": conv.title,
                    "date": conv.created_at.isoformat(),
                    "message_count": len(conv.messages),
                }
                for conv in conversations
            ]
        )
    except Exception as e:
        print(f"Ошибка получения разговоров: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ai-editor/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
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

        return ConversationDetailResponse(
            conversation={
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
        )
    except HTTPException:
        raise
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

        db.delete(conversation)
        db.commit()

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка удаления разговора: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/ai-editor/edit-element")
async def edit_element(
    request: ElementEditRequest,
    current_user: User = Depends(get_current_user)
) -> EditElementResponse:
    """Редактирование конкретного элемента"""
    edit_service = EditService()
    return await edit_service.edit_element(request)


@router.get("/api/ai-editor/status")
async def get_status() -> StatusResponse:
    """Проверка статуса AI редактора"""
    # Получаем базовую информацию о системе
    uptime = time.time() - psutil.boot_time()

    # TODO: Получить реальные данные о разговорах и сообщениях
    total_conversations = 0
    total_messages = 0

    return StatusResponse(
        status="Editor working",
        uptime=uptime,
        total_conversations=total_conversations,
        total_messages=total_messages
    )


@router.get("/api/ai-editor/download/{conversation_id}")
async def download_project(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DownloadResponse:
    """Скачать Next.js проект как ZIP файл"""
    # TODO: Implement project download functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Download functionality not implemented in refactored version"
    )


@router.get("/api/ai-editor/project/{conversation_id}/preview")
async def preview_project(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PreviewResponse:
    """Предварительный просмотр проекта"""
    # TODO: Implement project preview functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Preview functionality not implemented in refactored version"
    )


@router.get("/api/ai-editor/project/{conversation_id}/preview-proxy/{path:path}")
async def preview_proxy(
    conversation_id: int,
    path: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Прокси для предварительного просмотра проекта"""
    # TODO: Implement preview proxy functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Preview proxy functionality not implemented in refactored version"
    )


@router.get("/api/ai-editor/project/{conversation_id}/preview-proxy")
async def preview_proxy_root(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Прокси для корневого предварительного просмотра проекта"""
    # TODO: Implement preview proxy root functionality
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Preview proxy root functionality not implemented in refactored version"
    )
