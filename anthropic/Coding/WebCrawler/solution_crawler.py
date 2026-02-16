from typing import Set, List
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

class WebCrawler:
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.visited = {start_url}
        self.lock = threading.Lock()
        self.max_threads = 4
        self.host = urlparse(start_url).netloc
        
    def sanitize(self, url: str) -> str:
        """
        Remove URL fragment (`#section`) as per interview requirement.
        """
        parsed = urlparse(url)
        # _replace available on namedtuple since Python 3.3
        cleaned = parsed._replace(fragment="")
        return urlunparse(cleaned)

    def is_valid(self, url: str) -> bool:
        parsed = urlparse(url)
        # Check scheme AND ensure same hostname as start_url (prevent crawling external sites)
        return parsed.scheme in ('http', 'https') and parsed.netloc == self.host

    def crawl_sequential(self):
        """Standard BFS crawl to demonstrate basic logic"""
        queue = deque([self.start_url])
        while queue:
            url = queue.popleft()
            print(f"Crawling: {url}")
            
            # Simulated fetch & parse
            new_links = self.fetch_mock(url)
            
            for link in new_links:
                clean_link = self.sanitize(link)
                if self.is_valid(clean_link) and clean_link not in self.visited:
                    self.visited.add(clean_link)
                    queue.append(clean_link)

    def crawl_multithreaded_pool(self):
        """
        Modern Concurrency using ThreadPoolExecutor.
        This handles task submission and waiting cleanly unlike manual Threading.
        """
        print(f"Starting Multi-threaded crawl with {self.max_threads} workers...")
        
        # We need a shared 'visited' set with locking
        # And a way to manage tasks dynamically
        futures = set()
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            # Initial task
            f = executor.submit(self.process_url, self.start_url)
            futures.add(f)
            
            while futures:
                # Wait for at least one future to complete
                # return_when=FIRST_COMPLETED simulates a reactive loop
                done, not_done = as_completed(futures, timeout=None), None # Actually as_completed is an iterator
                
                # Handling dynamic task addition is tricky with standard loop.
                # A common pattern: Loop while futures is not empty.
                # Use as_completed on a copy of the set? Or manual polling?
                # Actually, as_completed yields futures as they finish.
                # If a future spawns new work, we must submit it.
                pass 
                
                # Correct Pattern for Dynamic Tasks:
                # Use a while loop checking for done futures.
                # For simplicity in interview, use a synchronized Queue + Workers pattern or recursive submission.
                # But recursive submission in ThreadPool can deadlock if pool is full.
                # Best approach: Queue + Workers.
                # But let's stick to the Executor submission model if possible.
                
                # Simplified for demo (not strictly robust dynamic scaling):
                # Just submit all initial, collect results, submit next batch.
                # (BFS Level-by-Level is easier to implement safely).
                
                current_level_urls = [self.start_url]
                while current_level_urls:
                    next_level_urls = []
                    # Process current level in parallel
                    fs = [executor.submit(self.fetch_mock, u) for u in current_level_urls]
                    
                    for future in as_completed(fs):
                        links = future.result()
                        for link in links:
                            clean = self.sanitize(link)
                            with self.lock:
                                if self.is_valid(clean) and clean not in self.visited:
                                    self.visited.add(clean)
                                    next_level_urls.append(clean)
                    
                    current_level_urls = next_level_urls

    def process_url(self, url):
        return self.fetch_mock(url)

    def fetch_mock(self, url):
        time.sleep(0.1) # Simulate network I/O
        return [f"{url}/a", f"{url}/b#frag"]

# --- Distributed Design Stub ---

class DistributedCrawlerWorker:
    """
    Conceptual worker for a distributed system (Redis-based).
    """
    def __init__(self, redis_client):
        self.redis = redis_client
        self.queue_key = "crawl_queue"
        self.visited_key = "visited_urls"

    def run(self):
        while True:
            # Atomic pop from Redis List/Queue
            url_bytes = self.redis.lpop(self.queue_key)
            if not url_bytes:
                time.sleep(1)
                continue
            
            url = url_bytes.decode('utf-8')
            new_links = self.fetch_and_parse(url)
            
            for link in new_links:
                # Optimization: Check Bloom Filter first
                clean_link = self.sanitize(link) 
                if not self.redis.sismember(self.visited_key, clean_link):
                    self.redis.sadd(self.visited_key, clean_link)
                    self.redis.rpush(self.queue_key, clean_link)

    def sanitize(self, url):
        return url.split('#')[0]

    def fetch_and_parse(self, url):
        return []
