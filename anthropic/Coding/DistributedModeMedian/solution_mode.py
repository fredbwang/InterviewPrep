from collections import defaultdict
import random
import threading
from typing import List, Dict, Any, Tuple

# --- Simulation Environment ---
class WorkerEnv:
    def __init__(self, worker_id: int, num_workers: int, bus: Dict[int, List[Any]], barrier: threading.Barrier):
        self._worker_id = worker_id
        self._num_workers = num_workers
        self._bus = bus
        self._barrier = barrier
    
    @property
    def worker_id(self): return self._worker_id
    
    @property
    def num_workers(self): return self._num_workers
    
    def recv(self) -> List[Any]:
        # Fetch messages intended for this worker
        # We look into the shared bus for our worker_id
        msgs = self._bus[self._worker_id][:]
        self._bus[self._worker_id].clear() # Consume
        return msgs
    
    def send(self, target_id: int, data: Any):
        # Direct write to shared memory bus
        self._bus[target_id].append(data)

    def sync(self):
        # Wait for all workers to reach this point
        self._barrier.wait()

# --- Solution: Mode (Most Frequent Element) ---

def find_mode_distributed(local_data: List[int], env: WorkerEnv) -> Tuple[int, int]:
    """
    Find the global mode using MapReduce pattern.
    Returns: (mode_value, global_count)
    """
    # 1. Local Count Map
    local_counts = defaultdict(int)
    for x in local_data:
        local_counts[x] += 1
    
    # 2. Shuffle / Partition (Map Phase)
    # Target worker for a key is hash(key) % num_workers
    for key, count in local_counts.items():
        target_worker = hash(key) % env.num_workers
        env.send(target_worker, {"type": "partial_count", "key": key, "count": count})
    
    # --- Synchronization Barrier ---
    env.sync()
    
    # 3. Aggregate (Reduce Phase)
    # Receive all partial counts assigned to this worker.
    incoming_msgs = env.recv()
    aggregated_counts = defaultdict(int)
    
    for msg in incoming_msgs:
        if msg.get("type") == "partial_count":
            k = msg["key"]
            c = msg["count"]
            aggregated_counts[k] += c
            
    # Find local maximum among keys assigned to this worker
    local_best_key = None
    local_best_count = -1
    
    for k, c in aggregated_counts.items():
        if c > local_best_count:
            local_best_count = c
            local_best_key = k
            
    # 4. Global Maximum (Gather Phase)
    # Send local best to Leader (Worker 0)
    leader_id = 0
    env.send(leader_id, {"type": "candidate_mode", "key": local_best_key, "count": local_best_count})
    
    # --- Synchronization Barrier ---
    env.sync()
    
    # 5. Leader Decides
    if env.worker_id == leader_id:
        msgs = env.recv()
        global_best_key = None
        global_best_count = -1
        
        for msg in msgs:
            if msg.get("type") == "candidate_mode":
                k = msg["key"]
                c = msg["count"]
                if c > global_best_count:
                    global_best_count = c
                    global_best_key = k
        
        return global_best_key, global_best_count
    else:
        return None, None # Workers wait for result

# --- Solution: Median (Distributed QuickSelect Concept) ---

def find_median_distributed(local_data: List[int], total_elements: int, env: WorkerEnv):
    """
    Find median using iterative pivot selection.
    Assumes Leader coordinates rounds.
    """
    # Range of candidate values or indices being searched
    # Concept: Leader picks pivot P.
    # Workers count: <P, =P, >P
    # Leader sums counts.
    # If total_less > N/2: Median is < P. Recurse on left.
    # If total_less + total_equal > N/2: Median is P.
    # Else: Median is > P. Recurse on right.
    pass

if __name__ == "__main__":
    NUM_WORKERS = 4
    # Generate some distributed data
    # Mode should be 42
    all_data = [42]*50 + [1]*20 + [2]*20 + [3]*5 + [42]*10
    random.shuffle(all_data)
    
    # Split among workers
    chunk_size = len(all_data) // NUM_WORKERS
    worker_data = []
    for i in range(NUM_WORKERS):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < NUM_WORKERS - 1 else len(all_data)
        worker_data.append(all_data[start:end])
        
    print(f"Total items: {len(all_data)}")
    print("Running distributed mode calculation...")
    
    # Bus and Barrier
    bus: Dict[int, List[Any]] = {i: [] for i in range(NUM_WORKERS)}
    barrier = threading.Barrier(NUM_WORKERS)
    
    results = [None] * NUM_WORKERS
    
    def worker_task(wid):
        env = WorkerEnv(wid, NUM_WORKERS, bus, barrier)
        res = find_mode_distributed(worker_data[wid], env)
        results[wid] = res
        
    threads = []
    for i in range(NUM_WORKERS):
        t = threading.Thread(target=worker_task, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    leader_res = results[0]
    print(f"Leader Result: Key={leader_res[0]}, Count={leader_res[1]}")
    
    # Verification
    from collections import Counter
    real_counts = Counter(all_data)
    real_mode = real_counts.most_common(1)[0]
    print(f"Actual Mode: Key={real_mode[0]}, Count={real_mode[1]}")
    
    assert leader_res[0] == real_mode[0]
    assert leader_res[1] == real_mode[1]
    print("SUCCESS: Distributed mode matches actual mode.")
