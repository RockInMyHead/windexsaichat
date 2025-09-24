from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

# Import routers
from routes import auth, chat, conversations, admin, ai_editor

app = FastAPI(title="WindexAI", description="AI Chat Platform with Model Selection")

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

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(admin.router)
app.include_router(ai_editor.router)

# Pydantic models for API documentation
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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/editor", response_class=HTMLResponse)
async def read_editor():
    """Serve the AI editor HTML page"""
    return FileResponse("static/editor.html")

@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {"models": MODELS}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
