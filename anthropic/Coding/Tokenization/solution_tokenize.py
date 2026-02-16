from typing import List, Dict, Optional

class Tokenizer:
    def __init__(self, vocab: Dict[str, int]):
        self.vocab = vocab
        self.reversed_vocab = {v: k for k, v in vocab.items()}
        self.unk_token_id = vocab.get("UNK", -1)

    def simple_tokenize_flawed(self, text: str) -> List[int]:
        """
        Original flawed implementation from the interview question.
        Issues: Greedy matching misses long tokens, loses characters not in vocab.
        """
        tokens = []
        key = ""
        for char in text:
            key += char
            if key in self.vocab:
                tokens.append(self.vocab[key])
                key = ""
        return tokens

    def tokenize_max_match(self, text: str) -> List[int]:
        """
        Tokenize using Maximum Matching (Greedy Left-to-Right).
        """
        tokens = []
        i = 0
        n = len(text)
        max_token_len = max(len(k) for k in self.vocab.keys()) if self.vocab else 0

        while i < n:
            match_found = False
            # Try to match the longest possible token starting at i
            # Limit the search window to max_token_len for efficiency
            end_limit = min(n, i + max_token_len)
            
            for j in range(end_limit, i, -1):
                chunk = text[i:j]
                if chunk in self.vocab:
                    tokens.append(self.vocab[chunk])
                    i = j
                    match_found = True
                    break
            
            if not match_found:
                # Handle unknown character
                # Option 1: Emit UNK token (Standard NLP approach)
                # Option 2: Skip character
                # Option 3: Keep raw character (If detokenizer supports it)
                if "UNK" in self.vocab:
                    tokens.append(self.vocab["UNK"])
                else:
                    # In this problem context, maybe append -1 or raise error?
                    pass
                i += 1  # Advance past the unknown character

        return tokens

    def detokenize(self, tokens: List[int]) -> str:
        text = ""
        for token in tokens:
            if token in self.reversed_vocab:
                text += self.reversed_vocab[token]
            else:
                # How to handle unknown tokens? In strict mode, maybe error.
                pass
        return text

# Example Usage
if __name__ == "__main__":
    vocab = {
        "a": 1,
        "b": 2,
        "ab": 3,
        "UNK": -1
    }
    tokenizer = Tokenizer(vocab)
    
    text = "aba"
    # Flawed: 'a' -> 1, 'b' -> 2, 'a' -> 1. Result: [1, 2, 1] ("a", "b", "a")
    # Max Match: 'ab' -> 3, 'a' -> 1. Result: [3, 1] ("ab", "a")
    
    print(f"Text: {text}")
    print(f"Flawed: {tokenizer.simple_tokenize_flawed(text)}")
    print(f"MaxMatch: {tokenizer.tokenize_max_match(text)}")
    
    # Test with Unknown
    text_unk = "axb"
    print(f"Text with unknown: {text_unk}")
    print(f"MaxMatch (UNK): {tokenizer.tokenize_max_match(text_unk)}") # Expect [1, -1, 2]
