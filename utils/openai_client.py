from openai import OpenAI
import os
import tempfile
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Model configurations
MODELS = {
    "gpt-4o-mini": {
        "name": "WIndexAI Lite",
        "description": "Быстрая и эффективная модель для повседневных задач",
        "max_tokens": 16384,
        "temperature": 0.7
    },
    "gpt-4o": {
        "name": "WIndexAI Pro", 
        "description": "Продвинутая модель с расширенными возможностями",
        "max_tokens": 16384,
        "temperature": 0.7
    }
}

def get_openai_client() -> OpenAI:
    """Get OpenAI client instance"""
    return openai_client

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get model configuration"""
    return MODELS.get(model_name, MODELS["gpt-4o-mini"])

def generate_response(messages: List[Dict[str, str]], model: str = "gpt-4o-mini") -> str:
    """Generate AI response using OpenAI API"""
    try:
        model_config = get_model_config(model)
        
        response = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=model_config["max_tokens"],
            temperature=model_config["temperature"],
            stream=False
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        # Более детальная обработка ошибок
        if "max_tokens" in str(e):
            return "Извините, произошла ошибка с настройками модели. Попробуйте еще раз."
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
        formatted_messages.append({
            "role": message["role"],
            "content": message["content"]
        })
    
    return formatted_messages

def transcribe_audio(audio_file_path: str) -> str:
    """Transcribe audio file using OpenAI Whisper"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ru"  # Russian language
            )
        return transcript.text
    except Exception as e:
        return None

def text_to_speech(text: str, voice: str = "alloy") -> str:
    """Convert text to speech using OpenAI TTS"""
    try:
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.write(response.content)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        return None