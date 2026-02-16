
import random

class CircularArray:
    def __init__(self, size, initial_values=None):
        self.size = size
        if initial_values:
            if len(initial_values) != size:
                raise ValueError("Initial values length must match size")
            self.data = list(initial_values)
        else:
            self.data = [random.choice([0, 1]) for _ in range(size)]
        
        self.current_index = 0
        self.steps_taken = 0  # To track "limited operations" if needed

    def move_forward(self):
        self.current_index = (self.current_index + 1) % self.size
        self.steps_taken += 1

    def move_backward(self):
        self.current_index = (self.current_index - 1 + self.size) % self.size
        self.steps_taken += 1

    def get_value(self):
        return self.data[self.current_index]

    def set_value(self, value):
        if value not in (0, 1):
            raise ValueError("Value must be 0 or 1")
        self.data[self.current_index] = value

def find_circular_array_size(arr: CircularArray) -> int:
    """
    Determines the size of the CircularArray using limited operations.
    Optimized O(N) Algorithm:
    1. Set start (current pos) to 1.
    2. Expand a search range exponentially: 1, 2, 4, 8...
    3. In each range [0, limit], walk forward and clear all '1's to '0'.
    4. At the end of the range (limit), check if start is still '1'.
       - If start is '1': It hasn't been overwritten. Size N > limit.
         Continue to next range [limit, 2*limit].
       - If start is '0': It was overwritten! Size N <= limit.
         We have found an upper bound.
    5. Phase 2: Find exact size.
       - The array is now "clean" (all 0s) at least up to N.
       - We are currently at start (index 0) because we moved back to check.
       - Set start to 1.
       - Walk forward until we see 1 again. The distance is N.
    """
    
    # Initialize start point
    arr.set_value(1)
    
    limit = 1
    total_displacement = 0
    
    while True:
        # Move forward 'limit' steps, carefully clearing '1's
        for idx in range(limit):
            arr.move_forward()
            if arr.get_value() == 1:
                # print(f"DEBUG: Clearing 1 at displacement {total_displacement + idx + 1}")
                arr.set_value(0)
        
        total_displacement += limit
        
        # Check start (absolute position 0)
        # We need to move back 'total_displacement' steps
        for _ in range(total_displacement):
            arr.move_backward()
            
        if arr.get_value() == 0:
            # Start was killed! total_displacement >= N
            # print(f"DEBUG: Start killed. Upper bound {total_displacement}")
            break
        else:
            # Start is alive. N > total_displacement.
            # Restore position to continue clearing
            for _ in range(total_displacement):
                arr.move_forward()
            limit *= 2

    # Phase 2: Find exact N
    # We are currently at start (index 0).
    # The array has been cleared of '1's at least up to N.
    # Set start to 1.
    arr.set_value(1)
    
    count = 0
    while True:
        arr.move_forward()
        count += 1
        if arr.get_value() == 1:
            return count


def test_solution():
    test_cases = [
        (1, [0]),
        (1, [1]),
        (2, [0, 1]),
        (2, [0, 0]),
        (2, [1, 1]),
        (3, [0, 1, 0]),
        (5, [1, 1, 1, 1, 1]),
        (10, [0]*10),
        (100, [random.randint(0, 1) for _ in range(100)]),
    ]

    print("Running tests...")
    for size, initial_vals in test_cases:
        arr = CircularArray(size, initial_vals)
        result = find_circular_array_size(arr)
        print(f"Expected: {size}, Got: {result} - {'PASS' if result == size else 'FAIL'}")
        assert result == size

    print("\nLarge Random Test (Size 500)")
    size = 5000
    arr = CircularArray(size)
    result = find_circular_array_size(arr)
    print(f"Expected: {size}, Got: {result} - {'PASS' if result == size else 'FAIL'}")
    assert result == size

if __name__ == "__main__":
    test_solution()
