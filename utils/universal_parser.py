"""
Универсальный парсер веб-страниц для извлечения структурированной информации
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import time
import logging
from urllib.parse import urljoin, urlparse
import html2text

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UniversalWebParser:
    """Универсальный парсер веб-страниц"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.cache = {}
        self.cache_duration = 300  # 5 минут кэширования
        
        # Инициализация html2text для конвертации в markdown
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False
        self.h2t.body_width = 0  # Не ограничивать ширину
        
    def get_page_content(self, url: str) -> Optional[str]:
        """Получить содержимое страницы"""
        try:
            # Проверяем кэш
            if url in self.cache:
                cached_data, timestamp = self.cache[url]
                if time.time() - timestamp < self.cache_duration:
                    return cached_data
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Определяем кодировку
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            # Кэшируем результат
            self.cache[url] = (response.text, time.time())
            
            return response.text
        except Exception as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            return None
    
    def parse_page(self, url: str) -> Dict[str, Any]:
        """Универсальный парсинг страницы"""
        try:
            html_content = self.get_page_content(url)
            if not html_content:
                return {"error": "Не удалось получить содержимое страницы"}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Извлекаем основную информацию
            result = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "title": self._extract_title(soup),
                "description": self._extract_description(soup),
                "keywords": self._extract_keywords(soup),
                "headings": self._extract_headings(soup),
                "paragraphs": self._extract_paragraphs(soup),
                "links": self._extract_links(soup, url),
                "images": self._extract_images(soup, url),
                "tables": self._extract_tables(soup),
                "lists": self._extract_lists(soup),
                "metadata": self._extract_metadata(soup),
                "structured_data": self._extract_structured_data(soup),
                "text_content": self._extract_text_content(soup),
                "markdown_content": self._convert_to_markdown(soup)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге страницы {url}: {e}")
            return {"error": str(e)}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечь заголовок страницы"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Альтернативные варианты
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечь описание страницы"""
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        # Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        # Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc.get('content').strip()
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Извлечь ключевые слова"""
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            keywords = keywords_tag.get('content').split(',')
            return [kw.strip() for kw in keywords if kw.strip()]
        return []
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Извлечь заголовки всех уровней"""
        headings = {}
        for level in range(1, 7):
            tag_name = f'h{level}'
            tags = soup.find_all(tag_name)
            headings[f'h{level}'] = [tag.get_text().strip() for tag in tags if tag.get_text().strip()]
        return headings
    
    def _extract_paragraphs(self, soup: BeautifulSoup) -> List[str]:
        """Извлечь параграфы"""
        paragraphs = []
        p_tags = soup.find_all('p')
        for p in p_tags:
            text = p.get_text().strip()
            if text and len(text) > 20:  # Фильтруем короткие параграфы
                paragraphs.append(text)
        return paragraphs
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Извлечь ссылки"""
        links = []
        a_tags = soup.find_all('a', href=True)
        
        for a in a_tags:
            href = a.get('href')
            text = a.get_text().strip()
            
            if href and text:
                # Преобразуем относительные ссылки в абсолютные
                absolute_url = urljoin(base_url, href)
                
                links.append({
                    "url": absolute_url,
                    "text": text,
                    "title": a.get('title', ''),
                    "domain": urlparse(absolute_url).netloc
                })
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Извлечь изображения"""
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src')
            if src:
                # Преобразуем относительные ссылки в абсолютные
                absolute_url = urljoin(base_url, src)
                
                images.append({
                    "url": absolute_url,
                    "alt": img.get('alt', ''),
                    "title": img.get('title', ''),
                    "width": img.get('width', ''),
                    "height": img.get('height', '')
                })
        
        return images
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечь таблицы"""
        tables = []
        table_tags = soup.find_all('table')
        
        for table in table_tags:
            table_data = {
                "headers": [],
                "rows": [],
                "caption": ""
            }
            
            # Извлекаем заголовки
            header_row = table.find('tr')
            if header_row:
                headers = header_row.find_all(['th', 'td'])
                table_data["headers"] = [h.get_text().strip() for h in headers]
            
            # Извлекаем строки данных
            rows = table.find_all('tr')[1:]  # Пропускаем заголовок
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text().strip() for cell in cells]
                if row_data:
                    table_data["rows"].append(row_data)
            
            # Извлекаем подпись таблицы
            caption = table.find('caption')
            if caption:
                table_data["caption"] = caption.get_text().strip()
            
            if table_data["rows"]:  # Добавляем только непустые таблицы
                tables.append(table_data)
        
        return tables
    
    def _extract_lists(self, soup: BeautifulSoup) -> Dict[str, List[List[str]]]:
        """Извлечь списки"""
        lists = {"ul": [], "ol": []}
        
        for list_type in ["ul", "ol"]:
            list_tags = soup.find_all(list_type)
            for list_tag in list_tags:
                items = []
                li_tags = list_tag.find_all('li')
                for li in li_tags:
                    text = li.get_text().strip()
                    if text:
                        items.append(text)
                
                if items:
                    lists[list_type].append(items)
        
        return lists
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Извлечь метаданные"""
        metadata = {}
        
        # Извлекаем все meta теги
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def _extract_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлечь структурированные данные (JSON-LD, microdata)"""
        structured_data = []
        
        # JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append({
                    "type": "json-ld",
                    "data": data
                })
            except json.JSONDecodeError:
                continue
        
        # Microdata
        items = soup.find_all(attrs={'itemscope': True})
        for item in items:
            item_data = {
                "type": "microdata",
                "itemtype": item.get('itemtype', ''),
                "properties": {}
            }
            
            # Извлекаем свойства
            props = item.find_all(attrs={'itemprop': True})
            for prop in props:
                prop_name = prop.get('itemprop')
                prop_value = prop.get('content') or prop.get_text().strip()
                item_data["properties"][prop_name] = prop_value
            
            structured_data.append(item_data)
        
        return structured_data
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Извлечь весь текстовый контент"""
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Получаем текст
        text = soup.get_text()
        
        # Очищаем текст
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def _convert_to_markdown(self, soup: BeautifulSoup) -> str:
        """Конвертировать HTML в Markdown"""
        try:
            return self.h2t.handle(str(soup))
        except Exception as e:
            logger.error(f"Ошибка при конвертации в markdown: {e}")
            return ""
    
    def search_and_parse(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """Поиск и парсинг результатов"""
        try:
            # Используем DuckDuckGo для поиска
            search_url = f"https://html.duckduckgo.com/html/?q={query}"
            
            html_content = self.get_page_content(search_url)
            if not html_content:
                return {"error": "Не удалось получить результаты поиска"}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Парсим результаты поиска
            search_results = soup.find_all('div', class_='result', limit=num_results)
            
            for result in search_results:
                try:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = title_elem.get('href', '')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        # Парсим найденную страницу
                        parsed_page = self.parse_page(url) if url else {}
                        
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet,
                            "parsed_content": parsed_page
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
            logger.error(f"Ошибка при поиске и парсинге: {e}")
            return {"error": str(e)}
    
    def extract_specific_info(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Извлечь специфическую информацию по CSS селекторам"""
        try:
            html_content = self.get_page_content(url)
            if not html_content:
                return {"error": "Не удалось получить содержимое страницы"}
            
            soup = BeautifulSoup(html_content, 'html.parser')
            result = {}
            
            for key, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        result[key] = elements[0].get_text().strip()
                    else:
                        result[key] = [elem.get_text().strip() for elem in elements]
                else:
                    result[key] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении специфической информации: {e}")
            return {"error": str(e)}

# Глобальный экземпляр парсера
universal_parser = UniversalWebParser()

def parse_web_page(url: str) -> Dict[str, Any]:
    """Парсинг веб-страницы"""
    return universal_parser.parse_page(url)

def search_and_parse_web(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Поиск и парсинг результатов"""
    return universal_parser.search_and_parse(query, num_results)

def extract_info_by_selectors(url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
    """Извлечение информации по селекторам"""
    return universal_parser.extract_specific_info(url, selectors)
