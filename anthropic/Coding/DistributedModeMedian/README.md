# Distributed Mode & Median (Coding Q4)

**Sources:**
- [1point3acres (1132204)](https://www.1point3acres.com/bbs/thread-1132204-1-1.html)
- [1point3acres (1139508)](https://www.1point3acres.com/bbs/thread-1139508-1-1.html)
- [1point3acres (1102889)](https://www.1point3acres.com/bbs/thread-1102889-1-1.html)
- [1point3acres (1135727)](https://www.1point3acres.com/bbs/thread-1135727-1-1.html)

### Problem Description
This is a **Coding Q4** problem focusing on **Distributed Systems**.
You are simulated as one of `N` workers in a cluster.
Your goal is to find global statistics (Mode, Median) efficiently.

**Key Constraints (New):**
1.  **Single Data Source:** All workers might read from the *same* static dataset (file/blob) but are assigned different **indices** (shards).
2.  **Bandwidth Latency:** The cost of `send/recv` is proportional to data size.
3.  **No Multi-threading:** It is a distributed simulation, not local threading.

### Part 1: Find Mode (MapReduce)
**Goal:** Find the most frequent element.
**Constraint:** Keys are scattered. One worker cannot hold all data in memory if not aggregated.

**Algorithm:**
1.  **Read & Local Count:** Read assigned chunk. Count frequencies locally.
2.  **Shuffle (Map):**
    - `target_id = hash(key) % num_workers`.
    - Send `(key, count)` to `target_id`.
    - *Crucial Optimization:* Send **aggregated** counts, not raw values.
3.  **Aggregate (Reduce):**
    - Receive counts. Sum them up per key.
    - Find local max `(key, total_count)`.
4.  **Gather:**
    - Send local max to Leader (Worker 0).
    - Leader finds global max.

### Part 2: Find Median (Distributed QuickSelect)
**Goal:** Find the median element.

**Algorithm:**
1.  **Pivot Selection:** Leader picks a random pivot `P` from its local data and broadcasts it.
    - *Optimization:* Use "Median of Medians" of local samples for a better pivot.
2.  **Local Partitioning:**
    - Each worker counts elements:
        - `L`: Count < P
        - `E`: Count == P
        - `G`: Count > P
    - Send `(L, E, G)` to Leader.
3.  **Global Decision:**
    - Leader sums `total_L`, `total_E`, `total_G`.
    - If `k < total_L`: Median is in Left. Broadcast "Recurse Left".
    - If `k < total_L + total_E`: Median is `P`. Done.
    - Else: Median is in Right. Broadcast "Recurse Right" (work on `k - total_L - total_E`).

### Performance Model (Roofline)
**Hint from HM Round:** Be aware of the **Roofline Model**.
- **Compute Bound:** Are you limited by CPU speed (e.g., hashing, counting)?
- **Memory/Bandwidth Bound:** Are you limited by Network or RAM speed (e.g., shuffling raw data)?
- *Application:* In this problem, naive shuffling (sending every int) hits the Bandwidth ceiling. Aggregating before sending moves you towards Compute efficiency.

### Testing Strategy
**Question:** How to verify correctness in a distributed simulation?
1.  **Mock Environment:** The interviewer provides a mock `WorkerEnv` (like in `solution_mode.py`).
2.  **Synchronization:**
    - Ensure all `send`s are complete before `recv`.
    - In the simulation, this might be implicitly handled or requires a `barrier()` call if provided.
    - If no barrier, Workers might need to send a "DONE" signal to the target for every phase.
