# Stock Agent (Tool Use / LLM Building Block)

**Source:** [1point3acres (1144763)](https://www.1point3acres.com/bbs/thread-1144763-1-1.html)

### Problem Description
**Classification:** Agents/Coding (New Category)

This interview tests your ability to **build an Agent** using LLMs as a component.
- **Environment:** Google Colab.
- **Context:** Tools (`get_stock_price`, `calculate`) and API syntax are provided.
- **Constraint:** Open-book (don't memorize syntax), focus on logic.

### Task 1: Single-Turn Agent
Implement a function that:
1.  Takes a user query (e.g., "What is the price of Apple plus Microsoft?").
2.  Calls the LLM with available tools.
3.  Parses the LLM response (which might request tool calls).
4.  Executes the tools (e.g., calls `get_stock_price("AAPL")`).
5.  (Optional for Single Turn) Returns the final answer or the tool outputs to the user.

**Key Concept: The ReAct Loop (Reason + Act)**
1.  **Thought:** LLM decides what to do.
2.  **Action:** LLM emits a tool call.
3.  **Observation:** Code executes tool, gets result.
4.  **Response:** Feed observation back to LLM (Multi-turn) or return.

### Task 2: Optimization (Cost & Latency)
**Question:** How to reduce LLM calls and API calls?

**Strategies:**
1.  **Multi-Tool Call (Parallel):**
    - Instead of `Call LLM -> Get AAPL -> Call LLM -> Get MSFT`, teach the LLM to output `[get_price("AAPL"), get_price("MSFT")]` in a *single* turn.
    - Execute both in parallel.
    - Feed both results back.
2.  **Batching:** If the API supports it, `get_prices(["AAPL", "MSFT"])`.
3.  **Caching:** Cache stock prices for a short duration (TTL).
4.  **System Prompt Optimization:** Explicitly instruct the model to "Make all necessary tool calls at once".

### Sample Code Structure
- `tools`: A dictionary of mapping function names to implementations.
- `tool_definitions`: The JSON schema passed to the LLM.
- `run_agent(query)`: The main loop.
