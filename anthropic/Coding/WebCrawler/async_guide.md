
# Python Asyncio & Aiohttp Guide

## Core Concept: The Event Loop
Think of the Event Loop as a single worker in a restaurant. Instead of hiring 10 waiters (threads) for 10 tables, you have **one super-fast waiter** (the Event Loop).
- When Table 1 orders (starts an HTTP request), the waiter doesn't stand there waiting for the food.
- They immediately go to Table 2, Table 3, etc.
- When the food (response) is ready for Table 1, the kitchen rings a bell (callback), and the waiter serves it.
**Result:** 1 waiter handles thousands of tables because they never sit idle waiting.

---

## 1. `asyncio` (The Engine)
The standard library that provides the Event Loop and tools to run async functions.

### Key Keywords:
- **`async def`**: Defines a coroutine (a function that can be paused).
  ```python
  async def my_task():
      return "Hello"
  ```
- **`await`**: Pauses the current function until the awaited task is done. The Event Loop uses this free time to work on other tasks.
  ```python
  result = await my_task()  # Pause here until my_task finishes
  ```

### Essential Helper Functions:

#### `asyncio.run(coro)`
- **The Starter.** Sets up the Event Loop, runs your main function, and closes everything down when done.
- *Use case:* The entry point of your script.
  ```python
  if __name__ == "__main__":
      asyncio.run(main())
  ```

#### `asyncio.gather(*tasks)`
- **The Bundler.** Runs multiple tasks concurrently and waits for ALL of them to finish.
- *Use case:* Downloading 50 URLs at once.
- *Returns:* A list of results in the same order as the inputs.
  ```python
  urls = ["url1", "url2", "url3"]
  tasks = [download(u) for u in urls]
  results = await asyncio.gather(*tasks) 
  # results = [data1, data2, data3]
  ```

#### `asyncio.create_task(coro)`
- **The Fire-and-Forget (Sort of).** Schedules a coroutine to run on the loop immediately.
- *Use case:* You want to start a background task but keep doing other work in the current function.
  ```python
  task = asyncio.create_task(background_job())
  # code continues immediately
  await task  # wait for it later
  ```

#### `asyncio.sleep(seconds)`
- **Non-blocking Sleep.** Pauses the current task but **lets the Event Loop run other tasks** during the wait.
- *Crucial difference:* `time.sleep(1)` blocks the *entire* program (stops everything). `await asyncio.sleep(1)` just pauses *this* specific task.

---

## 2. `aiohttp` (The Async Browser)
`requests` is synchronous (blocking). If you use `requests` inside an `async def`, you block the entire Event Loop! `aiohttp` is the non-blocking equivalent.

### Client Structure:

#### `aiohttp.ClientSession()`
- Like a browser window. It holds connection pools and cookies.
- **Best Practice:** Create ONE session and reuse it for all requests (don't create a new session for every URL).
  ```python
  async with aiohttp.ClientSession() as session:
      # use session here
  ```

#### `session.get(url)` / `session.post(url)`
- Starts the HTTP request.
- Must use `async with` to handle the connection context.
  ```python
  async with session.get(url) as response:
      # Reading the body is also async!
      html = await response.text()      # For string content
      data = await response.read()      # For binary content (images, etc)
      json_data = await response.json() # For JSON APIs
  ```

---

## 3. Other Popular Async Libraries

### `aiofiles`
- **Async File I/O.** Standard `open()` is blocking. For small files, it doesn't matter much. For large file operations (reading 1GB logs), `open()` stops the Event Loop. `aiofiles` fixes this.
  ```python
  async with aiofiles.open('filename', mode='r') as f:
      contents = await f.read()
  ```

### `asyncpg` / `aiomysql`
- **Async Databases.** Connect to PostgreSQL/MySQL non-blockingly. Highly optimized for performance.

### `FastAPI`
- **Async Web Framework.** Modern replacement for Flask/Django. Built on top of asyncio/Starlette.
  ```python
  @app.get("/")
  async def read_root():
      return {"Hello": "World"}
  ```

---

## Common Pitfalls
1. **Using blocking code:** `time.sleep(5)` or `requests.get()` inside an async function freezes the *entire* loop.
2. **Forgetting `await`:** Calling `my_coroutine()` without `await` just creates a coroutine object but never runs it.
3. **Too many tasks:** `asyncio.gather(*10000_tasks)` might crash your system or get you banned by a server. Use `asyncio.Semaphore` to limit concurrency.
