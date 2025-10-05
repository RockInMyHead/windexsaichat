import os
import tempfile
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI
import httpx

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Proxy Configuration
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USERNAME = os.getenv("PROXY_USERNAME")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD")

# Build proxy URL if enabled
proxy_url = None
if PROXY_ENABLED and PROXY_HOST and PROXY_PORT:
    if PROXY_USERNAME and PROXY_PASSWORD:
        proxy_url = f"http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        proxy_url = f"http://{PROXY_HOST}:{PROXY_PORT}"
    print(f"🌐 Proxy enabled: {PROXY_HOST}:{PROXY_PORT}")

# Initialize OpenAI client always using a simple httpx Client
if OPENAI_API_KEY and OPENAI_API_KEY != "sk-demo-key-replace-with-real-openai-key":
    try:
        http_client = httpx.Client()
        openai_client = OpenAI(api_key=OPENAI_API_KEY, http_client=http_client)
        print("✅ OpenAI client initialized successfully")
    except Exception as e:
        print(f"❌ Warning: Failed to initialize OpenAI client: {e}")
        openai_client = None
else:
    print("⚠️ OpenAI API key not configured")
    openai_client = None

# Import new AI configuration
try:
    from .ai_config import (get_enhanced_user_prompt, get_generation_params,
                            get_model_config, get_system_prompt)
except ImportError as e:
    print(f"Warning: Could not import ai_config: {e}")
    # Fallback functions
    def get_enhanced_user_prompt(message): return message
    def get_generation_params(model): return {}
    def get_model_config(model): return {}
    def get_system_prompt(): return ""

# Legacy MODELS dict for backward compatibility
MODELS = {
    "gpt-4o-mini": {
        "name": "WIndexAI Lite",
        "description": "Быстрая и эффективная модель для повседневных задач",
        "max_tokens": 2000,
        "temperature": 0.7,
        "top_p": 0.9,
    },
    "gpt-4o": {
        "name": "WIndexAI Pro",
        "description": "Продвинутая модель с расширенными возможностями",
        "max_tokens": 6000,
        "temperature": 0.65,
        "top_p": 0.95,
    },
}


def get_openai_client() -> OpenAI:
    """Get OpenAI client instance"""
    return openai_client


def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get model configuration - now uses new AI config"""
    from .ai_config import get_model_config as get_ai_model_config

    return get_ai_model_config(model_name)


def generate_response(
    messages: List[Dict[str, str]], model: str = "gpt-4o-mini"
) -> str:
    """Generate AI response using OpenAI API with enhanced analytical system"""
    if not openai_client:
        return "⚠️ OpenAI API ключ не настроен. Пожалуйста, добавьте ваш API ключ в файл .env"

    try:
        # Get generation parameters from new config
        gen_params = get_generation_params(model)

        # Prepare enhanced messages
        enhanced_messages = []

        # Add system prompt
        system_prompt = get_system_prompt()
        enhanced_messages.append(system_prompt)

        # Process user messages and enhance the last user message
        for i, msg in enumerate(messages):
            if msg.get("role") == "user" and i == len(messages) - 1:
                # This is the last user message - enhance it
                enhanced_user_prompt = get_enhanced_user_prompt(msg["content"])
                enhanced_messages.append(
                    {"role": "user", "content": enhanced_user_prompt}
                )
            else:
                # Keep other messages as is
                enhanced_messages.append(msg)

        response = openai_client.chat.completions.create(
            model=gen_params["model"],
            messages=enhanced_messages,
            max_tokens=gen_params["max_tokens"],
            temperature=gen_params["temperature"],
            top_p=gen_params["top_p"],
            stream=False,
        )

        return response.choices[0].message.content

    except Exception as e:
        # Более детальная обработка ошибок
        if "max_tokens" in str(e):
            return (
                "Извините, произошла ошибка с настройками модели. Попробуйте еще раз."
            )
        elif "rate_limit" in str(e).lower():
            return "Превышен лимит запросов. Пожалуйста, подождите немного и попробуйте снова."
        elif "invalid_api_key" in str(e).lower():
            return "Ошибка API ключа. Обратитесь к администратору."
        else:
            return f"Извините, произошла ошибка при генерации ответа: {str(e)[:100]}..."


def format_messages_for_openai(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Format messages for OpenAI API"""
    formatted_messages = []

    for message in messages:
        formatted_messages.append(
            {"role": message["role"], "content": message["content"]}
        )

    return formatted_messages


def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper"""
    if not openai_client:
        return None

    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, language="ru"  # Russian language
            )
        return transcript.text
    except Exception as e:
        return None


def text_to_speech(text: str, voice: str = "alloy") -> str:
    """Convert text to speech using OpenAI TTS"""
    if not openai_client:
        return None

    try:
        response = openai_client.audio.speech.create(
            model="tts-1", voice=voice, input=text
        )

        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(response.content)
        temp_file.close()

        return temp_file.name
    except Exception as e:
        return None
