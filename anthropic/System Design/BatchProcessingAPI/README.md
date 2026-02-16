# Batch Processing API (System Design)

**Source:** [1point3acres (1147020)](https://www.1point3acres.com/bbs/thread-1147020-1-1.html)

### Problem Description
This is a System Design question focusing on **Infrastructure / Backend**.
**API Signature:**
```cpp
list<string> batch_string(list<string> input)
```
**Core Challenge:** Design an API to combine requests and send them to a backend GPU, where **one GPU can only process one batch at a time**.

**Context:** The interviewer's feedback suggests they are looking for deep understanding of concurrency, queuing, and possibly low-level implementation details, not just high-level "load balancer -> service".

### Key Requirements
1.  **Batching:** Accumulate incoming requests into groups (batches) to maximize GPU throughput.
    - *Constraint:* Latency vs Throughput trade-off. If a batch isn't full, how long do we wait? (Timeouts).
2.  **Concurrency Control:** A GPU handles one batch at a time.
    - Must prevent overloading the GPU.
    - Queuing mechanism close to the worker.
3.  **Routing/Load Balancing:** Distribution across multiple GPU nodes.

### Solution Architecture
1.  **API Gateway / Frontend Node:**
    - Receives `list<string>`.
    - Pushes requests into a **Dynamic Batching Component**.
2.  **Dynamic Batcher (The Core):**
    - Implementing logic similar to **NVIDIA Triton Inference Server** or **vLLM's Continuous Batching**.
    - *Mechanism:*
        - Maintain a thread-safe queue.
        - A "Batcher" thread pulls items until `max_batch_size` OR `max_wait_time` is reached.
        - Dispatches the formulated batch to the GPU worker.
3.  **Worker / GPU:**
    - Executes the model inference.
    - Returns results.
    - **Backpressure:** If GPU is busy, the Batcher must pause or queue up.

### Deep Dive Topics (What likely caused failure)
- **Race Conditions:** Handling concurrent requests safely.
- **Failures:** What if a single item causes the whole batch to crash (OOM)?
    - *Solution:* Error isolation / bisecting the batch.
- **Tail Latency:** How does batching affect P99? (Head-of-line blocking).
- **Affinity:** Do we route requests for the same model to the same node? (Locality).

### Warning Flags (From User Experience)
- **Mismatched Level:** Candidates report being asked general app design (Messaging) even for deep infra roles.
- **Verification:** Interviewers might perform "calculator math" to verify your throughput/latency numbers add up. Be precise.
