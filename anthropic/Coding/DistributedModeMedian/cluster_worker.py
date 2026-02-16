import threading
from collections import defaultdict, Counter

class Worker:
    def __init__(self, workerId, k, localData, cluster):
        self.workerId = workerId
        self.k = k
        self.localData = localData
        self.cluster = cluster
        self.final_result = None # To store result if this worker is the leader

    # Sends a payload data to the specified worker asynchronously.
    def sendAsyncMessage(self, targetWorkerId, payload):
        self.cluster.sendAsyncMessage(targetWorkerId, payload)

    # Receives a payload data from the worker's mailbox.
    def receive(self):
        return self.cluster.receive(self.workerId)
    
    def run(self):
        # 1. Local Frequency Count (Map Phase)
        local_counts = Counter(self.localData)
        
        # 2. Shuffle / Distribute
        # Send partial counts to the designated worker based on hash
        for key, count in local_counts.items():
            target_id = hash(key) % self.k
            self.sendAsyncMessage(target_id, (key, count))
            
        # 3. Synchronization (Wait for all workers to finish sending)
        self.cluster.sync()
        
        # Start Timing
        import time
        t0 = time.time()
        
        # 4. Aggregate Received Counts (Reduce Phase)
        # Read from mailbox until empty (all shuffle data is in)
        aggregated_counts = defaultdict(int)
        while True:
            msg = self.receive()
            if msg == "": 
                break
            if isinstance(msg, tuple):
                k, c = msg
                aggregated_counts[k] += c
        
        t1 = time.time()
                
        # 5. Find Local Candidate (Sub-result)
        # Find the key with the highest count assigned to this worker
        best_key = None
        best_count = -1
        
        for k, v in aggregated_counts.items():
            if v > best_count:
                best_count = v
                best_key = k
            elif v == best_count:
                if best_key is None or k < best_key:
                    best_key = k
        
        t2 = time.time()
        
        self.freq_agg_time = t1 - t0
        self.find_local_mode_time = t2 - t1
        
        # 6. Gather Phase: Send local candidate to Leader (Worker 0)
        # We use a special tuple wrapper or check logic to distinguish if needed,
        # but here we rely on the barrier to separate phases, so buffer should be clean.
        
        # Barrier before sending candidates to ensure Leader finished processing Reduce messages
        # (Though Leader just drained its mailbox in step 4, so it's empty)
        self.cluster.sync()
        
        if best_count > 0:
            self.sendAsyncMessage(0, ("CANDIDATE", best_key, best_count))
            
        # Barrier to ensure Leader has received all candidates
        self.cluster.sync()
        
        # 7. Consensus / Leader Aggregation (Worker 0 only)
        if self.workerId == 0:
            global_mode = None
            global_count = -1
            
            # Process remaining messages (Candidates)
            while True:
                msg = self.receive()
                if msg == "": 
                    break
                if isinstance(msg, tuple) and msg[0] == "CANDIDATE":
                    _, k, c = msg
                    if c > global_count:
                        global_count = c
                        global_mode = k
                    elif c == global_count:
                        if global_mode is None or k < global_mode:
                            global_mode = k
            
            self.final_result = global_mode

class Cluster:
    def __init__(self, data, k):
        self.k = k

        self.shards = []
        for i in range(k):
            self.shards.append([])

        # Distribute data evenly across workers
        totalSize = len(data)
        if k > 0:
            baseSize = totalSize // k
            remainder = totalSize % k
            
            index = 0
            for w in range(k):
                chunkSize = baseSize + (1 if w < remainder else 0)
                for j in range(chunkSize):
                    if index < totalSize:
                        self.shards[w].append(data[index])
                        index += 1

        self.mailboxes = {i: [] for i in range(k)}
        self.readIndices = {i: 0 for i in range(k)}
        
        # Internal primitives for simulation
        self.barrier = threading.Barrier(k)
        
        self.workers = [Worker(i, k, self.shards[i], self) for i in range(k)]

    def sendAsyncMessage(self, targetWorkerId, payload):
        # Simulating async send (append to target mailbox)
        self.mailboxes[targetWorkerId].append(payload)

    def receive(self, workerId):
        myMailbox = self.mailboxes[workerId]
        idx = self.readIndices[workerId]
        if idx < len(myMailbox):
            self.readIndices[workerId] = idx + 1
            return myMailbox[idx]
        return ""
        
    def sync(self):
        self.barrier.wait()
        
    def findMode(self):
        # Start Worker Threads
        threads = []
        for w in self.workers:
            t = threading.Thread(target=w.run)
            threads.append(t)
            t.start()
            
        # Wait for all workers to complete
        for t in threads:
            t.join()
            
        # Retrieve result from Leader (Worker 0)
        return self.workers[0].final_result

    @staticmethod
    def main():
        Cluster.test1()
        Cluster.test2()
        Cluster.test3()
        Cluster.test4()

    @staticmethod
    def test1():
        print("===== Test 1 =====")
        data = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
        cluster = Cluster(data, 3)
        print(f"Result: {cluster.findMode()}")  # Expected: 4

    @staticmethod
    def test2():
        print("===== Test 2 =====")
        data = [1, 2, 3, 1, 2, 3]
        cluster = Cluster(data, 2)
        print(f"Result: {cluster.findMode()}")  # Expected: 1

    @staticmethod
    def test3():
        print("===== Test 3 =====")
        data = []
        for i in range(100):
            data.append(7)
        for i in range(50):
            data.append(3)
        for i in range(30):
            data.append(11)
        for i in range(20):
            data.append(5)
        cluster = Cluster(data, 10)
        print(f"Result: {cluster.findMode()}")  # Expected: 7

    @staticmethod
    def test4():
        print("===== Test 4 (Large Scale + Timing) =====")
        import random
        # 100 nodes, 100k items, 10k distinct values
        k = 100
        num_items = 1000000
        num_distinct = 100000
        expected_mode = 4201
        
        data = []
        for _ in range(num_items):
            data.append(random.randint(0, num_distinct - 1))
        for _ in range(500):
            data.append(expected_mode)
        random.shuffle(data)
        
        print(f"Running with {len(data)} items and {k} workers...")
        cluster = Cluster(data, k)
        result = cluster.findMode()
        print(f"Result: {result}")
        
        if result == expected_mode:
            print("SUCCESS: Large scale test passed.")
        else:
            print(f"FAILURE: Expected {expected_mode}, got {result}")
            
        # Helper to print stats and histogram
        def print_metrics(name, times):
            min_t = min(times)
            max_t = max(times)
            avg_t = sum(times) / len(times)
            
            print(f"\nTiming Stats: {name}")
            print(f"Min: {min_t*1000:.4f} ms")
            print(f"Max: {max_t*1000:.4f} ms")
            print(f"Avg: {avg_t*1000:.4f} ms")
            
            # Text-based Histogram
            print(f"Time Distribution ({name}):")
            buckets = 10
            if max_t == min_t:
                 bucket_size = 0.0001
            else:
                 bucket_size = (max_t - min_t) / buckets
                 
            bucket_counts = [0] * buckets
            for t in times:
                if bucket_size == 0:
                    idx = 0
                else:
                    idx = int((t - min_t) / bucket_size)
                    if idx >= buckets: idx = buckets - 1
                bucket_counts[idx] += 1
                
            for i in range(buckets):
                range_start = min_t + (i * bucket_size)
                range_end = min_t + ((i + 1) * bucket_size)
                count = bucket_counts[i]
                bar = "#" * count
                print(f"{range_start*1000:6.3f}ms - {range_end*1000:6.3f}ms | {bar} ({count})")

        agg_times = [w.freq_agg_time for w in cluster.workers]
        mode_times = [w.find_local_mode_time for w in cluster.workers]
        
        print_metrics("Freq Aggregation", agg_times)
        print_metrics("Find Local Mode", mode_times)


if __name__ == "__main__":
    Cluster.main()