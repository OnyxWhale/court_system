import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ForumParser:
    def __init__(self, base_url="https://forum.gta5rp.com/forums/federalnyi-sud.1745/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.root_url = "https://forum.gta5rp.com/"  # Корневой URL для тредов
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def fetch_page(self, url):
        """Получает HTML-страницу по URL."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException:
            return None  # Возвращаем None при ошибке

    def parse_threads(self, soup):
        """Парсит список тредов с одной страницы."""
        threads = []
        for thread in soup.select(".structItem--thread"):
            title_elem = thread.select(".structItem-title a")[-1]
            if not title_elem:
                continue
            href = title_elem["href"].lstrip('/')
            # Формируем правильный URL для треда
            url = f"{self.root_url}{href}" if href.startswith("threads/") else f"{self.root_url}threads/{href}"
            title = title_elem.text.strip()
            prefix_elem = thread.select_one(".structItem-cell--meta .label")
            prefix = prefix_elem.text.strip() if prefix_elem else ""
            time_elem = thread.select_one(".structItem-startDate time")
            created_at = datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00")) if time_elem else datetime.now()
            threads.append({
                "url": url,
                "title": title,
                "prefix": prefix,
                "created_at": created_at,
                "updated_at": datetime.now()
            })
        return threads

    def parse_all_threads(self, pages):
        """Парсит треды с указанного количества страниц."""
        all_threads = []
        for page in range(1, pages + 1):
            page_url = self.base_url if page == 1 else f"{self.base_url}page-{page}"
            soup = self.fetch_page(page_url)
            if soup:
                threads = self.parse_threads(soup)
                all_threads.extend(threads)
        return all_threads

    def parse_messages(self, thread_url):
        """Парсит сообщения в треде."""
        soup = self.fetch_page(thread_url)
        if not soup:
            return []  # Если страница недоступна, возвращаем пустой список
        messages = []
        for message in soup.select(".message"):
            author_elem = message.select_one(".message-attribution-main a")
            content_elem = message.select_one(".bbWrapper")
            time_elem = message.select_one(".message-attribution-main time")
            if not (author_elem and content_elem):
                continue
            author = author_elem.text.strip()
            content = content_elem.text.strip()
            posted_at = datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00")) if time_elem else datetime.now()
            messages.append({
                "url": thread_url,
                "author": author,
                "content": content,
                "posted_at": posted_at
            })
        return messages