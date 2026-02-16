# Web Crawler (Distributed / Async)

**Sources:**
- [1point3acres (1160362)](https://www.1point3acres.com/bbs/thread-1160362-1-1.html)
- [1point3acres (1157666)](https://www.1point3acres.com/bbs/thread-1157666-1-1.html)
- [1point3acres (1146090)](https://www.1point3acres.com/bbs/thread-1146090-1-1.html)
- [1point3acres (1131484)](https://www.1point3acres.com/bbs/thread-1131484-1-1.html)

### Problem Description
This question has evolved from a simple BFS crawler to one focused on **Concurrency** and **URL Handling nuance**.

**Core Requirements:**
- **Goal:** Crawl all pages within a single hostname.
- **Handling:** Remove URL fragments (`#section`) before deduplication.
- **Concurrency:** 
    - **Threading:** `ThreadPoolExecutor` (Basic).
    - **Async:** `asyncio` + `aiohttp` (Advanced / Preferred by some interviewers for IO bound tasks).

### Key Pitfalls (From Interview Experiences)
1.  **Sanitization Order:** You must sanitize (remove fragment) **BEFORE** checking `visited`.
    - Incorrect: `if url not in visited: sanitize(url) ...` -> Result: `page` and `page#1` are treated as different.
    - Correct: `clean_url = remove_fragment(url); if clean_url not in visited: ...`
2.  **Concurrency Approach:**
    - **Do NOT** start with manual `Threading` + `Lock` primitives unless asked. It's error-prone and "old school".
    - **DO** use `concurrent.futures.ThreadPoolExecutor` or `asyncio`.
3.  **Async/Await Nuance:**
    - Using `requests` inside `asyncio` blocks the event loop! You MUST use an async library like `aiohttp`.
    - Don't forget `await` keywords (classic failure point).

### Helpful References
- [StackOverflow: AsyncIO vs Threading vs Multiprocessing in Python](https://stackoverflow.com/questions/60451367)
- [StackOverflow: Crawling with ThreadPoolExecutor](https://stackoverflow.com/questions/11254558)
- [Oxylabs Blog: Concurrency vs Parallelism](https://oxylabs.io/blog/concurrency-vs-parallelism)

### Reasoning: Concurrency vs Parallelism (CPU vs I/O Bound)
**Key Concept:**
- **CPU Bound:** Limited by processor speed (e.g., Parsing massive HTML, hashing).
    - `Multiprocessing` is faster because it bypasses the GIL (Global Interpreter Lock), utilizing multiple cores.
    - `Threading` is limited by GIL to one core.
- **I/O Bound:** Limited by Network/Disk (e.g., Fetching URL, waiting for response).
    - `Threading` and `AsyncIO` are comparably fast because the CPU is mostly idle waiting for network. The GIL is released during I/O operations.
    - `AsyncIO` is often preferred for **massive** scaling (10k+ connections) due to lower memory overhead compared to threads.

**Interview Application:**
- **Q:** "How to speed up the crawler?"
- **A:**
    1.  **Start with Threading (`ThreadPoolExecutor`):** It's simpler and sufficient for I/O bound crawling (fetching URLs). It overcomes network latency effectively.
    2.  **Acknowledge the CPU bottleneck:** Parsing HTML (`BeautifulSoup`) is CPU bound. If we heavily parse, threads might hit the GIL limit.
    3.  **Advanced Optimization:** Move parsing logic to a separate `ProcessPoolExecutor` (Multiprocessing) or use `asyncio` for the network part to handle thousands of concurrent requests with minimal overhead.

### Follow-ups (System Design Style)
The specific source (1131484) highlights these System Design follow-ups for Senior roles:
1.  **Politeness Policy:**
    - *Problem:* Crawler is too aggressive.
    - *Solution:* Implement per-domain rate limiting. Use `urllib.robotparser` to respect `robots.txt`. Add a delay (`time.sleep` or async sleep) between requests to the same domain.
2.  **Distributed Crawling:**
    - *Problem:* Seed list is in the millions.
    - *Solution:* Use a Message Queue (Kafka/SQS).
        - **URL Frontier:** Central queue of URLs to visit.
        - **Workers:** Pull URL, fetch, parse, push new links back to Frontier.
        - **Deduplication:** Needs a distributed KV store (Redis/Cassandra) for `visited` set. Apply Bloom Filter for space efficiency.
3.  **Content Deduplication (Mirror Detection):**
    - *Problem:* Many URLs point to same content (e.g., mirrors, query params).
    - *Solution:* Compute **Content Hash** (MD5/SHA) of the HTML body. Store `Hash -> URL` map. If hash exists, skip processing. Use **Locality Sensitive Hashing (LSH)** or **MinHash** to detect near-duplicates.

### Part 1: Single Threaded
- Standard BFS using `deque`.
- `urllib.parse.urlparse` to handle hostname check and fragment removal.

### Part 2: Multi-Threaded (The Expectation)
- Use `ThreadPoolExecutor`.
- **Shared State:** A thread-safe `visited` set (or use a `Lock` around a standard set).

### Part 3: AsyncIO (The Advanced Follow-up)
- Use `aiohttp` for non-blocking HTTP requests.
- Use `BeautifulSoup` (which is blocking/CPU-bound) cautiously. Ideally run it in a thread executor if parsing heavy HTML, but for simple tasks, running it inline is often accepted in interviews or wrapped in `asyncio.to_thread`.
- **Recursion vs Queue:**
    - `await asyncio.gather(*[dfs(u) for u in links])` works but can blow the stack on deep crawls.
    - **Better:** Use `asyncio.Queue` and a fix set of workers.
