# System Design Q1 vs Q3: Clarification

**Source:** [1point3acres (1158532)](https://www.1point3acres.com/bbs/thread-1158532-1-1.html)

### The Confusion
Candidates report encountering "Inference API" questions in both Q1 and Q3. The core difference lies not necessarily in the *topic* (Inference) but in the **focus** of the interview.

### Q1: Scalable Infrastructure Design
- **Prompt:** "Design scalable, secure, and reliable systems to solve a complex problem."
- **Focus:** **Greenfield Design & Architecture.**
    - How do you build it from scratch?
    - Load Balancing, Database Sharding, Caching, API Gateway.
    - Consistency vs Availability (CAP theorem).
- **Inference Context:**
    - "Design an API that takes a prompt and returns a completion."
    - You must design the queue, the worker fleet, the result storage.
    - How to handle 1M RPS? How to handle long-running requests?

### Q3: System Metrics & Optimization (ML Operations)
- **Prompt:** "Scale, monitor and optimize an existing system in production. Focus on aspects of a ML driven system outside the model architecture itself."
- **Focus:** **Operational Excellence, Observability, & ML Specifics.**
    - The system *exists*. It's slow or failing. Fix it.
    - **Metrics:** Latency (P99, P95), Throughput, Error Rates, GPU Utilization.
    - **ML Specifics:** Function drift, Data drift, Model staleness, A/B Testing infrastructure.
    - **Scaling:** Autoscaling policies based on *queue depth* vs *GPU memory*.
- **Inference Context:**
    - "Our inference API has high P99 latency. How do you debug and fix it?"
    - "We need to deploy a new model version without downtime. Design the rollout."
    - "Requests are failing. How do you set up alerting?"

### Summary Table

| Feature | Q1 (Infrastructure) | Q3 (Metrics & ML Ops) |
| :--- | :--- | :--- |
| **Stage** | Design from scratch (Whiteboard) | Optimization / Debugging (Scenario) |
| **Key Artifacts** | High-level Diagram, Component definition | Dashboards, Alerting rules, Rollout strategies |
| **ML Depth** | Shallow (Treat model as black box worker) | Deep (Understand pre-fill/decode, batching impact) |
| **Problem Ex** | "Build ChatGPT backend" | "ChatGPT is slow at night. Why?" |
