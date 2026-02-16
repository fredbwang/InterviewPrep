from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Sample:
    ts: int
    stack: List[str]

@dataclass
class Event:
    kind: str  # "start" or "end"
    ts: int
    name: str

    def __repr__(self):
        return f'{self.kind}:{self.ts}:{self.name}'

def parse_input(input_strings: List[str]) -> List[Sample]:
    samples = []
    for s in input_strings:
        # Format "ts:stack_string"
        parts = s.split(':', 1)
        ts = int(parts[0])
        stack_str = parts[1]
        if not stack_str:
            stack = []
        else:
            stack = stack_str.split('->')
        samples.append(Sample(ts, stack))
    return samples

def format_output(events: List[Event]) -> List[str]:
    return [str(e) for e in events]

def convert_to_trace_filtered(samples: List[Sample], n_consecutive: int = 1) -> List[Event]:
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
            
    
    # Sort events by timestamp to ensure chronological order.
    # For the same timestamp, 'start' should ideally come before 'end' 
    # (though typically they naturally separate by strict nesting, 
    # but for safety/cleanliness we enforce it).
    events.sort(key=lambda x: (x.ts, 0 if x.kind == 'start' else 1))
    
    return events

def solve(input_strings: List[str]) -> List[str]:
    # Defaulting to N=2 based on strict input/output example alignment attempt
    # But user didn't specify.
    # Let's try to match the logic first.
    samples = parse_input(input_strings)
    # The user manual example might be N=2
    events = convert_to_trace_filtered(samples, n_consecutive=2)
    return format_output(events)

if __name__ == "__main__":
    test_input = [
        "1:main",
        "2:main->A",
        "3:main->A",
        "4:main->B",
        "5:main->B->C",
        "6:main->B"
    ]
    result = solve(test_input)
    print(result)
