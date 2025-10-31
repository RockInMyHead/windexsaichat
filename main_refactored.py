"""
Main application entry point - Refactored version
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from core.database import create_tables
from routes import (
    admin, auth, chat, conversations, dashboard,
    deploy, documents, profile, voice
)
from routes.cloud_mock import router as cloud_mock_router
from schemas.chat import ModelInfo


# Create database tables
create_tables()

# Create FastAPI app
app = FastAPI(
    title="WindexAI",
    description="AI-powered chat platform with multiple models",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
app.include_router(deploy.router)
app.include_router(voice.router)
app.include_router(documents.router)
app.include_router(dashboard.router)
app.include_router(profile.router)
app.include_router(cloud_mock_router)


# Root endpoint
@app.get("/")
async def root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html", media_type="text/html")


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


# API documentation for models
@app.get("/api/models", response_model=dict)
async def get_models():
    """Get available AI models"""
    from utils.ai_config import MODEL_CONFIGS

    models = {}
    for model_id, config in MODEL_CONFIGS.items():
        models[model_id] = ModelInfo(
            id=model_id,
            name=config["name"],
            description=config["description"],
            max_tokens=config["max_tokens"],
            capabilities=config.get("capabilities", ["текст", "код", "анализ"])
        )

    return {"models": models}


if __name__ == "__main__":
    uvicorn.run(
        "main_refactored:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
