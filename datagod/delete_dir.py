# Given a API for file system
#
# Delete(path) -> bool: deletes the file or empty directory, returns false if deletion was not successful.
# isDirectory(path) -> bool: checks whether filepath is directory or not.
# GetAllFiles(path) -> List<string>: gets the absolute paths of all files in a directory, including other sub-directories.
# implement rm -rf.
#
# Follow up: prevents out of memory (OOM) error.
#
# Approaches:
#
# Created a simple recursive DFS approach.
# 1st improvement: deleted all files before call sub-directory recursively
# 2nd improvement: Instead of pushing the copy of the path into input, just update the path with relative file name.
# 3rd improvement: Implemented non-recursively and when the stack gets too large, save them to disk.
# The intviewer weren't too satisfied with my approaches.
# He was expecting some generator (yield) way to do it, but I wasn't sure how that exactly works.

from typing import List, Generator
from collections import deque

# Mock API functions for context (Since implementation is not provided, we pass)
def Delete(path: str) -> bool:
    """Deletes the file or empty directory, returns false if deletion was not successful."""
    # Implementation would go here
    print(f"Deleting: {path}")
    return True

def isDirectory(path: str) -> bool:
    """Checks whether filepath is directory or not."""
    # Implementation would go here
    return True # Mock return

def GetAllFiles(path: str) -> List[str]:
    """Gets the absolute paths of all files in a directory, including other sub-directories."""
    # Implementation would go here
    return [] # Mock return

def delete_dir_generator(root_path: str) -> Generator[str, None, None]:
    """
    Generator that yields paths to delete in post-order (children before parent).
    This iterative approach avoids recursion limitations (Stack Overflow) and 
    reduces memory overhead compared to storing a full list of descendants.
    """
    # If the root is not a directory (or doesn't exist), just yield it (Delete handles it)
    # However, strictly for 'rm -rf' logic on a file, we can just check isDirectory.
    if not isDirectory(root_path):
        yield root_path
        return

    # Stack stores tuples of (current_path, children_iterator)
    # Using an iterator prevents loading all future siblings into the stack logic,
    # though valid memory usage still depends on GetAllFiles returning a list.
    stack = [(root_path, iter(GetAllFiles(root_path)))]
    
    while stack:
        parent, children = stack[-1]
        
        try:
            child = next(children)
            
            if isDirectory(child):
                # If it's a directory, we must process its children first.
                # Push it to the stack to dive deeper.
                stack.append((child, iter(GetAllFiles(child))))
            else:
                # If it's a file, we can delete it immediately.
                yield child
        
        except StopIteration:
            # All children of the current directory have been processed.
            # Now safe to delete the directory itself.
            stack.pop()
            yield parent

def delete_dir(path: str) -> bool:
    """
    Implements rm -rf using the generator to delete files/directories safely.
    """
    success = True
    for target in delete_dir_generator(path):
        if not Delete(target):
            success = False
            # Option: break or continue? rm -rf usually continues.
            print(f"Failed to delete {target}")
    return success

# Example usage (commented out)
# if __name__ == "__main__":
#     delete_dir("/path/to/delete")

class Solution:
    def deleteAllFilesAndDir(self, path: str) -> None:
        folders = []
        queue = deque([path])

        while queue:
            top = queue.popleft()
            if isDirectory(top):
                folders.append(top)
                queue.extend(GetAllFiles(top))
            else:
                Delete(top)
            
        for folder in reversed(folders):
            Delete(folder)

    def deleteAllFilesAndDir_IterativeDFS(self, path: str) -> None:
        """
        Iterative DFS using an explicit stack to simulate recursion.
        This handles the OOM issue by only storing the current path from root to leaf
        (Memory: O(depth)) instead of all directories (Memory: O(N)).
        """
        if not isDirectory(path):
            Delete(path)
            return

        # Stack elements: (current_path, children_iterator)
        stack = [(path, iter(GetAllFiles(path)))]

        while stack:
            # Peek at the current directory we are processing
            parent, children_iter = stack[-1]

            try:
                # Get the next child for this directory
                child = next(children_iter)
                
                if isDirectory(child):
                    # If it's a directory, pause the current parent and 
                    # push the child onto the stack to process it first (DFS)
                    stack.append((child, iter(GetAllFiles(child))))
                else:
                    # If it's a file, delete it immediately
                    Delete(child)
            
            except StopIteration:
                # All children of this directory have been processed
                # We can now safely delete the directory itself
                stack.pop()
                Delete(parent)
