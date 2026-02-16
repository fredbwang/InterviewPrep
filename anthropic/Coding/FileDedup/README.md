# File De-duplication

**Sources:**
- [1point3acres (1165014)](https://www.1point3acres.com/bbs/thread-1165014-1-1.html)
- [1point3acres (1144078)](https://www.1point3acres.com/bbs/thread-1144078-1-1.html)

### Problem Description
Given a directory, find all duplicate files.
This question tests your ability to optimize file I/O and handle system design considerations for large-scale data.
**Environment:** Google Colab.

### Part 1: Algorithmic Optimization (The "Funnel" Approach)
The goal is to avoid reading full file content whenever possible, as I/O is slow.

1.  **Stage 1: File Size Check**
    - `os.path.getsize(path)`.
    - If sizes differ, files are definitely different.
    - Group files by size.
2.  **Stage 2: Partial Hash (First 1KB)**
    - Read only the first 1024 bytes.
    - Hash this chunk.
    - If partial hashes differ, files are different.
3.  **Stage 3: Full Hash (Last Resort)**
    - Only for files with matching size AND matching partial hash.
    - Read the rest of the file and compute full SHA-256.

**Complexity Discussion:**
- *Best Case:* All files have unique sizes -> O(N) stat calls.
- *Worst Case:* All files are identical (or copies). You must read every byte of every file. Time complexity is proportional to Total Size of all files.
- *Hash Collisions:* No hash is perfect. For true safety, you might need byte-by-byte comparison if hashes match (paranoia mode), but usually SHA-256 is accepted as unique.

### Part 2: System Design Follow-ups

#### 1. CPU vs I/O Bound?
- **Question:** How do you tell if your program is CPU or I/O bound?
- **Answer:** Look at CPU usage metrics (e.g., `top` or profiler).
    - **I/O Bound:** CPU is idle (waiting for disk/network). Low CPU usage.
    - **CPU Bound:** CPU is pinned at 100% (hashing logic dominating).
- *Optimization:*
    - If I/O bound -> Use Threading or AsyncIO.
    - If CPU bound -> Use Multiprocessing to utilize all cores.

#### 2. Continuous Monitoring System
**Scenario:** Design a system to monitor a drive and notify owners when they add a duplicate.
- **Components:**
    - **File Watcher:** Listens to file system events (e.g., `inotify` on Linux, `FSEvents` on macOS).
    - **Database:** Needs two tables/mappings.
        - `Map<Hash, List<FilePath>>`: To quickly find duplicates.
        - `Map<FilePath, Hash>`: To handle deletions (if file X is deleted, remove its hash from the first map).
- **Workflow:**
    - New File Event -> Calc Hash -> Check DB -> If exists, Notify Owner.
    - Delete File Event -> Lookup Hash -> Remove from DB.

#### 3. Scaling (MapReduce)
For massive datasets (Petabytes):
- **Map:** Input `(FilePath, Metadata)`. Emit `(FileSize, FilePath)`.
- **Reduce:** Group by Size. If list > 1, emit `(FileSize, List<FilePath>)`.
- **Map 2:** Input `(List<FilePath>)`. Read 1KB of each, emit `(PartialHash, FilePath)`.
- **Reduce 2:** Group by PartialHash. If list > 1, emit `(PartialHash, List<FilePath>)`.
- **Map 3:** Input `(List<FilePath>)`. Read Full Content, emit `(FullHash, FilePath)`.
