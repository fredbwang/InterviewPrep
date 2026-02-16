# Inference System Design (System Design Q1)

**Question:** Design a scalable, secure, and reliable backend for serving LLM/AI model requests.

### Key Concepts for Q1
This question focuses on **Infrastructure** and **Architecture** rather than ML specifics (though basic understanding helps).

1.  **Architecture:**
    - **API Gateway:** Auth, Rate Limiting (Token Bucket), Routing.
    - **Compute Layer (GPU Fleet):** Stateless workers.
    - **Queue Layer:** Decouple intake from processing (Time-to-first-token is critical).
    - **Model Registry/Storage:** Where models are loaded from (S3/GCS) with caching on nodes.

2.  **Scalability (The "S"):**
    - **Horizontal Scaling:** Autoscaling GPU nodes based on *Queue Depth* or *GPU Memory Pressure*.
    - **Cold Starts:** How to handle massive startup time for 70B+ models? (keep warm pools).
    - **Continuous Batching:** Maximize throughput (explain vLLM concept lightly).

3.  **Reliability (The "R"):**
    - **Health Checks:** Detect stuck inference (CUDA errors).
    - **Circuit Breakers:** Fail fast if backend is overloaded.
    - **Fallback:** Route to smaller models if large ones fail?

4.  **Security:**
    - **Rate Limiting:** Crucial due to high compute cost (Quota per org/user).
    - **Input Validation:** Context window limits.
    - **PII Redaction:** Filter inputs before logging.

### Deep Dive: Inference Mechanics (Good for Bonus)
1.  **Pre-fill vs Decode:**
    - *Pre-fill:* Processing the prompt (parallelizable).
    - *Decode:* Generating tokens one by one (sequential).
2.  **KV Cache:** Managing GPU memory.

### Resources
- [vLLM: Easy, Fast, and Cheap LLM Serving](https://vllm.ai/)
- [Continuous Batching Explained](https://www.anyscale.com/blog/continuous-batching-llm-inference)
