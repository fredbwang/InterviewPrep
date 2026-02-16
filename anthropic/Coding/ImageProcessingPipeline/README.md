# Image Processing Pipeline (Concurrency / Growth)

**Sources:**
- [1point3acres (1150952)](https://www.1point3acres.com/bbs/thread-1150952-1-1.html)
- [1point3acres (1154439)](https://www.1point3acres.com/bbs/thread-1154439-1-1.html)

### Problem Description
This problem tests your ability to use external libraries (`Pillow`, `scikit-image`), parse data, and **optimize for performance using concurrency**.

**Goal:** Apply a set of transformation pipelines (JSON) to a set of images.

**Input:**
- **Images:** Folders `small_images` and `big_images`.
- **Pipelines:** Dictionary or folder of JSON files.
- **Output:** Folder `out`.

**Transformations (6 Types):**
1.  `grayscale` (No args)
2.  `flip_horizontally` (No args)
3.  `flip_vertically` (No args)
4.  `scale` (Has args)
5.  `blur` (Has args)
6.  `rotate` (Has args)

### Part 1: Sequential Implementation
- Read standard `small_images`.
- Apply transformations using a library like `Pillow`.
- Save to `out` folder.
- **Focus:** API lookup speed (knowing how to use `Image.transpose(Image.FLIP_LEFT_RIGHT)`, `ImageFilter.BLUR`, etc.).

### Part 2: High Performance (Concurrency)
- Process `big_images`.
- **Constraint:** There is a strict time limit. Sequential processing will be too slow.
- **Solution:** Use **Multiprocessing** (`ProcessPoolExecutor`).
    - **Why Process vs Thread?** Image processing is **CPU Bound**. Python's GIL (Global Interpreter Lock) prevents Threads from utilizing multiple CPU cores effectively for CPU tasks. Threads are better for I/O (network requests).
    - **Shared Memory:** Not strictly needed if paths are passed, but be mindful of overhead.

### Follow-up Questions
- **Threads vs Processes:** Explain GIL.
- **Memory Usage:** Loading too many large images into RAM simultaneously? (Batching / Semaphore).
