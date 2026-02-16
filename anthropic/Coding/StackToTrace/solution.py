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
    if not samples:
        return []
        
    events = []
    
    class ActiveFrame:
        def __init__(self, name, start_ts):
            self.name = name
            self.start_ts = start_ts
            self.count = 1
            self.emitted = False
            
    active_stack: List[ActiveFrame] = []
    
    for sample in samples:
        curr_raw_stack = sample.stack
        ts = sample.ts
        
        # 1. Compute Longest Common Prefix (LCP) with active stack
        lcp = 0
        min_len = min(len(active_stack), len(curr_raw_stack))
        while lcp < min_len and active_stack[lcp].name == curr_raw_stack[lcp]:
            lcp += 1
            
        # 2. Handle runs that ended (prune from top)
        # These frames are no longer present in the current stack
        while len(active_stack) > lcp:
            frame = active_stack.pop()
            if frame.emitted:
                events.append(Event("end", ts, frame.name))
                
        # 3. Handle continuing runs (increment count, maybe emit)
        for i in range(lcp):
            frame = active_stack[i]
            frame.count += 1
            if frame.count >= n_consecutive and not frame.emitted:
                events.append(Event("start", frame.start_ts, frame.name))
                frame.emitted = True
                
        # 4. Handle new runs (add to stack)
        for i in range(lcp, len(curr_raw_stack)):
            name = curr_raw_stack[i]
            new_frame = ActiveFrame(name, ts)
            
            # Special case for N=1: emit immediately
            if n_consecutive <= 1:
                events.append(Event("start", ts, name))
                new_frame.emitted = True
                    
            active_stack.append(new_frame)
            
    events.sort(key=lambda x: (x.ts, 0 if x.kind == 'start' else 1))
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
