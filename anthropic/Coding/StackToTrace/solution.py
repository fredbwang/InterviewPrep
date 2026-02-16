from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Sample:
    ts: float
    stack: List[str]

@dataclass
class Event:
    kind: str  # "start" or "end"
    ts: float
    name: str

    def __repr__(self):
        return f'{self.kind} {self.ts} {self.name}'

def convert_to_trace(samples: List[Sample]) -> List[Event]:
    """
    Converts a list of stack samples into a trace of start/end events.
    """
    events = []
    prev_stack = []
    
    for sample in samples:
        curr_stack = sample.stack
        ts = sample.ts
        
        # Find Longest Common Prefix (LCP) length
        lcp_len = 0
        min_len = min(len(prev_stack), len(curr_stack))
        while lcp_len < min_len and prev_stack[lcp_len] == curr_stack[lcp_len]:
            lcp_len += 1
            
        # 1. Handle Ends (functions disjoint from current stack)
        # We must end functions from the top of the stack downwards (reverse order)
        # These are functions present in prev_stack but not in curr_stack (after LCP)
        for i in range(len(prev_stack) - 1, lcp_len - 1, -1):
            events.append(Event("end", ts, prev_stack[i]))
            
        # 2. Handle Starts (new functions in current stack)
        # These are functions present in curr_stack but not in prev_stack (after LCP)
        for i in range(lcp_len, len(curr_stack)):
            events.append(Event("start", ts, curr_stack[i]))
            
        prev_stack = list(curr_stack)  # Create a copy to be safe
        
    return events


def convert_to_trace_filtered(samples: List[Sample], n_consecutive: int) -> List[Event]:
    """
    Follow-up: Prune brief function calls.
    Only emit events for functions that appear in N consecutive samples.
    """
    events = []
    prev_stack = [] # This tracks the *effective* stack (only events we actually admitted)
    
    for i, sample in enumerate(samples):
        curr_raw_stack = sample.stack
        ts = sample.ts
        
        # Determine which functions in the current raw stack are "valid"
        # A function at index `d` is valid if it appears in samples[i...i+n-1] at index `d`
        # AND it matches the name.
        # Ideally, the parent chain must also be valid.
        
        curr_effective_stack = []
        for d, func_name in enumerate(curr_raw_stack):
            # Check if this specific frame persists for N samples
            is_persistent = True
            if i + n_consecutive > len(samples):
                is_persistent = False
            else:
                for k in range(1, n_consecutive):
                    future_sample = samples[i+k]
                    # Check bounds and name match
                    if d >= len(future_sample.stack) or future_sample.stack[d] != func_name:
                        is_persistent = False
                        break
            
            # If persistent, add to effective stack. 
            # Note: If parent is not persistent, child cannot be persistent in a valid trace?
            # Or can we have gaps? "Nested function call's end event is before enclosing".
            # If parent is pruned, the child is orphaned. 
            # Usually, if parent is pruned, child is implicitly pruned or merged.
            # We'll assume strict hierarchy: if parent is pruned, stop.
            if is_persistent:
                curr_effective_stack.append(func_name)
            else:
                break # Stop adding children if parent is not valid
        
        # Now perform standard diff logic between prev_stack (effective) and curr_effective_stack
        lcp_len = 0
        min_len = min(len(prev_stack), len(curr_effective_stack))
        while lcp_len < min_len and prev_stack[lcp_len] == curr_effective_stack[lcp_len]:
            lcp_len += 1
            
        # Ends
        for idx in range(len(prev_stack) - 1, lcp_len - 1, -1):
            events.append(Event("end", ts, prev_stack[idx]))
            
        # Starts 
        # Note: Use the timestamp of the *first* sample where it appeared?
        # The prompt says: "You can decide if you want to use the 1st or Nth timestamp for the start time".
        # We'll use the current sample's timestamp (1st).
        for idx in range(lcp_len, len(curr_effective_stack)):
            events.append(Event("start", ts, curr_effective_stack[idx]))
            
        prev_stack = curr_effective_stack

    return events


if __name__ == "__main__":
    print("--- Basic Test ---")
    s1 = Sample(1.0, ["main"])
    s2 = Sample(2.5, ["main", "func1"])
    s3 = Sample(3.1, ["main"])
    
    samples = [s1, s2, s3]
    events = convert_to_trace(samples)
    for e in events:
        print(e)
        
    print("\n--- Recursive Test ---")
    # Sample s2{1, {"main"}};
    # Sample s3{2, {"main", "f1", "f2", "f3"}};
    # Sample s4{3, {"main"}};
    r1 = Sample(1.0, ["main"])
    r2 = Sample(2.0, ["main", "f1", "f2", "f3"])
    r3 = Sample(3.0, ["main"])
    rec_samples = [r1, r2, r3]
    rec_events = convert_to_trace(rec_samples)
    for e in rec_events:
        print(e)

    print("\n--- Pruning Test (N=2) ---")
    # A appears in 1, 2. B appears in 1.
    # 1: [A, B]
    # 2: [A]
    # 3: [A]
    # If N=2:
    # 1: A is in 1,2. Valid. B is in 1, not 2. Invalid. Eff=[A]
    # 2: A is in 2,3. Valid. Eff=[A]
    # 3: A is in 3 (end of list, can't be N=2 consecutive unless we count backward or assume future? 
    # Usually "N consecutive samples" implies lookahead. If we are at end, we can't lookahead.
    # So last N-1 samples can never start new events? Or do we assume stability?
    # Logic: if i + n > len, is_persistent = False.
    
    p1 = Sample(10, ["root", "noise"]) 
    p2 = Sample(11, ["root"])
    p3 = Sample(12, ["root", "feature"])
    p4 = Sample(13, ["root", "feature"]) 
    
    # N=2:
    # 1: root is in 1,2. "noise" not in 2. Eff=[root]. Start root.
    # 2: root is in 2,3. Eff=[root]. No change.
    # 3: root is in 3,4. "feature" is in 3,4. Eff=[root, feature]. Start feature.
    # 4: root is in 4... (no 5). "feature" is in 4... (no 5). 
    # If strictly lookahead, they fail. If we treat existing as valid until proven otherwise?
    # The prompt: "prune ... by only emitting events for function calls that appear in N consecutive samples".
    # Usually implies filtering the input stream.
    # Let's see the logic output.
    
    prune_samples = [p1, p2, p3, p4]
    prune_events = convert_to_trace_filtered(prune_samples, 2)
    for e in prune_events:
        print(e)
