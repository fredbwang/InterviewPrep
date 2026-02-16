import os
import json
import pickle

class InMemoryCacheFlawed:
    """
    Simulated flawed implementation from the interview.
    Bug Likely: Cannot hash mutable types (list, dict).
    """
    def __init__(self):
        self.store = {}

    def get_cache_key(self, func_name, args, kwargs):
        # Flawed: Converting directly to string might rely on order
        # Or trying to hash mutable list/dict will crash
        # return str(args) + str(kwargs)  # Unstable if order changes
        # return hash((args, kwargs))     # Crash if args contain list
        pass
        
class DurableCache:
    def __init__(self, filename="cache_wal.jsonl"):
        self.filename = filename
        self.store = {}
        self._recover()

    def _recover(self):
        """Replay the Write-Ahead Log to restore state."""
        if not os.path.exists(self.filename):
            print("No existing cache data found.")
            return

        print(f"Recovering from {self.filename}...")
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    entry = json.loads(line)
                    # {type: "set", key: "...", value: "..."}
                    if entry['op'] == 'set':
                        self.store[entry['key']] = entry['value']
                    elif entry['op'] == 'delete':
                        if entry['key'] in self.store:
                            del self.store[entry['key']]
            print(f"Restored {len(self.store)} items.")
        except Exception as e:
            print(f"Recovery failed: {e}")

    def _append_to_log(self, op: str, key: str, value=None):
        """Append operation to log file (Naive durability)."""
        entry = {'op': op, 'key': key, 'value': value}
        with open(self.filename, 'a') as f:
            f.write(json.dumps(entry) + "\n")
            f.flush()  # Ensure it hits disk immediately if critical
            os.fsync(f.fileno()) # Force flush to disk hardware

    def get(self, key):
        return self.store.get(key)
    
    def set(self, key, value):
        self.store[key] = value
        self._append_to_log('set', key, value)
    
    def delete(self, key):
        if key in self.store:
            del self.store[key]
            self._append_to_log('delete', key)

    # --- Helper for generating keys from function args ---
    @staticmethod
    def make_key(func_name, args, kwargs):
        """
        Robust key generation handling unhashable types and kwargs order.
        """
        # Convert args to list of immutable representations
        key_args = []
        for arg in args:
            if isinstance(arg, list):
                key_args.append(tuple(arg))
            elif isinstance(arg, dict):
                key_args.append(tuple(sorted(arg.items())))
            else:
                key_args.append(arg)
        
        # Sort kwargs items to ensure stability: f(a=1, b=2) == f(b=2, a=1)
        key_kwargs = tuple(sorted(kwargs.items()))
        
        # Serialize to use as cache key (string or hash of tuple)
        # Using string is safer for debugging, hash for speed.
        return f"{func_name}:{tuple(key_args)}:{key_kwargs}"

# Test
if __name__ == "__main__":
    cache = DurableCache("test_cache.db")
    
    # 1. Key Generation Test
    k1 = DurableCache.make_key("foo", [1, [2, 3]], {'b': 2, 'a': 1})
    k2 = DurableCache.make_key("foo", [1, [2, 3]], {'a': 1, 'b': 2})
    print(f"Key Stability Test: {k1 == k2}") # Should be True
    
    # 2. Persistence Test
    cache.set(k1, "Cached Result")
    print(f"Set value: {cache.get(k1)}")
    
    # Simulate restart by creating new instance
    cache2 = DurableCache("test_cache.db")
    print(f"Recovered value: {cache2.get(k1)}")
    
    # Cleanup
    try: os.remove("test_cache.db") 
    except: pass
