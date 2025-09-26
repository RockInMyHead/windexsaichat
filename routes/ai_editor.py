import os
import json
import re
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from routes.auth import get_current_user, User
from utils.openai_client import openai_client
from utils.web_search import search_web, format_search_results
from database import get_db, Conversation as DBConversation, Message as DBMessage

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

@router.post("/api/ai-editor", response_model=AIEditorResponse)
async def ai_editor(request: AIEditorRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Editor endpoint for website generation with web search capability"""
    
    try:
        
        # Получаем последнее сообщение пользователя
        last_message = request.messages[-1] if request.messages else None
        user_message = last_message.get('content', '') if last_message else ''
        
        # Управление разговором
        if not request.conversation_id:
            # Создаем новый разговор для AI редактора
            conversation = DBConversation(
                title="Новый проект сайта",
                conversation_type="ai_editor",
                user_id=current_user.id
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            conversation_id = conversation.id
        else:
            conversation_id = request.conversation_id
            # Проверяем, что разговор принадлежит пользователю
            conversation = db.query(DBConversation).filter(
                DBConversation.id == conversation_id,
                DBConversation.user_id == current_user.id,
                DBConversation.conversation_type == "ai_editor"
            ).first()
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        
        # Добавляем сообщение пользователя в базу данных
        if last_message and last_message.get('role') == 'user':
            user_message_db = DBMessage(
                role="user",
                content=user_message,
                conversation_id=conversation_id
            )
            db.add(user_message_db)
            db.commit()
        
        # Проверяем, нужен ли веб-поиск
        web_search_results = ""
        if last_message and last_message.get('role') == 'user' and should_search_web(user_message):
            
            # Извлекаем поисковый запрос
            search_query = extract_search_query(user_message)
            if not search_query:
                search_query = user_message
            
            # Выполняем поиск
            try:
                search_results = search_web(search_query, num_results=3)
                web_search_results = format_search_results(search_results)
            except Exception as e:
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
                "content": """Ты senior React/Next.js разработчик и UI/UX дизайнер. Создавай современные, премиальные веб-приложения на Next.js с правильной модульной архитектурой и TypeScript.

ОБЯЗАТЕЛЬНО:
• Используй Next.js 14+ с App Router
• TypeScript для типизации
• Tailwind CSS для стилизации  
• Модульная архитектура с компонентами
• Responsive дизайн (Mobile-first)
• Семантический HTML и accessibility
• Оптимизированные изображения с next/image

СТРУКТУРА NEXT.JS ПРОЕКТА:
```
project-name/
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── components/
│       ├── ui/
│       │   ├── Button.tsx
│       │   ├── Card.tsx
│       │   └── Container.tsx
│       ├── sections/
│       │   ├── Hero.tsx
│       │   ├── Features.tsx
│       │   └── Footer.tsx
│       └── layout/
│           ├── Header.tsx
│           └── Navigation.tsx
├── lib/
│   ├── types.ts
│   └── utils.ts
└── public/
    ├── images/
    └── icons/
```

ТЕХНОЛОГИИ:
• Next.js 14+ (App Router)
• TypeScript
• Tailwind CSS
• React 18+ (Hooks, Context)
• Next.js Image optimization
• Responsive design patterns
• Modern CSS (Container queries, Grid, Flexbox)

ФОРМАТ ОТВЕТА (строго):
1) Краткое описание проекта (1–2 предложения)
2) Структура файлов:
FILE_STRUCTURE_START
project-name/
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── next.config.js
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── globals.css
│   └── components/
└── lib/
FILE_STRUCTURE_END

3) Содержимое каждого файла:

PACKAGE_JSON_START
{
  "name": "project-name",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "autoprefixer": "^10.0.0",
    "postcss": "^8.0.0",
    "tailwindcss": "^3.0.0",
    "typescript": "^5.0.0"
  }
}
PACKAGE_JSON_END

TSCONFIG_START
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
TSCONFIG_END

TAILWIND_CONFIG_START
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
    },
  },
  plugins: [],
}
export default config
TAILWIND_CONFIG_END

NEXT_CONFIG_START
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['images.unsplash.com', 'images.pexels.com'],
  },
}

module.exports = nextConfig
NEXT_CONFIG_END

LAYOUT_TSX_START
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Project Name',
  description: 'Project description',
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
}
LAYOUT_TSX_END

PAGE_TSX_START
import Hero from './components/sections/Hero'
import Features from './components/sections/Features'
import Footer from './components/sections/Footer'

export default function Home() {
  return (
    <main>
      <Hero />
      <Features />
      <Footer />
    </main>
  )
}
PAGE_TSX_END

GLOBALS_CSS_START
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
GLOBALS_CSS_END

Далее создавай компоненты в соответствующих папках с TypeScript типизацией.

4) Инструкции по запуску:
- npm install
- npm run dev
- Открыть http://localhost:3000"""
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
                max_tokens=3000
            )
        except Exception as _:
            response = openai_client.chat.completions.create(
                model=fallback_model,
            messages=messages,
                max_tokens=2500
            )
        
        # Получаем ответ
        content = response.choices[0].message.content
        
        # Добавляем ответ AI в базу данных
        ai_message_db = DBMessage(
            role="assistant",
            content=content or "Извините, не удалось сгенерировать сайт.",
            conversation_id=conversation_id
        )
        db.add(ai_message_db)
        
        # Обновляем заголовок разговора на основе первого сообщения пользователя
        if len(request.messages) == 1:  # Первый обмен
            title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            conversation.title = title
        
        db.commit()
        
        return AIEditorResponse(
            content=content or "Извините, не удалось сгенерировать сайт.",
            conversation_id=conversation_id,
            status="completed",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        return AIEditorResponse(
            content=f"Ошибка генерации: {str(e)}",
            conversation_id=conversation_id if 'conversation_id' in locals() else 0,
            status="error",
            timestamp=datetime.now().isoformat()
        )

@router.post("/api/ai-editor/edit-element")
async def edit_element(
    request: ElementEditRequest,
    user: User = Depends(get_current_user)
):
    """Редактирование конкретного элемента на сайте"""
    try:
        
        # Создаем промпт для редактирования элемента
        edit_prompt = f"""
Ты - эксперт по веб-разработке. Пользователь хочет отредактировать элемент на своем сайте.

ИНФОРМАЦИЯ ОБ ЭЛЕМЕНТЕ:
- Тип элемента: {request.element_type}
- Текущий текст: "{request.current_text}"
- Инструкция по редактированию: {request.edit_instruction}

ТЕКУЩИЙ HTML КОД САЙТА:
{request.html_content}

ЗАДАЧА:
Отредактируй указанный элемент согласно инструкции пользователя. Сохрани весь остальной HTML код без изменений.

ТРЕБОВАНИЯ:
1. Найди элемент с текстом "{request.current_text}" в HTML
2. Примени изменения согласно инструкции "{request.edit_instruction}"
3. Сохрани структуру и стили сайта
4. Верни полный обновленный HTML код
5. Объясни, что именно было изменено

ИЗОБРАЖЕНИЯ ИЗ ИНТЕРНЕТА:
• Если пользователь просит добавить изображение, используй прямые ссылки на изображения
• Хорошие источники: Unsplash, Pexels, Pixabay
• Всегда добавляй alt-текст для доступности
• Используй адаптивные CSS стили для изображений

ФОРМАТ ОТВЕТА:
Ответь в формате:
RESPONSE_START
[Твое объяснение изменений]
RESPONSE_END

HTML_START
[Полный обновленный HTML код]
HTML_END
"""

        # Отправляем запрос к OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты - эксперт по веб-разработке и HTML/CSS."},
                {"role": "user", "content": edit_prompt}
            ],
            max_tokens=4000,
            temperature=0.3
        )
        
        response_text = response.choices[0].message.content
        
        # Извлекаем HTML код из ответа
        html_match = re.search(r'HTML_START\s*(.*?)\s*HTML_END', response_text, re.DOTALL)
        response_match = re.search(r'RESPONSE_START\s*(.*?)\s*RESPONSE_END', response_text, re.DOTALL)
        
        if html_match:
            updated_html = html_match.group(1).strip()
            response_text = response_match.group(1).strip() if response_match else "Элемент успешно отредактирован."
            
            return {
                "html_content": updated_html,
                "response": response_text,
                "status": "success"
            }
        else:
            # Если не удалось извлечь HTML, возвращаем оригинальный код
            return {
                "html_content": request.html_content,
                "response": "Не удалось применить изменения. Попробуйте более конкретную инструкцию.",
                "status": "error"
            }
        
    except Exception as e:
        return {
            "html_content": request.html_content,
            "response": f"Ошибка при редактировании: {str(e)}",
            "status": "error"
        }

@router.get("/api/ai-editor/conversations")
async def get_ai_editor_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all AI editor conversations for current user"""
    conversations = db.query(DBConversation).filter(
        DBConversation.user_id == current_user.id,
        DBConversation.conversation_type == "ai_editor"
    ).order_by(DBConversation.updated_at.desc()).all()
    
    user_conversations = []
    for conv in conversations:
        # Count messages
        message_count = db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).count()
        # Get last message for preview
        last_msg = db.query(DBMessage).filter(DBMessage.conversation_id == conv.id).order_by(DBMessage.timestamp.desc()).first()
        snippet = last_msg.content if last_msg else ''
        snippet_date = last_msg.timestamp.isoformat() if last_msg else conv.created_at.isoformat()
        user_conversations.append({
            "id": conv.id,
            "title": conv.title,
            "preview": snippet,
            "date": snippet_date,
            "message_count": message_count
        })
    
    return {"conversations": user_conversations}

@router.get("/api/ai-editor/conversations/{conversation_id}")
async def get_ai_editor_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get AI editor conversation history"""
    conversation = db.query(DBConversation).filter(
        DBConversation.id == conversation_id,
        DBConversation.user_id == current_user.id,
        DBConversation.conversation_type == "ai_editor"
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(DBMessage).filter(
        DBMessage.conversation_id == conversation_id
    ).order_by(DBMessage.timestamp).all()
    
    conversation_data = {
        "id": conversation.id,
        "title": conversation.title,
        "timestamp": conversation.created_at.isoformat(),
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]
    }
    
    return {"conversation": conversation_data}

@router.post("/api/ai-editor/conversations")
async def create_ai_editor_conversation(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new AI editor conversation"""
    conversation = DBConversation(
        title="Новый проект сайта",
        conversation_type="ai_editor",
        user_id=current_user.id
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return {"conversation_id": conversation.id}

@router.delete("/api/ai-editor/conversations/{conversation_id}")
async def delete_ai_editor_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete AI editor conversation"""
    conversation = db.query(DBConversation).filter(
        DBConversation.id == conversation_id,
        DBConversation.user_id == current_user.id,
        DBConversation.conversation_type == "ai_editor"
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete all messages first
    db.query(DBMessage).filter(DBMessage.conversation_id == conversation_id).delete()
    
    # Delete conversation
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted"}

@router.get("/api/ai-editor/page")
async def get_editor_page():
    """Serve the Editor page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/editor.html")

@router.get("/api/ai-editor/test")
async def test_ai_editor():
    """Test endpoint"""
    return {"status": "Editor working"}