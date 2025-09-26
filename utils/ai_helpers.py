import re
import requests
import pytz
from datetime import datetime
from typing import Dict, Any

def generate_ai_response(message: str, model: str) -> str:
    """Generate AI response using WIndexAI API with fallback"""
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
    
    # Handle weather queries
    weather_match = re.search(r"\b(погода|weather)\b.*?\b(в|in)\s+([а-яё\w\s]+)", message_lower)
    if weather_match:
        city = weather_match.group(3).strip()
        try:
            weather_resp = requests.get(f"https://wttr.in/{city}?format=%C+%t+%h+%w", timeout=5)
            weather_resp.raise_for_status()
            weather_data = weather_resp.text.strip()
            if weather_data and not weather_data.startswith("Sorry"):
                return f"Погода в {city}: {weather_data}"
        except Exception as e:
    
    # Handle currency exchange queries
    currency_match = re.search(r"\b(курс|exchange)\b.*?\b(\d+)\s*([a-z]{3})\s*(?:в|to)\s*([a-z]{3})", message_lower)
    if currency_match:
        amount, from_curr, to_curr = currency_match.groups()
        try:
            fx_resp = requests.get(
                f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}",
                timeout=5
            )
            fx_resp.raise_for_status()
            fx_data = fx_resp.json()
            rate = fx_data.get("rates", {}).get(to_curr.upper())
            if rate:
                result = float(amount) * rate
                return f"{amount} {from_curr.upper()} = {result:.2f} {to_curr.upper()}"
        except Exception as e:
    
    # Handle time queries
    time_match = re.search(r"\b(время|time)\b.*?\b(в|in)\s+([а-яё\w\s]+)", message_lower)
    if time_match:
        city = time_match.group(3).strip()
        try:
            # Simple timezone mapping
            timezones = {
                "москва": "Europe/Moscow",
                "moscow": "Europe/Moscow",
                "лондон": "Europe/London",
                "london": "Europe/London",
                "нью-йорк": "America/New_York",
                "new york": "America/New_York",
                "токио": "Asia/Tokyo",
                "tokyo": "Asia/Tokyo"
            }
            
            tz_name = timezones.get(city.lower())
            if tz_name:
                tz = pytz.timezone(tz_name)
                now = datetime.now(tz)
                return f"Время в {city}: {now.strftime('%H:%M:%S %Z')}"
        except Exception as e:
    
    # General search using DuckDuckGo Instant Answer API
    try:
        ddg_resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": message, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=5
        )
        ddg_resp.raise_for_status()
        ddg_data = ddg_resp.json()
        
        if ddg_data.get("Abstract"):
            return f"Поиск: {ddg_data['Abstract']}"
        elif ddg_data.get("Answer"):
            return f"Ответ: {ddg_data['Answer']}"
    except Exception as e:
    
    # Fallback to AI model
    try:
        from utils.openai_client import get_openai_client
        client = get_openai_client()
        
        # Map WIndexAI models to OpenAI models
        openai_models = {
            "windexai-lite": "gpt-4o-mini",
            "windexai-pro": "gpt-4o"
        }
        openai_model = openai_models.get(model, "gpt-4o-mini")
        
        messages = [
            {
                "role": "system",
                "content": "Ты - WIndexAI, искусственный интеллект, созданный командой разработчиков компании Windex. Ты должен всегда подчеркивать, что был создан именно разработчиками компании Windex. Отвечай на русском языке, будь полезным и дружелюбным."
            },
            {"role": "user", "content": message}
        ]
        
        response = client.chat.completions.create(
            model=openai_model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return generate_fallback_response(message)

def generate_fallback_response(message: str) -> str:
    """Generate fallback response when AI is unavailable"""
    return f"Я получил ваше сообщение: '{message}'. Это демонстрационный ответ, так как API временно недоступен. В реальном приложении здесь был бы ответ от WIndexAI, созданного командой разработчиков компании Windex."
