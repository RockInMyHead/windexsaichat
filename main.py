from typing import List

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import database
from database import create_tables
# Import routers
from routes import (admin, ai_editor, auth, chat, conversations, dashboard,
                    deploy, documents, voice)

# Create tables on startup
create_tables()

app = FastAPI(title="WindexsAi", description="Chat Platform with Model Selection")

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
app.include_router(deploy.router)
app.include_router(voice.router)
app.include_router(documents.router)
app.include_router(dashboard.router)


# Pydantic models for API documentation
class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    max_tokens: int
    capabilities: List[str]


# Available models
MODELS = {
    "gpt-4o-mini": ModelInfo(
        id="gpt-4o-mini",
        name="WIndexAI Lite",
        description="Быстрая и эффективная модель для повседневных задач",
        max_tokens=16384,
        capabilities=["текст", "код", "анализ", "перевод"],
    ),
    "gpt-4o": ModelInfo(
        id="gpt-4o",
        name="WIndexAI Pro",
        description="Продвинутая модель с расширенными возможностями",
        max_tokens=16384,
        capabilities=["текст", "код", "анализ", "перевод", "креативность", "логика"],
    ),
}


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/pricing", response_class=HTMLResponse)
async def read_pricing():
    """Serve the pricing HTML page"""
    return FileResponse("static/pricing.html")


@app.get("/editor", response_class=HTMLResponse)
async def read_editor():
    """Serve the AI editor HTML page"""
    return FileResponse("static/editor.html")


@app.get("/style.css")
async def get_css():
    """Serve CSS file directly"""
    return FileResponse("static/style.css", media_type="text/css")


@app.get("/script.js")
async def get_js():
    """Serve JS file directly"""
    return FileResponse("static/script.js", media_type="application/javascript")


@app.get("/editor.js")
async def get_editor_js():
    """Serve Editor JS file directly"""
    return FileResponse("static/editor.js", media_type="application/javascript")


@app.get("/round_logo-07.svg")
async def get_logo():
    """Serve logo SVG file directly"""
    return FileResponse("static/round_logo-07.svg", media_type="image/svg+xml")


@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon file directly"""
    return FileResponse("static/favicon.ico", media_type="image/x-icon")


@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {"models": MODELS}


# Public deployment route
@app.get("/deploy/{deploy_url}", response_class=HTMLResponse)
async def serve_public_deployment(deploy_url: str):
    """Serve deployed website publicly"""
    from database import get_db
    from routes.deploy import serve_deployment

    # Get database session
    db = next(get_db())
    try:
        return await serve_deployment(deploy_url, db)
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1107)
# flake8: noqa
