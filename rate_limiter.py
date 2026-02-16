from collections import deque

def solve_rate_limiter(timestamps: list[int], maxRequests: int, windowSize: int) -> list[bool]:
    """
    Determines for each request whether it should be allowed based on a sliding window of allowed requests.
    
    Args:
        timestamps: A strictly increasing list of request timestamps.
        maxRequests: The maximum number of allowed requests in the window.
        windowSize: The size of the time window [t - windowSize + 1, t].
        
    Returns:
        A list of booleans indicating allowing (True) or rejection (False) for each request.
    """
    allowed_timestamps = deque()
    results = []
    
    for t in timestamps:
        # Remove expired timestamps from the window
        # Window is [t - windowSize + 1, t] (inclusive)
        # Expired if timestamp < t - windowSize + 1
        lower_bound = t - windowSize + 1
        
        while allowed_timestamps and allowed_timestamps[0] < lower_bound:
            allowed_timestamps.popleft()
            
        # Check current capacity
        if len(allowed_timestamps) < maxRequests:
            allowed_timestamps.append(t)
            results.append(True)
        else:
            results.append(False)
            
    return results
