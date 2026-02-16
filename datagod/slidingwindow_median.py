from typing import List, Dict

def sliding_window(input_points: List[Dict], tag: str, k: int, is_time_window: bool = False) -> List[int]:
    """
    Calculates the sum of values in sliding windows based on either a fixed number of points or a fixed time duration.
    
    Args:
        input_points: List of data point dictionaries containing 'tags', 'timestamp', 'value'.
        tag: The tag to filter by.
        k: The window size (number of points OR duration in seconds).
        is_time_window: Boolean flag to switch between fixed-point (False) and fixed-time (True) modes.
        
    Returns:
        List of sums for each valid window.
    """
    # ---------------------------------------------------------
    # SHARED PRE-PROCESSING
    # ---------------------------------------------------------
    # Filter points by tag and extract (timestamp, value)
    filtered_points = [
        (p["timestamp"], p["value"]) 
        for p in input_points 
        if tag in p["tags"]
    ]
    
    # Sort by timestamp
    filtered_points.sort(key=lambda x: x[0])
    
    if not filtered_points:
        return []

    results = []
    
    # ---------------------------------------------------------
    # DIVERGENCE: Handle specific window logic
    # ---------------------------------------------------------
    if not is_time_window:
        # === Strategy 1: Fixed Number of Points (k points) ===
        if len(filtered_points) < k:
            return []
        
        # Calculate sum of the first window
        current_sum = sum(p[1] for p in filtered_points[:k])
        results.append(current_sum)
        
        # Slide the window
        # We start from index k because the first window includes indices 0 to k-1
        for i in range(k, len(filtered_points)):
            current_sum += filtered_points[i][1]       # Add new point entering window
            current_sum -= filtered_points[i - k][1]   # Remove old point leaving window
            results.append(current_sum)
            
    else:
        # === Strategy 2: Fixed Time Duration (k seconds) ===
        # The window [t, t + k] must be fully contained within the global data range.
        max_time = max(p["timestamp"] for p in input_points)
        
        right = 0
        current_sum = 0
        n = len(filtered_points)
        
        # Iterate through each point as the start of a potential window
        for left in range(n):
            start_time = filtered_points[left][0]
            end_time = start_time + k
            
            # Constraint check: Window must end at or before the last recorded global timestamp
            if end_time > max_time:
                break
            
            # Expand right boundary to include all points falling within [start_time, end_time]
            # Note: filtered_points is sorted by timestamp
            while right < n and filtered_points[right][0] <= end_time:
                current_sum += filtered_points[right][1]
                right += 1
                
            results.append(current_sum)
            
            # Prepare for next iteration: 
            # The next window will start at filtered_points[left + 1]. 
            # The current start point (filtered_points[left]) will logically fall out 
            # of the window relative to the new start time, so we decrement its value.
            current_sum -= filtered_points[left][1]

    return results

if __name__ == "__main__":
    input_points = [
        {"tags": ["env:dev"], "timestamp": 0, "value": 1},
        {"tags": ["env:dev"], "timestamp": 1, "value": 3},
        {"tags": ["env:prod", "host:a"], "timestamp": 2, "value": 5},
        {"tags": ["env:dev"], "timestamp": 3, "value": -1},
        {"tags": ["env:dev", "host:a"], "timestamp": 6, "value": -3},
        {"tags": ["env:dev"], "timestamp": 7, "value": 5},
        {"tags": ["env:staging", "host:a"], "timestamp": 9, "value": -3},
        {"tags": ["env:dev"], "timestamp": 10, "value": -4},
        {"tags": ["env:dev"], "timestamp": 11, "value": 6},
        {"tags": ["env:dev"], "timestamp": 14, "value": -1},
        {"tags": ["env:staging"], "timestamp": 15, "value": 10},
    ]

    print("Part 1 (Fixed Points k=3):")
    # Expected Output: [3, -1, 1, -2, 7, 1]
    print(sliding_window(input_points, "env:dev", 3, is_time_window=False))

    print("\nPart 2 (Fixed Time k=3):")
    # Expected Output: [3, 2, -4, 2, 1, 2, 5]
    print(sliding_window(input_points, "env:dev", 3, is_time_window=True))