import requests
from bs4 import BeautifulSoup
from datetime import datetime

class ForumParser:
    def __init__(self, base_url="https://forum.gta5rp.com/forums/federalnyi-sud.1745/"):
        self.base_url = base_url.rstrip('/') + '/'
        self.root_url = "https://forum.gta5rp.com/"
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def fetch_page(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            return None

    def parse_threads(self, soup):
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
        all_threads = []
        for page in range(1, pages + 1):
            page_url = self.base_url if page == 1 else f"{self.base_url}page-{page}"
            soup = self.fetch_page(page_url)
            if soup:
                threads = self.parse_threads(soup)
                all_threads.extend(threads)
        return all_threads

    def parse_messages(self, thread_url):
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
            posted_at = datetime.fromisoformat(time_elem["datetime"].replace("Z", "+00:00")) if time_elem else datetime.now()

            messages.append({
                "url": msg_url,
                "author": author,
                "content": content,
                "posted_at": posted_at
            })
        return messages