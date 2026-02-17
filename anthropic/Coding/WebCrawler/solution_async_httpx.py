import asyncio
import httpx
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import logging

# Simplified logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

class AsyncCrawler:
    def __init__(self, start_url: str, max_concurrency: int = 5, limit: int = 50, output_file: str = None):
        self.start_url = start_url
        self.host = urlparse(start_url).netloc
        self.limit = limit
        self.output_file = output_file
        self.max_concurrency = max_concurrency
        self.sem = asyncio.Semaphore(max_concurrency)
        self.visited = set()
        self.client = None

    async def log_found(self, url: str):
        pass
        # if self.output_file:
        #     with open(self.output_file, "a", encoding="utf-8") as f:
        #         f.write(url + "\n")

    async def get_all_links(self, url: str) -> list:
        html = ""
        async with self.sem:
            try:
                response = await self.client.get(url, timeout=10.0, follow_redirects=True)
                if response.status_code == 200 and 'text/html' in response.headers.get('content-type', ''):
                    html = response.text
            except Exception:
                return []

        if not html: return []

        soup = BeautifulSoup(html, "html.parser")
        links = []
        for tag in soup.find_all('a', href=True):
            full_url = urljoin(url, tag['href'])
            parsed = urlparse(full_url)
            clean_url = urlunparse(parsed._replace(fragment=""))
            
            # Basic validation
            if parsed.scheme in ('http', 'https') and parsed.netloc == self.host:
                links.append(clean_url)
        return links

    async def _worker(self, queue):
        while True:
            try:
                current_url = await queue.get()
            except asyncio.CancelledError:
                return

            try:
                if len(self.visited) >= self.limit:
                    continue
                
                links = await self.get_all_links(current_url)
                for link in links:
                    if link not in self.visited:
                        if len(self.visited) >= self.limit:
                            break
                        self.visited.add(link)
                        queue.put_nowait(link)
                        await self.log_found(link)
            finally:
                queue.task_done()

    async def crawl_bfs(self):
        print(f"Starting Parallel BFS ({self.max_concurrency} workers)...")
        self.visited = {self.start_url}
        queue = asyncio.Queue()
        queue.put_nowait(self.start_url)
        
        async with httpx.AsyncClient() as client:
            self.client = client
            workers = [asyncio.create_task(self._worker(queue)) for _ in range(self.max_concurrency)]
            await queue.join()
            for w in workers: w.cancel()

    async def crawl_dynamic(self):
        """Dynamic Bag-of-Tasks Strategy (Interview Pattern)."""
        print(f"Starting Dynamic Futures Crawl...")
        self.visited = {self.start_url}
        pending = set()
        
        # Start initial task
        # Note: In this pattern, we must ensure self.client is ready.
        async with httpx.AsyncClient() as client:
            self.client = client
            
            # Create first task
            # We wrap get_all_links in a task. 
            # Since get_all_links waits on self.sem, we rely on that for throttling network,
            # but we can have many pending tasks waiting for the semaphore.
            first_task = asyncio.create_task(self.get_all_links(self.start_url))
            pending.add(first_task)
            
            while pending:
                # Wait for any task to complete
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                
                for task in done:
                    if len(self.visited) >= self.limit:
                        break
                    
                    try:
                        links = task.result()
                        for link in links:
                            if link not in self.visited:
                                if len(self.visited) >= self.limit:
                                    break
                                self.visited.add(link)
                                await self.log_found(link)
                                
                                # Schedule next task immediately
                                new_task = asyncio.create_task(self.get_all_links(link))
                                pending.add(new_task)
                    except Exception:
                        pass
                
                if len(self.visited) >= self.limit:
                    for t in pending: t.cancel()
                    break

    async def crawl_sequential(self):
        print("Starting Sequential Crawl...")
        self.visited = {self.start_url}
        queue = [self.start_url]
        
        async with httpx.AsyncClient() as client:
            self.client = client
            while queue and len(self.visited) <= self.limit:
                current_url = queue.pop(0)
                if len(self.visited) > self.limit: break
                    
                links = await self.get_all_links(current_url)
                for link in links:
                    if link not in self.visited:
                        if len(self.visited) >= self.limit: break
                        self.visited.add(link)
                        queue.append(link)
                        await self.log_found(link)

async def measure_time(name, coro):
    start = time.perf_counter()
    await coro
    end = time.perf_counter()
    duration = end - start
    print(f"{name} took {duration:.2f} seconds\n")
    return duration

async def main():
    start_url = "https://crawler-test.com/"
    output_file = "crawler_output.txt"
    limit = 200
    
    with open(output_file, "w") as f:
        f.write(f"Benchmarks for {start_url} (Limit={limit})\n\n")

    # BFS
    with open(output_file, "a") as f: f.write("--- BFS ---\n")
    crawler_bfs = AsyncCrawler(start_url, limit=limit, output_file=output_file)
    time_bfs = await measure_time("BFS", crawler_bfs.crawl_bfs())
    with open(output_file, "a") as f: f.write(f"\nTime: {time_bfs:.2f}s\n\n")
    
    # Dynamic
    with open(output_file, "a") as f: f.write("--- Dynamic ---\n")
    crawler_dyn = AsyncCrawler(start_url, limit=limit, output_file=output_file)
    time_dyn = await measure_time("Dynamic", crawler_dyn.crawl_dynamic())
    with open(output_file, "a") as f: f.write(f"\nTime: {time_dyn:.2f}s\n\n")

    # Sequential
    with open(output_file, "a") as f: f.write("--- Sequential ---\n")
    crawler_seq = AsyncCrawler(start_url, limit=limit, output_file=output_file)
    time_seq = await measure_time("Sequential", crawler_seq.crawl_sequential())
    with open(output_file, "a") as f: f.write(f"\nTime: {time_seq:.2f}s\n\n")
    
    print(f"Results written to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
