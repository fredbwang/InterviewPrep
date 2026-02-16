from typing import List

class Node:
    def __init__(self, name: str, size: int = 0):
        self.name = name
        self.size = size  # 0 for directories, >0 for files
        self.children: List['Node'] = []

    def add_child(self, child: 'Node'):
        self.children.append(child)

def get_total_size(root: Node) -> int:
    """
    Calculates the total size of the filesystem tree starting from root.
    """
    # Sum the current node's size (0 for dirs, value for files)
    # plus the total size of all its children recursively.
    total = root.size
    for child in root.children:
        total += get_total_size(child)
    
    return total

# Test cases
if __name__ == "__main__":
    # stored in a tree:
    # root/ (0)
    #   file1 (100)
    #   file2 (200)
    #   sub/ (0)
    #     file3 (50)
    #     sub2/ (0)
    #       file4 (10)

    root = Node("root", 0)  # Directory
    
    f1 = Node("file1", 100)
    f2 = Node("file2", 200)
    
    sub = Node("sub", 0)    # Directory
    f3 = Node("file3", 50)
    
    sub2 = Node("sub2", 0)  # Directory
    f4 = Node("file4", 10)
    
    root.add_child(f1)
    root.add_child(f2)
    root.add_child(sub)
    
    sub.add_child(f3)
    sub.add_child(sub2)
    
    sub2.add_child(f4)
    
    print(f"Total size: {get_total_size(root)}")