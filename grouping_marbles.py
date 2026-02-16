
def solve_grouping_marbles(n, groupA, groupB, groupC):
    """
    Solves the Grouping Marbles problem.
    
    Args:
        n (int): The total number of marbles, numbered 1 to n.
        groupA (list): List of marble numbers currently in group A.
        groupB (list): List of marble numbers currently in group B.
        groupC (list): List of marble numbers currently in group C.
        
    Returns:
        int: The minimum number of moves required.
    """
    
    # Map each marble to its current group for O(1) lookup
    # 0: A, 1: B, 2: C
    # Indices are 1-based marble numbers
    marble_to_group = {}
    for x in groupA:
        marble_to_group[x] = 0
    for x in groupB:
        marble_to_group[x] = 1
    for x in groupC:
        marble_to_group[x] = 2
        
    # Variables to track prefix counts
    # cA: Count of marbles in 1..k that are in Input A
    # cB: Count of marbles in 1..k that are in Input B
    # cC: Count of marbles in 1..k that are in Input C
    cA = 0
    cB = 0
    cC = 0 # Actually cC is not strictly needed for the formula but good for debug
    
    # We want to maximize: 
    #   Matches = (PrefixA[i] - PrefixB[i]) + (PrefixB[j] - PrefixC[j]) + TotalC
    #   Subject to 0 <= i <= j <= n
    # Let X[k] = PrefixA[k] - PrefixB[k]
    # Let Y[k] = PrefixB[k] - PrefixC[k]
    # We need max(X[i] + Y[j]) for i <= j.
    
    # Initialization for k=0
    # At k=0, counts are 0. X[0]=0. Y[0]=0.
    max_X = 0        # max(X[i]) for 0 <= i <= current_j
    best_term = 0    # max(X[i] + Y[j]) for 0 <= i <= j <= current_k
    
    for k in range(1, n + 1):
        group = marble_to_group.get(k)
        
        if group == 0: # A
            cA += 1
        elif group == 1: # B
            cB += 1
        elif group == 2: # C
            cC += 1
            
        # Calculate X and Y for current index k (which acts as 'j' in our formula)
        current_X = cA - cB
        current_Y = cB - cC
        
        # Determine max X seen so far (candidate for optimal i)
        # Since i <= j, and we are at j=k, any previous i (0..k) is valid
        # if current_X > max_X:
        #     max_X = current_X
        max_X = max(max_X, current_X)
            
        # Determine best term for current j
        current_term = max_X + current_Y
        
        # if current_term > best_term:
        #     best_term = current_term
        best_term = max(best_term, current_term)
            
    # Total marbles in C initially
    total_C = len(groupC)
    
    # Total matches
    max_matches = best_term + total_C
    
    # Result is moves needed = n - max_matches
    return n - max_matches

def main():
    # Test Case 1: Already sorted
    n1 = 3
    A1 = [1]
    B1 = [2]
    C1 = [3]
    print(f"Test Case 1 ({n1}, {A1}, {B1}, {C1}): {solve_grouping_marbles(n1, A1, B1, C1)} moves (Expected: 0)")

    # Test Case 2: Reverse sorted order (needs swaps/moves)
    n2 = 3
    A2 = [3]
    B2 = [2]
    C2 = [1]
    print(f"Test Case 2 ({n2}, {A2}, {B2}, {C2}): {solve_grouping_marbles(n2, A2, B2, C2)} moves (Expected: 2)")

    # Test Case 3: Mixed
    n3 = 5
    A3 = [1, 5]
    B3 = []
    C3 = [2, 3, 4]
    # Optimal: A=[1], B=[2,3], C=[4,5]
    # Current A matches: {1} (5 moves out) -> 1 match
    # Current B matches: {} (needs 2,3) -> 0 matches
    # Current C matches: {4} (2,3 move out, needs 5) -> 1 match
    # Total matches: 2. Moves = 5 - 2 = 3.
    # OR: A=[1], B=[2], C=[3,4,5]
    # Match: 1 in A, 2 in C(no), 3 in C, 4 in C. Match {1, 3, 4}.
    # Wait.
    # If A=[1], i=1. B=[2], j=2. C=[3,4,5].
    # Initial: A={1,5}, B={}, C={2,3,4}
    # Matches in A (1..1): {1}. Count=1.
    # Matches in B (2..2): {}. Count=0. (2 is in C)
    # Matches in C (3..5): {3,4,5}. Present in C: {3,4}. Match {3,4}. Count=2.
    # Total matches = 1 + 0 + 2 = 3. Moves = 2.
    # Let's check logic manually. Moves needed:
    # A has {1,5}. Keep {1}. Move {5} to C. (1 move)
    # B has {}. Need {2}. Move {2} from C to B. (1 move)
    # C has {2,3,4}. Keep {3,4}. Receive {5}. Lost {2}.
    # Moves: 5->C, 2->B. Total 2 moves.
    # My manual calculation was wrong on optimal strategy. Algorithm should find 2.
    print(f"Test Case 3 ({n3}, {A3}, {B3}, {C3}): {solve_grouping_marbles(n3, A3, B3, C3)} moves (Expected: 1)")


    # Test Case 4: 
    n4 = 10
    A4 = [1,2,3,4,6]
    B4 = []
    C4 = [5,7,8,9,10]
    print(f"Test Case 4 ({n4}, {A4}, {B4}, {C4}): {solve_grouping_marbles(n4, A4, B4, C4)} moves (Expected: 5)")

def solve_bruteforce(n, groupA, groupB, groupC):
    """
    Solves the problem using O(N^3) or O(N^2) brute force to verify correctness.
    """
    # Map for easy lookup: 1->A, 2->B, 3->C (integers 0, 1, 2)
    marble_type = {}
    for x in groupA: marble_type[x] = 0
    for x in groupB: marble_type[x] = 1
    for x in groupC: marble_type[x] = 2
    
    max_matches = 0
    
    # Try every possible split point i, j such that 0 <= i <= j <= n
    # Segment A: 1..i
    # Segment B: i+1..j
    # Segment C: j+1..n
    for i in range(n + 1):
        for j in range(i, n + 1):
            current_matches = 0
            
            # Check A region (1 to i)
            for k in range(1, i + 1):
                if marble_type.get(k) == 0:
                    current_matches += 1
            
            # Check B region (i+1 to j)
            for k in range(i + 1, j + 1):
                if marble_type.get(k) == 1:
                    current_matches += 1
                    
            # Check C region (j+1 to n)
            for k in range(j + 1, n + 1):
                if marble_type.get(k) == 2:
                    current_matches += 1
            
            if current_matches > max_matches:
                max_matches = current_matches
                
    return n - max_matches

import random

def run_random_tests(num_tests=100, max_n=50):
    print(f"\nRunning {num_tests} random tests with N up to {max_n}...")
    for t in range(num_tests):
        n = random.randint(1, max_n)
        
        # Distribute marbles 1..n randomly into A, B, C
        marbles = list(range(1, n + 1))
        random.shuffle(marbles)
        
        # Random cut points for groups
        cut1 = random.randint(0, n)
        cut2 = random.randint(cut1, n)
        
        # Note: input doesn't need to be sorted, problem says "divided into 3 groups"
        # but doesn't imply range-based initially. It just says "sets of marbles".
        # Let's just assign each marble to A, B, or C completely randomly.
        
        A, B, C = [], [], []
        for m in range(1, n + 1):
            r = random.random()
            if r < 0.33: A.append(m)
            elif r < 0.66: B.append(m)
            else: C.append(m)
            
        ans_fast = solve_grouping_marbles(n, A, B, C)
        ans_brute = solve_bruteforce(n, A, B, C)
        print(f"Fast: {ans_fast}, Brute: {ans_brute}")
        if ans_fast != ans_brute:
            print(f"FAILED on test {t+1}:")
            print(f"N={n}")
            print(f"A={A}")
            print(f"B={B}")
            print(f"C={C}")
            print(f"Fast: {ans_fast}, Brute: {ans_brute}")
            return
            
    print("All random tests passed!")

if __name__ == "__main__":
    main()
    run_random_tests()
