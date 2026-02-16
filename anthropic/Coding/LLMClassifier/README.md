# LLM Binary Classifier (Coding Q5/Topic LLM)

**Source:** [1point3acres (1137751)](https://www.1point3acres.com/bbs/thread-1137751-1-1.html)

### Problem Description
This interview is topic-specific ("LLM") but is essentially a coding/implementation task.
**Goal:** Build a **Binary Classifier** using a provided LLM helper function.

**Provided Helper:**
- `get_token_probs(inputs: List[str]) -> List[Dict[str, float]]`
    - Returns log-probabilities of the next token for a batch of inputs.
    - Output format might be like: `[{'Yes': -0.1, 'No': -2.3}, ...]` (Log Probs).

**Task:**
1.  **Design System Prompt:** Create a prompt template that forces the LLM to output a binary decision (e.g., "Is this sentiment positive? Answer Yes or No.").
2.  **Scoring Logic:** Instead of just checking if the output is "Yes" or "No", use the **probabilities**.
    - Calculate a logic score based on `P("Yes")` vs `P("No")`.
    - Handle Log Probabilities (add/subtract them, don't multiply).
    - Score = `exp(log_prob_yes) / (exp(log_prob_yes) + exp(log_prob_no))` (Softmax).
3.  **Thresholding:** Decide the class based on a customizable threshold (default 0.5).

### Key Challenges
- **Log Probabilities:** Understanding that models usually return log-probs. Simple arithmetic errors here are fatal.
- **Normalization:** The model might output other tokens. You need to normalize only across your target tokens ("Yes", "No").
- **Batching:** The helper takes a batch. Your classifier should process a batch efficiently.

### Follow-ups (Performance Optimization)
1.  **Prompt Engineering:** Few-shot prompting to stabilize output.
2.  **Threshold Tuning:** Adjust threshold for Precision vs Recall.
3.  **Self-Consistency (Repeated Sampling):**
    - Generate multiple times (with temp > 0) and take majority vote?
    - *Correction:* For a classifier based on *next token prob*, you don't generate. You just inspect the prob distribution at the first position. Repeated sampling might apply if you are doing Chain-of-Thought (CoT) generation before the answer.

### Code Structure
```python
def classify(inputs: List[str], helper_fn) -> List[float]:
    # 1. format prompts
    prompts = [f"Text: {txt}\nIs this likely to be spam? Answer Yes or No:" for txt in inputs]
    
    # 2. call helper
    # Returns list of dicts: [{'Yes': -0.5, 'No': -1.2, ...}, ...]
    all_log_probs = helper_fn(prompts) 
    
    scores = []
    for log_probs in all_log_probs:
        # 3. Extract logic
        # Handle case where 'Yes' or 'No' might not be top 1
        lp_yes = log_probs.get('Yes', -999)
        lp_no = log_probs.get('No', -999)
        
        # 4. Normalize (Softmax)
        # score = exp(yes) / (exp(yes) + exp(no))
        pass
    return scores
```
