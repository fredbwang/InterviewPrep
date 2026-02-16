from typing import Set, List
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
import threading
import time

class WebCrawler:
    def __init__(self, start_url: str):
        self.start_url = start_url
        self.visited = {start_url}
        self.visited_lock = threading.Lock() # Explicit lock name
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

    def crawl_multithreaded(self):
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
            f_start = executor.submit(self.process_url, self.start_url)
            futures.add(f_start)
            
            while futures:
                # Wait for at least one future to complete
                done, not_done = wait(futures, return_when=FIRST_COMPLETED)
                
                for future in done:
                    futures.remove(future)
                    new_urls = future.result()

                    for link in new_urls:
                        clean_link = self.sanitize(link)
                        
                        # Atomic Check + Add
                        with self.visited_lock:
                            if self.is_valid(clean_link) and clean_link not in self.visited:
                                self.visited.add(clean_link)
                                # Submit new task immediately
                                new_future = executor.submit(self.process_url, clean_link)
                                futures.add(new_future)

    def process_url(self, url):
        # Flattened logic: Fetch -> Parse -> Return Links
        return self.fetch_mock(url)

    def fetch_mock(self, url):
        time.sleep(0.01) # Simulate network I/O
        # Mock logic: return logical children based on depth or pattern
        if len(url) > 50: return [] # Stop recursion at some depth
        return [f"{url}/a", f"{url}/b#frag"]

# --- Test Suite ---
import unittest

class TestWebCrawler(unittest.TestCase):
    def test_sanitize(self):
        crawler = WebCrawler("http://example.com")
        self.assertEqual(crawler.sanitize("http://example.com/page#section"), "http://example.com/page")
        self.assertEqual(crawler.sanitize("http://example.com/page"), "http://example.com/page")

    def test_is_valid(self):
        crawler = WebCrawler("http://example.com")
        self.assertTrue(crawler.is_valid("http://example.com/foo"))
        self.assertFalse(crawler.is_valid("http://google.com/foo")) # External domain
        self.assertFalse(crawler.is_valid("ftp://example.com/foo")) # Invalid scheme

    def test_crawl_multithreaded_execution(self):
        """
        Verify that the multithreaded crawler actually runs and populates 'visited'.
        """
        start_url = "http://example.com"
        crawler = WebCrawler(start_url)
        crawler.max_threads = 2
        
        # Override fetch_mock to be deterministic and finite for testing
        def mock_fetch(url):
            if url == start_url:
                return ["http://example.com/1", "http://example.com/2"]
            if url == "http://example.com/1":
                return ["http://example.com/3#fragment"]
            return []
            
        # Monkey patch the fetch method on the instance
        crawler.fetch_mock = mock_fetch
        
        crawler.crawl_multithreaded()
        
        expected = {
            "http://example.com",
            "http://example.com/1",
            "http://example.com/2",
            "http://example.com/3" # Fragment removed
        }
        self.assertEqual(crawler.visited, expected)

if __name__ == "__main__":
    unittest.main()
