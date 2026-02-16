import math
from typing import List, Dict

# --- Mock LLM Helper Function ---
def get_log_probs(prompts: List[str]) -> List[Dict[str, float]]:
    """
    Simulates an LLM API returning log-probabilities for next tokens.
    For demonstration, we mock results based on certain keywords in `prompts`.
    """
    results = []
    for p in prompts:
        # Mock sentiment analysis: "bad" suggests negative ("No"), "good" suggests positive ("Yes")
        if "bad" in p.lower():
            # Higher prob for 'No' (Negative being the target class?)
            # Let's say we classify "Is this positive?" -> No
            # log(0.1) approx -2.3, log(0.9) approx -0.1
            results.append({'Yes': -2.3, 'No': -0.1, 'Maybe': -5.0})
        else:
            # Positive
            results.append({'Yes': -0.1, 'No': -2.3, 'Maybe': -5.0})
    return results

class LLMClassifier:
    def __init__(self, helper_fn):
        self.helper_fn = helper_fn
        self.positive_token = "Yes"
        self.negative_token = "No"

    def predict_proba(self, texts: List[str]) -> List[float]:
        """
        Returns the probability of the POSITIVE class.
        """
        # 1. Format Prompts
        # System prompt engineering is key here.
        prompts = [
            f"Review: {text}\nIs this review positive? Answer Yes or No:" 
            for text in texts
        ]
        
        # 2. Get Log Probs from LLM
        # Batch processing is crucial for efficiency
        batch_log_probs = self.helper_fn(prompts)
        
        probabilities = []
        for log_probs in batch_log_probs:
            # 3. Extract logic
            # Use specific tokens. Default to very low probability (-999) if token not in top-k
            lp_pos = log_probs.get(self.positive_token, -999.0)
            lp_neg = log_probs.get(self.negative_token, -999.0)
            
            # 4. Normalize (Softmax on just these two tokens)
            # P(Yes) = exp(Yes) / (exp(Yes) + exp(No))
            # To avoid overflow, we can subtract max? (Not strictly needed for 2 classes usually)
            
            try:
                exp_pos = math.exp(lp_pos)
                exp_neg = math.exp(lp_neg)
                
                # Handling case where both are virtually zero probability (shouldn't happen with good prompt)
                total = exp_pos + exp_neg
                if total == 0:
                    prob = 0.5
                else:
                    prob = exp_pos / total
            except OverflowError:
                # If one is huge, it dominates
                prob = 1.0 if lp_pos > lp_neg else 0.0
                
            probabilities.append(prob)
            
        return probabilities

    def predict(self, texts: List[str], threshold: float = 0.5) -> List[str]:
        probas = self.predict_proba(texts)
        return [self.positive_token if p >= threshold else self.negative_token for p in probas]

# Example Usage
if __name__ == "__main__":
    classifier = LLMClassifier(get_log_probs)
    inputs = ["This movie was good", "This movie was bad behavior"]
    
    print("Inputs:", inputs)
    probs = classifier.predict_proba(inputs)
    print("Probabilities (Positive):", probs)
    preds = classifier.predict(inputs)
    print("Predictions:", preds)
