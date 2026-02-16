class Solution:
    def solveDependency(self, arr: List[List[int]]) -> int:

        stack = []
        visited = set()

        depMap = {}

        for pair in arr:
            depMap[pair[0]] = pair[1]

        for i in range(len(arr)):
            if arr[i][0] not in visited:
                stack.append(arr[i][0])
                visited.add(arr[i][0])
            else:
                visited.add(arr[i][0])
        
        res = []
        while stack:
            res.append(stack.pop())
            
        return res
        
    def __init__(self):
        
        print(Solution().solveDependency([[1, 2], [2, 3], [3, 4], [1, 4]]))