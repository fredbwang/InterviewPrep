# Tokenization (Internal Tooling)

**Sources:**
- [1point3acres (7100015)](https://www.1point3acres.com/interview/problems/post/7100015)
- [1point3acres (1111070)](https://www.1point3acres.com/bbs/thread-1111070-1-1.html)
- [1point3acres (1164836)](https://www.1point3acres.com/bbs/thread-1164836-1-1.html)

### Problem Description
This interview focuses on code readability, code review, and implementing a robust tokenizer for an internal tool.

#### Part 1: Read Code & Identify Issues
You are given a simple `tokenize` and `detokenize` function.
**Code:**
```python
def tokenize(text: str, vocab: dict):
    tokens = []
    key = ""
    for i in range(len(text)):
        key += text[i]
        if key in vocab:
            tokens.append(vocab[key])
            key = ""
    return tokens

vocab = {"a": 1, "b": 2, "cd": 3}
```
**Issues:**
1.  **Greedy Matching:** It eagerly matches the first valid token.
    - Example: `vocab = {"t": 1, "to": 2}`, `text = "to"`.
    - It matches "t", emits token 1, then tries to match "o" (fails).
    - Result: `[1]`. Ideally should be `[2]`.
2.  **Unknown Characters:** If a character sequence doesn't match any vocab key, it is discarded or stuck in `key`.
    - Example: `text = "x"`. Key becomes "x". Loop ends. Token list is `[]`. "x" is lost.

#### Part 2: Code Review (UNK Handling)
The interviewer proposes a patch:
```python
if key in vocab: ...
else:
   tokens.append(vocab.get("UNK", -1))
```
**Critique:**
- **Premature UNK:** Adding UNK immediately when a key isn't in vocab breaks prefix matching.
    - `text="ca"`, `vocab={"cat": 1}`.
    - `key="c"`. Not in vocab -> emits UNK. `key` reset?
    - If `key` resets, we can never match "cat".
- **Ambiguity:** What does UNK represent? A single char? A block?
- **Loss of Information:** `detokenize` cannot recover the original text from UNK.

#### Part 3: Robust Implementation
**Goal:** Implement `tokenize` to handle:
1.  **Valid Vocab Matches**: Correctly identify tokens from the vocabulary.
2.  **Unknown Characters**: Handle characters not in the vocabulary without crashing or losing data.

**Approaches:**

**A. Prefix Check (User's Attempt):**
- Checking `if not any(k.startswith(key) for k in vocab)` allows you to detect when a sequence is a "Dead End" (cannot possibly form a token).
- *Downside:* `startswith` loop over entire vocab every char is O(V * L). Verry slow. Trie is better.

**B. Max Match (Recommended):**
- At index `i`, check substrings `text[i:j]` for `j` from `len(text)` down to `i+1`.
- Finds the longest valid token starting at `i`.
- If no match found, handle `text[i]` as Unknown (emit UNK or skip).
