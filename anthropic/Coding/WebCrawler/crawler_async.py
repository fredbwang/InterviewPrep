import httpx
import asyncio
import os
import tempfile
import time
from crawler import get_links  # Reuse the get_links function for consistency
from urllib.parse import urlparse

HEADERS = {
    'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'
}

async def download_page_async(client, link, temp_dir):
    print(f"[Task START] {link}")
    try:
        # Generate filename from URL
        filename = link.split("/")[-1] + ".html"
        filepath = os.path.join(temp_dir, filename)
        
        # print(f"Downloading {link}...")
        response = await client.get(link, headers=HEADERS)
        content = response.content
        
        # File I/O is blocking, but for small files it's often negligible.
        # Ideally use aiofiles for true async file I/O, but standard open() is fine for this comparison.
        with open(filepath, "wb") as f:
            f.write(content)
        print(f"[Task WRITE FINISH] {link}")
    except Exception as e:
        print(f"Error processing {link}: {e}")
    print(f"[Task FINISH] {link}")

async def main():
    links = get_links()
    # Use the same subset as the threaded version
    target_links = links[:10]
    
    temp_dir = os.path.join(tempfile.gettempdir(), 'crawled_pages_async')
    os.makedirs(temp_dir, exist_ok=True)
    print(f"Saving pages to: {temp_dir}")
    
    start_time = time.time()
    
    # Create a single session and reuse it
    async with httpx.AsyncClient() as client:
        tasks = []
        for link in target_links:
            task = download_page_async(client, link, temp_dir)
            tasks.append(task)
        
        # Run all downloads concurrently
        # Note: We are not explicitly limiting concurrency here like max_workers=10
        # If we wanted to limit concurrency, we would use asyncio.Semaphore
        print(f"[Main] Firing tasks and waiting...")
        await asyncio.gather(*tasks)
        print(f"[Main] asyncio.gather finished. Control returned to main.")
            
    duration = time.time() - start_time
    print(f"Downloaded {len(target_links)} links in {duration} seconds")
    print(f"[Main] Execution stopped.")

if __name__ == "__main__":
    # Windows-specific fix for asyncio selector event loop policy if needed, 
    # but usually fine on modern Python versions.
    asyncio.run(main())
