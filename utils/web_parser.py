"""
Универсальный веб-парсер для получения актуальной информации из интернета
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import logging

from utils.universal_parser import parse_web_page, search_and_parse_web, extract_info_by_selectors
from utils.advanced_web_search import get_advanced_web_search, format_advanced_search_results

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebParser:
    """Универсальный веб-парсер"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.cache = {}
        self.cache_duration = 300  # 5 минут кэширования
        
    def get_page_content(self, url: str) -> Optional[str]:
        """Получить содержимое страницы"""
        try:
            # Проверяем кэш
            if url in self.cache:
                cached_data, timestamp = self.cache[url]
                if time.time() - timestamp < self.cache_duration:
                    return cached_data
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Кэшируем результат
            self.cache[url] = (response.text, time.time())
            
            return response.text
        except Exception as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            return None
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Парсинг HTML"""
        return BeautifulSoup(html, 'html.parser')
    
    def get_crypto_prices(self) -> Dict[str, Any]:
        """Получить курсы криптовалют"""
        try:
            # Используем CoinGecko API для получения актуальных курсов
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,binancecoin,cardano,solana&vs_currencies=usd,rub&include_24hr_change=true"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "crypto_prices": {}
            }
            
            crypto_names = {
                "bitcoin": "Bitcoin (BTC)",
                "ethereum": "Ethereum (ETH)", 
                "binancecoin": "Binance Coin (BNB)",
                "cardano": "Cardano (ADA)",
                "solana": "Solana (SOL)"
            }
            
            for crypto_id, name in crypto_names.items():
                if crypto_id in data:
                    crypto_data = data[crypto_id]
                    result["crypto_prices"][name] = {
                        "usd": crypto_data.get("usd", 0),
                        "rub": crypto_data.get("rub", 0),
                        "change_24h": crypto_data.get("usd_24h_change", 0)
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении курсов криптовалют: {e}")
            return {"error": str(e)}
    
    def get_exchange_rates(self) -> Dict[str, Any]:
        """Получить курсы валют"""
        try:
            # Используем API Центробанка России
            url = "https://www.cbr-xml-daily.ru/daily_json.js"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "exchange_rates": {}
            }
            
            # Основные валюты
            currencies = ["USD", "EUR", "GBP", "CNY", "JPY"]
            
            for currency in currencies:
                if currency in data["Valute"]:
                    valute = data["Valute"][currency]
                    result["exchange_rates"][currency] = {
                        "name": valute["Name"],
                        "value": valute["Value"],
                        "previous": valute["Previous"],
                        "change": round(valute["Value"] - valute["Previous"], 4)
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении курсов валют: {e}")
            return {"error": str(e)}
    
    def get_news(self, query: str = "", limit: int = 5) -> Dict[str, Any]:
        """Получить новости"""
        try:
            # Используем NewsAPI (требует API ключ) или парсим новостные сайты
            news_sources = [
                "https://ria.ru",
                "https://tass.ru", 
                "https://lenta.ru"
            ]
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "news": []
            }
            
            for source in news_sources[:1]:  # Ограничиваем одним источником для демо
                try:
                    html = self.get_page_content(source)
                    if html:
                        soup = self.parse_html(html)
                        
                        # Ищем заголовки новостей (упрощенный парсинг)
                        headlines = soup.find_all(['h1', 'h2', 'h3'], limit=limit)
                        
                        for headline in headlines:
                            text = headline.get_text().strip()
                            if text and len(text) > 10:
                                result["news"].append({
                                    "title": text,
                                    "source": source,
                                    "url": headline.find('a')['href'] if headline.find('a') else None
                                })
                                
                except Exception as e:
                    logger.error(f"Ошибка при парсинге новостей с {source}: {e}")
                    continue
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при получении новостей: {e}")
            return {"error": str(e)}
    
    def get_weather(self, city: str = "Moscow") -> Dict[str, Any]:
        """Получить погоду"""
        try:
            # Используем OpenWeatherMap API (требует API ключ)
            # Для демо возвращаем заглушку
            return {
                "timestamp": datetime.now().isoformat(),
                "city": city,
                "weather": {
                    "temperature": "20°C",
                    "description": "Облачно",
                    "humidity": "65%",
                    "wind": "5 м/с"
                },
                "note": "Для получения реальных данных погоды требуется API ключ OpenWeatherMap"
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении погоды: {e}")
            return {"error": str(e)}
    
    def search_web(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Поиск в интернете"""
        try:
            # Используем DuckDuckGo для поиска (без API ключа)
            url = f"https://html.duckduckgo.com/html/?q={query}"
            
            html = self.get_page_content(url)
            if not html:
                return {"error": "Не удалось получить результаты поиска"}
            
            soup = self.parse_html(html)
            results = []
            
            # Парсим результаты поиска
            search_results = soup.find_all('div', class_='result', limit=limit)
            
            for result in search_results:
                try:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = title_elem.get('href', '')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
                        
                except Exception as e:
                    logger.error(f"Ошибка при парсинге результата поиска: {e}")
                    continue
            
            return {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Ошибка при поиске в интернете: {e}")
            return {"error": str(e)}
    
    def parse_general_info(self, topic: str) -> Dict[str, Any]:
        """Универсальный парсинг информации по теме"""
        try:
            # Определяем тип запроса и выбираем соответствующий метод
            topic_lower = topic.lower()
            
            if any(word in topic_lower for word in ['биткоин', 'bitcoin', 'btc', 'криптовалют', 'крипто', 'ethereum', 'eth', 'solana', 'sol', 'cardano', 'ada', 'binance', 'bnb']):
                return self.get_crypto_prices()
            elif any(word in topic_lower for word in ['курс', 'валют', 'доллар', 'евро', 'рубль']):
                return self.get_exchange_rates()
            elif any(word in topic_lower for word in ['новости', 'новость', 'news']):
                return self.get_news(topic)
            elif any(word in topic_lower for word in ['погода', 'weather']):
                return self.get_weather()
            else:
                # Для общих запросов используем поиск
                return self.search_web(topic)
                
        except Exception as e:
            logger.error(f"Ошибка при парсинге информации: {e}")
            return {"error": str(e)}

# Глобальный экземпляр парсера
web_parser = WebParser()

def get_web_info(topic: str) -> Dict[str, Any]:
    """Получить информацию из интернета по теме"""
    return web_parser.parse_general_info(topic)

def parse_any_website(url: str) -> Dict[str, Any]:
    """Универсальный парсинг любого веб-сайта"""
    return parse_web_page(url)

def search_and_parse_any(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Поиск и парсинг любых результатов"""
    return search_and_parse_web(query, num_results)

def extract_custom_info(url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """Извлечение кастомной информации по селекторам"""
    return extract_info_by_selectors(url, selectors)

def get_comprehensive_web_info(topic: str) -> Dict[str, Any]:
    """Получить комплексную информацию из интернета с продвинутым поиском"""
    try:
        # Сначала пробуем специализированные методы
        specialized_result = web_parser.parse_general_info(topic)
        
        # Если получили специализированные данные, возвращаем их
        if "error" not in specialized_result and any(key in specialized_result for key in ["crypto_prices", "exchange_rates", "news", "weather"]):
            return specialized_result
        
        # Иначе используем продвинутый поиск с TF-IDF ранжированием
        logger.info(f"Используем продвинутый поиск для: {topic}")
        advanced_search_result = get_advanced_web_search(topic, max_results=5)
        
        if "error" not in advanced_search_result and advanced_search_result.get("results"):
            return {
                "timestamp": datetime.now().isoformat(),
                "search_type": "advanced_search",
                "query": topic,
                "results": advanced_search_result["results"],
                "total_results": advanced_search_result["total_results"],
                "cache_hits": advanced_search_result.get("cache_hits", 0)
            }
        
        # Fallback к универсальному поиску
        logger.info(f"Fallback к универсальному поиску для: {topic}")
        search_result = search_and_parse_web(topic, num_results=3)
        
        if "error" not in search_result:
            return {
                "timestamp": datetime.now().isoformat(),
                "search_type": "universal_search",
                "search_results": search_result
            }
        
        return specialized_result
        
    except Exception as e:
        logger.error(f"Ошибка при получении комплексной информации: {e}")
        return {"error": str(e)}
