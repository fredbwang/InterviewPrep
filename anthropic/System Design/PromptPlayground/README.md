# Prompt Playground (System Design Q2)

**Source:** [1point3acres (1152783)](https://www.1point3acres.com/bbs/thread-1152783-1-1.html)

### Problem Description
Design a **Prompt Engineering Playground** (similar to OpenAI Playground or Anthropic Console).
This falls under **System Design Q2: Product Design**, which emphasizes UX, user flows, data modeling, and handling trade-offs.

### Key Aspects to Cover

#### 1. User Flows (UX Focus)
- **Core Loop:** User types prompt -> Adjusts parameters (Temperature, Top-P, Model) -> Clicks Run -> Streams Output.
- **Comparison:** Running the same prompt against multiple models side-by-side.
- **Management:** Saving prompts, organizing into projects, version history.

#### 2. Data Design (Schema)
This is critical for Q2.
- **Prompt:** `id`, `content`, `variables` ({{name}}), `version_id`.
- **Configuration:** `model_id`, `temperature`, `max_tokens`.
- **Run/Execution:** `id`, `prompt_id`, `input_snapshot`, `output_content`, `latency_ms`, `tokens_used`.
- **History:** How to store diffs or full snapshots of prompt versions?

#### 3. System Components
- **Frontend:** React/Next.js (needs to handle streaming heavily).
- **Backend API:**
    - `POST /run`: Proxies to LLM provider (internal or external).
    - **Streaming:** Server-Sent Events (SSE) or WebSockets to stream tokens to the UI in real-time.
    - **Rate Limiting:** Per user/org quotas.
- **Database:** Postgres (relational data for prompts/users), potentially NoSQL (DynamoDB) for execution logs if high volume.

#### 4. Scaling & Trade-offs
- **Latency:** The playground must feel snappy.
    - *Trade-off:* Do we store every single "Run" for history? Or only if the user explicitly saves? Storage cost vs Utility.
- **Streaming:** Holding open connections for SSE scales differently than short-lived REST requests.
    - Need an async gateway/proxy.
- **Cost Management:** Users running massive prompts. Need strict budget alerts.

### Feature Ideas (Bonus)
- **Variable Interpolation:** Detect `{{variable}}` syntax and generate form fields for testing.
- **Eval Sets:** Allow running a prompt against 50 test cases and measuring accuracy (simple string match or LLM-as-a-judge).
