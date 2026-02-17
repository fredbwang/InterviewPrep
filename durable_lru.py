
import json
import os
import shutil
from collections import OrderedDict

# Define the cache filename
LOG_FILE = "persistent_cache.jsonl"
SNAPSHOT_FILE = "persistent_cache.snap"

class PersistentLRUCache:
    def __init__(self, capacity: int, filename: str = LOG_FILE):
        self.capacity = capacity
        self.filename = filename
        self.cache = OrderedDict()
        self._load_from_disk()

    # --- 1. Recovery Logic ---
    def _load_from_disk(self):
        """Reads the append-only log line by line to rebuild the cache state."""
        if not os.path.exists(self.filename):
            return

        try:
            with open(self.filename, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        op = record.get("op")
                        key = record.get("key")
                        value = record.get("value")

                        if op == "PUT":
                            if key in self.cache:
                                self.cache.move_to_end(key)
                            self.cache[key] = value
                            if len(self.cache) > self.capacity:
                                self.cache.popitem(last=False)
                        
                        elif op == "GET":
                            if key in self.cache:
                                self.cache.move_to_end(key)
                                
                        elif op == "DEL":
                            if key in self.cache:
                                del self.cache[key]

                    except json.JSONDecodeError:
                        continue # Skip corrupted lines
        except Exception as e:
            print(f"Error recovering cache: {e}")

    # --- 2. Write Logic (Append-Only Log) ---
    def _log(self, op, key, value=None):
        """Appends an operation to the log file immediately."""
        entry = {"op": op, "key": key}
        if value is not None:
            entry["value"] = value
        
        try:
            with open(self.filename, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except IOError as e:
            print(f"Write failed: {e}")

    # --- Public API ---
    def get(self, key):
        if key not in self.cache:
            return -1
        
        self.cache.move_to_end(key)
        # Writes to disk to persist the "access" event (so LRU order survives crash)
        self._log("GET", key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        
        self.cache[key] = value
        self._log("PUT", key, value)
        
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

    def compact(self):
        """Maintenance: Rewrite the log to only include current active items."""
        # Create a new temp file, write current state as PUTs
        temp_file = self.filename + ".tmp"
        with open(temp_file, "w") as f:
            for key, value in self.cache.items():
                # Write in LRU order (oldest first) so replay builds correct order
                f.write(json.dumps({"op": "PUT", "key": key, "value": value}) + "\n")
        
        # Atomic replace
        shutil.move(temp_file, self.filename)
        print("Log compacted.")

# --- Demo & Test ---
if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    print("=== Phase 1: Operations ===")
    cache = PersistentLRUCache(3)
    cache.put("A", 1)
    cache.put("B", 2)
    cache.put("C", 3)
    print(f"State: {list(cache.cache.keys())}") # ['A', 'B', 'C']

    cache.get("A") # Access A -> Moves to end
    print(f"Accessed A: {list(cache.cache.keys())}") # ['B', 'C', 'A']

    cache.put("D", 4) # Evicts B (LRU)
    print(f"Added D: {list(cache.cache.keys())}") # ['C', 'A', 'D']

    print("\n=== Phase 2: Crash Simulation ===")
    # Re-instantiate from file
    del cache
    new_cache = PersistentLRUCache(3)
    print(f"Recovered State: {list(new_cache.cache.keys())}")
    
    # Assert correctness
    assert list(new_cache.cache.keys()) == ['C', 'A', 'D']
    assert new_cache.get("B") == -1
    print("Recovery Successful!")

    print("\n=== Phase 3: Compaction ===")
    old_size = os.path.getsize(LOG_FILE)
    print(f"Log size before compaction: {old_size} bytes")
    new_cache.compact()
    new_size = os.path.getsize(LOG_FILE)
    print(f"Log size after compaction: {new_size} bytes")
