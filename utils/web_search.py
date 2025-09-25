import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import re

class WebSearchEngine:
    """Веб-поисковик для получения актуальной информации из интернета"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_google(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Поиск через Google (без API)"""
        try:
            # Формируем URL для поиска
            search_url = f"https://www.google.com/search?q={query}&num={num_results}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Ищем результаты поиска
            search_results = soup.find_all('div', class_='g')
            
            for result in search_results[:num_results]:
                try:
                    # Заголовок и ссылка
                    title_elem = result.find('h3')
                    link_elem = result.find('a')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        url = link_elem.get('href', '')
                        
                        # Очищаем URL от Google редиректов
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        # Описание
                        desc_elem = result.find('span', class_='aCOpRe') or result.find('div', class_='VwiC3b')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if title and url and url.startswith('http'):
                            results.append({
                                'title': title,
                                'url': url,
                                'description': description
                            })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска Google: {e}")
            return []
    
    def search_duckduckgo(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Поиск через DuckDuckGo"""
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Ищем результаты поиска
            search_results = soup.find_all('div', class_='result')
            
            for result in search_results[:num_results]:
                try:
                    title_elem = result.find('a', class_='result__a')
                    desc_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = title_elem.get('href', '')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if title and url:
                            results.append({
                                'title': title,
                                'url': url,
                                'description': description
                            })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска DuckDuckGo: {e}")
            return []
    
    def search_bing(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Поиск через Bing"""
        try:
            search_url = f"https://www.bing.com/search?q={query}&count={num_results}"
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # Ищем результаты поиска
            search_results = soup.find_all('li', class_='b_algo')
            
            for result in search_results[:num_results]:
                try:
                    title_elem = result.find('h2')
                    link_elem = result.find('a')
                    desc_elem = result.find('p')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        url = link_elem.get('href', '')
                        description = desc_elem.get_text().strip() if desc_elem else ""
                        
                        if title and url:
                            results.append({
                                'title': title,
                                'url': url,
                                'description': description
                            })
                except Exception as e:
                    continue
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска Bing: {e}")
            return []
    
    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """Универсальный поиск по веб-источникам"""
        print(f"🔍 Поиск в интернете: {query}")
        
        # Пробуем разные поисковики
        search_engines = [
            self.search_duckduckgo,
            self.search_bing,
            self.search_google
        ]
        
        all_results = []
        
        for search_func in search_engines:
            try:
                results = search_func(query, num_results)
                if results:
                    all_results.extend(results)
                    break  # Если получили результаты, останавливаемся
            except Exception as e:
                print(f"Ошибка поисковика: {e}")
                continue
        
        # Убираем дубликаты по URL
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        return unique_results[:num_results]
    
    def fetch_page_content(self, url: str, max_length: int = 2000) -> str:
        """Получение содержимого веб-страницы"""
        try:
            print(f"📄 Загружаю страницу: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Удаляем скрипты и стили
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Получаем текст
            text = soup.get_text()
            
            # Очищаем текст
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Ограничиваем длину
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            print(f"Ошибка загрузки страницы {url}: {e}")
            return ""
    
    def search_and_fetch_content(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """Поиск и получение содержимого страниц"""
        # Сначала ищем
        search_results = self.search_web(query, num_results)
        
        # Затем получаем содержимое найденных страниц
        enriched_results = []
        
        for result in search_results:
            content = self.fetch_page_content(result['url'])
            
            enriched_results.append({
                'title': result['title'],
                'url': result['url'],
                'description': result['description'],
                'content': content
            })
            
            # Небольшая пауза между запросами
            time.sleep(1)
        
        return enriched_results

# Глобальный экземпляр поисковика
web_search_engine = WebSearchEngine()

def search_web(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    """Функция для поиска в интернете"""
    return web_search_engine.search_and_fetch_content(query, num_results)

def format_search_results(results: List[Dict[str, str]]) -> str:
    """Форматирование результатов поиска для LLM"""
    if not results:
        return "Результаты поиска не найдены."
    
    formatted = "🔍 РЕЗУЛЬТАТЫ ПОИСКА В ИНТЕРНЕТЕ:\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"{i}. **{result['title']}**\n"
        formatted += f"   URL: {result['url']}\n"
        if result['description']:
            formatted += f"   Описание: {result['description']}\n"
        if result['content']:
            formatted += f"   Содержимое: {result['content'][:500]}...\n"
        formatted += "\n"
    
    return formatted
