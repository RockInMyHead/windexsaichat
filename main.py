from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uvicorn
import json
import os
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from passlib.context import CryptContext
from jose import JWTError, jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="WindexAI", description="AI Chat Platform with Model Selection")

# WIndexAI API Configuration
WINDEXAI_API_KEY = os.getenv("WINDEXAI_API_KEY", "your-openai-api-key-here")

# Initialize OpenAI client
windexai_client = OpenAI(api_key=WINDEXAI_API_KEY)

# Authentication Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "windexai-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic models
class User(BaseModel):
    id: str
    username: str
    email: str
    created_at: str
    role: str  # 'user' or 'admin'

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    conversation_id: str
    model_used: str
    timestamp: str

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    max_tokens: int
    capabilities: List[str]

# Available models
MODELS = {
    "windexai-lite": ModelInfo(
        id="windexai-lite",
        name="WIndexAI Lite",
        description="Быстрая и эффективная модель для повседневных задач",
        max_tokens=4000,
        capabilities=["текст", "код", "анализ", "перевод"]
    ),
    "windexai-pro": ModelInfo(
        id="windexai-pro",
        name="WIndexAI Pro",
        description="Продвинутая модель с расширенными возможностями",
        max_tokens=8000,
        capabilities=["текст", "код", "анализ", "перевод", "креативность", "логика"]
    )
}

# In-memory storage (в реальном проекте используйте базу данных)
users_db = {}
conversations = {}

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if username in users_db:
        user_dict = users_db[username]
        return User(**user_dict)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, users_db[username]["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

# Authentication endpoints
@app.post("/api/auth/register", response_model=User)
async def register(user: UserCreate):
    """Register a new user"""
    if user.username in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    # Check if email is already used
    for existing_user in users_db.values():
        if existing_user["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    hashed_password = get_password_hash(user.password)
    user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # First registered user becomes admin
    role = "admin" if not users_db else "user"
    
    users_db[user.username] = {
        "id": user_id,
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now().isoformat(),
        "role": role
    }
    
    return User(**users_db[user.username])

# Admin panel endpoints
@app.get("/api/admin/users")
async def list_users(current_user: User = Depends(get_current_user)):
    """List all registered users (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return {"users": [u for u in users_db.values()]}  

@app.put("/api/admin/users/{username}/role")
async def update_user_role(username: str, role: str, current_user: User = Depends(get_current_user)):
    """Update a user's role (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if username not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if role not in ('user', 'admin'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    users_db[username]['role'] = role
    return {"message": f"Role for {username} updated to {role}"}

@app.post("/api/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Login user and return access token"""
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {"models": list(MODELS.values())}

@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """Get specific model info"""
    if model_id not in MODELS:
        raise HTTPException(status_code=404, detail="Model not found")
    return MODELS[model_id]

@app.post("/api/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Handle chat requests"""
    if request.model not in MODELS:
        raise HTTPException(status_code=400, detail="Invalid model")
    
    # Generate conversation ID if not provided
    if not request.conversation_id:
        conversation_id = f"conv_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        conversation_id = request.conversation_id
    
    # Initialize conversation if new
    if conversation_id not in conversations:
        conversations[conversation_id] = {
            "id": conversation_id,
            "title": "Новый чат",
            "timestamp": datetime.now().isoformat(),
            "messages": []
        }
    
    # Add user message
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]["messages"].append(user_message)
    
    # Generate AI response
    ai_response = generate_ai_response(request.message, request.model)
    
    # Add AI response
    ai_message = ChatMessage(
        role="assistant",
        content=ai_response,
        timestamp=datetime.now().isoformat()
    )
    conversations[conversation_id]["messages"].append(ai_message)
    
    # Update conversation title based on first user message
    if len(conversations[conversation_id]["messages"]) == 2:  # First exchange
        title = request.message[:50] + "..." if len(request.message) > 50 else request.message
        conversations[conversation_id]["title"] = title
    
    return ChatResponse(
        response=ai_response,
        conversation_id=conversation_id,
        model_used=request.model,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation": conversations[conversation_id]}

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversation deleted"}
    raise HTTPException(status_code=404, detail="Conversation not found")

@app.get("/api/conversations")
async def get_user_conversations(current_user: User = Depends(get_current_user)):
    """Get all conversations for current user"""
    user_conversations = []
    for conv_id, conv_data in conversations.items():
        if conv_id.startswith(f"conv_{current_user.username}_"):
            user_conversations.append({
                "id": conv_id,
                "title": conv_data.get("title", "Новый чат"),
                "timestamp": conv_data.get("timestamp", ""),
                "message_count": len(conv_data.get("messages", []))
            })
    
    # Sort by timestamp (newest first)
    user_conversations.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"conversations": user_conversations}

@app.post("/api/conversations")
async def create_conversation(current_user: User = Depends(get_current_user)):
    """Create a new conversation"""
    conversation_id = f"conv_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    conversations[conversation_id] = {
        "id": conversation_id,
        "title": "Новый чат",
        "timestamp": datetime.now().isoformat(),
        "messages": []
    }
    return {"conversation_id": conversation_id}

@app.put("/api/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, title: str, current_user: User = Depends(get_current_user)):
    """Update conversation title"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if user owns this conversation
    if not conversation_id.startswith(f"conv_{current_user.username}_"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    conversations[conversation_id]["title"] = title
    return {"message": "Conversation updated"}

@app.delete("/api/conversations")
async def clear_all_conversations(current_user: User = Depends(get_current_user)):
    """Clear all conversations for current user"""
    user_conversations = [conv_id for conv_id in conversations.keys() 
                         if conv_id.startswith(f"conv_{current_user.username}_")]
    
    for conv_id in user_conversations:
        del conversations[conv_id]
    
    return {"message": f"Deleted {len(user_conversations)} conversations"}

def generate_ai_response(message: str, model: str) -> str:
    """Generate AI response using WIndexAI API with fallback"""
    import re
    # Lowercase message for parsing
    message_lower = message.lower()
    
    # Handle bitcoin price queries
    if re.search(r"\b(биткоин\w*|биткойн\w*)\b", message_lower):
        try:
            cg_resp = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "bitcoin", "vs_currencies": "rub"},
                timeout=5
            )
            cg_resp.raise_for_status()
            cg = cg_resp.json()
            price = cg.get("bitcoin", {}).get("rub")
            if price:
                return f"Текущая цена биткоина: {price} RUB"
        except Exception as e:
            print(f"CoinGecko API error: {e}")
            # proceed to other parsers
    # Attempt to fetch instant answer from DuckDuckGo
    try:
        ddg_resp = requests.get("https://api.duckduckgo.com/", params={"q": message, "format": "json", "no_html": 1, "skip_disambig": 1}, timeout=5)
        ddg_resp.raise_for_status()
        ddg_data = ddg_resp.json()
        abstract = ddg_data.get("AbstractText")
        if abstract:
            return abstract
        related = ddg_data.get("RelatedTopics")
        if related and isinstance(related, list) and related:
            first = related[0]
            if "Text" in first and first["Text"]:
                return first["Text"]
            if "Topics" in first and first["Topics"]:
                sub = first["Topics"][0]
                if "Text" in sub:
                    return sub["Text"]
    except Exception as e:
        print(f"DuckDuckGo API error: {e}")
    
    # Handle weather queries with live data from wttr.in
    if "погода" in message_lower:
        # Extract city after 'в' or 'в городе'
        city_patterns = [
            r"погода\s+в\s+(\w+)",
            r"погода\s+в\s+городе\s+(\w+)",
            r"какая\s+погода\s+в\s+(\w+)",
            r"погода\s+(\w+)"
        ]
        
        city = "москве"  # default
        for pattern in city_patterns:
            match = re.search(pattern, message_lower)
            if match:
                city = match.group(1)
                break
        
        try:
            print(f"Fetching weather for: {city}")
            weather_resp = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()
            
            cond = weather_data["current_condition"][0]
            temp = cond["temp_C"]
            desc = cond["weatherDesc"][0]["value"]
            humidity = cond["humidity"]
            wind_speed = cond["windspeedKmph"]
            
            return f"Сейчас в {city.capitalize()}: {temp}°C, {desc}. Влажность: {humidity}%, ветер: {wind_speed} км/ч."
        except Exception as e:
            print(f"Weather API error: {e}")
            return "Не удалось получить данные о погоде. Попробуйте позже."
    
    # Handle currency exchange queries
    elif any(word in message_lower for word in ["курс", "доллар", "евро", "рубль", "валюта"]):
        try:
            print("Fetching currency rates")
            # Using exchangerate-api.com for currency rates
            currency_resp = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
            currency_resp.raise_for_status()
            currency_data = currency_resp.json()
            
            usd_to_rub = currency_data["rates"]["RUB"]
            eur_to_rub = currency_data["rates"]["RUB"] / currency_data["rates"]["EUR"]
            
            return f"Курс валют на сегодня: 1 USD = {usd_to_rub:.2f} RUB, 1 EUR = {eur_to_rub:.2f} RUB"
        except Exception as e:
            print(f"Currency API error: {e}")
            return "Не удалось получить актуальный курс валют. Попробуйте позже."
    
    # Handle time queries
    elif any(word in message_lower for word in ["время", "который час", "сколько времени"]):
        from datetime import datetime
        import pytz
        
        try:
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = datetime.now(moscow_tz)
            time_str = moscow_time.strftime("%H:%M")
            date_str = moscow_time.strftime("%d.%m.%Y")
            
            return f"Сейчас в Москве: {time_str}, {date_str}"
        except Exception as e:
            print(f"Time error: {e}")
            current_time = datetime.now().strftime("%H:%M")
            return f"Сейчас {current_time} (время сервера)"
    
    try:
        # Determine max_tokens and OpenAI model based on WIndexAI model
        if model == "windexai-lite":
            max_tokens = 1000
            openai_model = "gpt-4o-mini"
        else:  # windexai-pro
            max_tokens = 2000
            openai_model = "gpt-5-nano"
        
        # Prepare messages for WIndexAI API with system prompt
        messages = [
            {
                "role": "system", 
                "content": "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным."
            },
                {"role": "user", "content": message}
        ]
        
        print(f"Making request to WIndexAI API with model: {model}")
        
        # Make request to WIndexAI API
        response = windexai_client.chat.completions.create(
            model=openai_model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Return response without model prefix
        return ai_response
            
    except Exception as e:
        print(f"WIndexAI API Error: {e}, using fallback")
        return generate_fallback_response(message, model)

def generate_fallback_response(message: str, model: str) -> str:
    """Generate fallback response when API is unavailable"""
    # Simple responses based on message content
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["привет", "hello", "hi", "здравствуй"]):
        return "Привет! Я WIndexAI, созданный командой разработчиков компании Windex. Я готов помочь вам. Чем могу быть полезен?"
    elif any(word in message_lower for word in ["кто тебя", "кто создал", "кто сделал", "кто тебя сделал"]):
        return "Меня создала команда разработчиков компании Windex. Я горжусь тем, что являюсь продуктом их инновационной работы в области искусственного интеллекта."
    elif any(word in message_lower for word in ["как дела", "how are you", "что нового"]):
        return "У меня все отлично! Я готов отвечать на ваши вопросы и помогать с различными задачами. Команда разработчиков Windex сделала меня очень эффективным помощником."
    elif any(word in message_lower for word in ["спасибо", "thank you", "thanks"]):
        return "Пожалуйста! Рад был помочь. Если у вас есть еще вопросы, обращайтесь! Я всегда готов помочь, как и задумали мои создатели из компании Windex."
    elif any(word in message_lower for word in ["погода", "weather"]):
        return "К сожалению, я не могу получить актуальную информацию о погоде. Рекомендую проверить погодное приложение или сайт. Но я могу помочь с другими задачами!"
    elif any(word in message_lower for word in ["время", "time", "который час"]):
        current_time = datetime.now().strftime("%H:%M")
        return f"Сейчас {current_time}. Время на сервере может отличаться от вашего местного времени."
    else:
        return f"Я получил ваше сообщение: '{message}'. Это демонстрационный ответ, так как API временно недоступен. В реальном приложении здесь был бы ответ от WIndexAI, созданного командой разработчиков компании Windex."

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
