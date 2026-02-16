from collections import deque

def max_sum_with_limit(arr, k):
    """
    Finds the maximum sum of a subarray with length at most k.
    
    Args:
        arr (list[int]): The input array of integers.
        k (int): The maximum length of the subarray.
        
    Returns:
        int: The maximum subarray sum found.
    """
    n = len(arr)
    if n == 0 or k <= 0:
        return 0
    
    # Prefix sum array: P[i] is sum of arr[0...i-1]
    # P[0] = 0
    # P[x] = arr[0] + ... + arr[x-1]
    # Sum of subarray arr[i...j] (exclusive of j, inclusive of i in 0-based index)
    # is P[j+1] - P[i].
    # Let current ending index be 'current_idx' (from 1 to n).
    # We want max(P[current_idx] - P[start_idx]) where 1 <= current_idx - start_idx <= k.
    # So start_idx >= current_idx - k.
    
    P = [0] * (n + 1)
    for i in range(n):
        P[i+1] = P[i] + arr[i]
        
    # Deque stores indices 'i' of P, maintaining increasing order of P[i]
    q = deque([0])
    
    # Initialize max_sum to a very small number or the first possible sum
    max_sum = float('-inf')
    
    for i in range(1, n + 1):
        # 1. Remove indices that are out of the k-window from the front
        # The window constraint is: i - index <= k, so index >= i - k
        while q and q[0] < i - k:
            q.popleft()
            
        # 2. The deque front has the index with the minimum P value in range
        # maximizing P[i] - P[index]
        if q:
            current_sum = P[i] - P[q[0]]
            if current_sum > max_sum:
                max_sum = current_sum
                
        # 3. Maintain monotonic increasing property of deque for future P[i]
        # We are adding P[i] as a potential subtractor for future sums
        while q and P[q[-1]] >= P[i]:
            q.pop()
            
        q.append(i)
        
    return max_sum

def test_max_sum_with_limit():
    test_cases = [
        ([1, 2, 3, 4], 2, 7),        # [3, 4]
        ([1, -1, 1], 1, 1),          # [1] or [1]
        ([10, -2, -10, 5], 2, 10),   # [10]
        ([-1, -2, -3], 2, -1),       # [-1]
        ([5, -10, 5], 1, 5),         # [5]
        ([1, 2, -10, 3, 4], 2, 7),   # [3, 4]
        ([10, 20, 30], 1, 30),       # [30]
        ([1, 1, 1, 1, 1], 10, 5),    # Sum all
    ]
    
    for arr, k, expected in test_cases:
        result = max_sum_with_limit(arr, k)
        print(f"Arr: {arr}, K: {k} -> Expected: {expected}, Got: {result}")
        assert result == expected
        
if __name__ == "__main__":
    test_max_sum_with_limit()
