import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class AsyncCrawler:
    def __init__(self, max_concurrency=10):
        self.visited = set()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.start_hostname = None
        self.session = None

    def get_hostname(self, url):
        return urlparse(url).hostname

    def sanitize(self, url):
        idx = url.find('#')
        if idx > 0:
            url = url[:idx]
        return url

    async def get_links_from(self, url):
        """
        Fetch URL content and extract links asynchronously.
        Note: BeautifulSoup parsing is CPU-bound and blocks the event loop slightly.
        For high performance, wrap BS4 parsing in `asyncio.to_thread`.
        """
        try:
            async with self.semaphore:  # Limit concurrent requests
                async with self.session.get(url, timeout=10) as resp:
                    # print(f"Fetching: {url}")
                    if resp.status != 200:
                        return []
                    text = await resp.text()  # Await the body download
            
            # Parsing (CPU-bound) - Ideally offload to thread
            # links = await asyncio.to_thread(self.parse_links, text, url)
            
            # Simple inline parsing for interview
            soup = BeautifulSoup(text, "html.parser")
            links = [urljoin(url, a["href"]) for a in soup.find_all("a", href=True)]
            return links

        except Exception as e:
            # print(f"Error fetching {url}: {e}")
            return []

    async def crawl(self, start_url):
        self.start_hostname = self.get_hostname(start_url)
        self.session = aiohttp.ClientSession()
        try:
            await self.dfs(start_url)
        finally:
            await self.session.close()
        return list(self.visited)

    async def dfs(self, url):
        """
        Recursive DFS approach.
        In production, a Queue-based worker pool is safer to avoid RecursionError.
        """
        url = self.sanitize(url)
        if not url or url in self.visited:
            return
        if self.get_hostname(url) != self.start_hostname:
            return # Stay on same host

        self.visited.add(url)
        
        # Get links
        links = await self.get_links_from(url)
        
        # Concurrently crawl children
        # This spawns massive number of tasks quickly.
        # Ideally use a bounded queue.
        if links:
            await asyncio.gather(*(self.dfs(link) for link in links))

# --- Main For Testing ---
async def main():
    crawler = AsyncCrawler(max_concurrency=5)
    # Stub: Won't work without internet. Just checks syntax.
    # result = await crawler.crawl("https://www.google.com")
    pass

if __name__ == "__main__":
    # asyncio.run(main())
    pass
