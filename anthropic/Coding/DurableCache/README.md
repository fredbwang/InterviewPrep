# Durable In-Memory Cache (LRU Extension)

**Sources:**
- [1point3acres (1148690)](https://www.1point3acres.com/bbs/thread-1148690-1-1.html)
- [1point3acres (1152730)](https://www.1point3acres.com/bbs/thread-1152730-1-1.html)
- [1point3acres (1143852)](https://www.1point3acres.com/bbs/thread-1143852-1-1.html)

### Problem Description
**Classification:** Coding Q2 (Template-based) / Coding Q6 (Runtime Extension)

**Note:** This is confirmed to be the "new" Q2, replacing "FileDedup".

You are provided with a template containing an implementation of an In-Memory Cache (likely a simple dictionary or an LRU Cache).

**Task:**
1.  **Debug/Fix:** Find a bug in the cache key generation logic.
    - *Context:* The cache uses a `make_key(*args, **kwargs)` function.
    - *Bug:* It likely fails on mutable types (lists/dicts) or is sensitive to `kwargs` order.
    - *Solution:* Convert mutables to immutable types (tuple of tuples), sort kwargs.
2.  **Extend:** Make the cache **Durable** (persist across restarts).
    - Requirement: "If the cache crashes/restarts, data must be recovered without loss."

### Part 1: Key Generation Bug
Common pitfalls when caching function calls (`@lru_cache` style):
- **Unhashable Arguments:** `args` containing `list` or `dict`.
- **Order Sensitivity:** `kwargs` order shouldn't matter. `f(a=1, b=2)` should equal `f(b=2, a=1)`.
- **Solution:**
    - Convert `list` -> `tuple`.
    - Convert `dict` (`kwargs`) -> `frozenset` of items or sorted tuple.
    - JSON serialization (stable sort) strings.

### Part 2: Persistence (Durability)
**Implementation Options:**
1.  **Write-Ahead Log (WAL):** Capture every `set` operation to a file *before* updating memory. On startup, replay the log.
    - *Pros:* Fast write, robust.
    - *Cons:* Start-up time grows with log size (need compaction).
2.  **Snapshotting:** Periodically dump the entire `dict` to a JSON/Pickle file.
    - *Pros:* Simple.
    - *Cons:* Data loss window between snapshots. "Must ensure no data loss" implies WAL or synchronous write.
3.  **Synchronous Write (AOF - Append Only File):**
    - Every `set(key, val)` appends a line to `cache.log`.
    - On `__init__`, read `cache.log` line-by-line to repopulate `self.store`.

**Code Structure:**
```python
class DurableCache:
    def __init__(self, filename="cache.db"):
        self.filename = filename
        self.store = {}
        self._recover()

    def _recover(self):
        # Read from disk
        pass
```
