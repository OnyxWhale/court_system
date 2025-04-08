import logging
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class ForumParser:
    def __init__(self, base_url: str = settings.FORUM_BASE_URL):
        """
        Инициализация парсера форума.

        Args:
            base_url (str): Базовый URL форума (по умолчанию из настроек).
        """
        self.base_url = base_url.rstrip('/') + '/'
        self.root_url = "https://forum.gta5rp.com/"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Загружает страницу и возвращает объект BeautifulSoup.

        Args:
            url (str): URL страницы для загрузки.

        Returns:
            Optional[BeautifulSoup]: Объект BeautifulSoup или None при ошибке.
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            logger.error(f"Не удалось загрузить {url}: {e}")
            return None

    def parse_threads(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Парсит треды из объекта BeautifulSoup.

        Args:
            soup (BeautifulSoup): Объект BeautifulSoup с HTML страницы.

        Returns:
            List[Dict]: Список словарей с данными тредов.
        """
        threads = []
        for thread in soup.select(".structItem--thread"):
            title_elem = thread.select_one(".structItem-title a[data-xf-init='preview-tooltip']")
            if not title_elem:
                continue
            href = title_elem["href"].lstrip('/')
            url = f"{self.root_url}{href}" if href.startswith("threads/") else f"{self.root_url}threads/{href}"
            title = title_elem.text.strip()
            prefix_elem = thread.select_one(".structItem-title .label")
            prefix = prefix_elem.text.strip() if prefix_elem else "Нет"
            time_elem = thread.select_one(".structItem-startDate time")
            created_at = (
                datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00"))
                if time_elem
                else datetime.now()
            )
            threads.append({
                "url": url,
                "title": title,
                "prefix": prefix,
                "created_at": created_at,
                "updated_at": datetime.now()
            })
        return threads

    def parse_all_threads(self, pages: int, max_pages_per_run: int = 100) -> List[Dict]:
        """
        Парсит все треды с указанного количества страниц.

        Args:
            pages (int): Количество страниц для парсинга, заданное пользователем.
            max_pages_per_run (int): Максимальное количество страниц за один запуск.

        Returns:
            List[Dict]: Список словарей с данными тредов.
        """
        all_threads = []
        for page in range(1, min(pages, max_pages_per_run) + 1):
            page_url = self.base_url if page == 1 else f"{self.base_url}page-{page}"
            soup = self.fetch_page(page_url)
            if soup:
                threads = self.parse_threads(soup)
                all_threads.extend(threads)
                logger.info(f"Страница {page} успешно спарсена, найдено {len(threads)} тредов")
        return all_threads

    def parse_messages(self, thread_url: str) -> List[Dict]:
        """
        Парсит сообщения из указанного треда.

        Args:
            thread_url (str): URL треда на форуме.

        Returns:
            List[Dict]: Список словарей с данными сообщений.
        """
        soup = self.fetch_page(thread_url)
        if not soup:
            return []
        messages = []
        for msg in soup.select(".message.message--post"):
            msg_id = msg.get("data-content")
            msg_url = f"{thread_url}#{msg_id}" if msg_id else thread_url

            author_elem = msg.select_one(".message-userDetails .username")
            content_elem = msg.select_one(".message-content .bbWrapper")
            time_elem = msg.select_one(".message-attribution-main time.u-dt")

            author = author_elem.text.strip() if author_elem else "Unknown"
            content = content_elem.text.strip() if content_elem else "No content found"
            posted_at = (
                datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00"))
                if time_elem
                else datetime.now()
            )

            messages.append({
                "url": msg_url,
                "author": author,
                "content": content,
                "posted_at": posted_at
            })
        return messages