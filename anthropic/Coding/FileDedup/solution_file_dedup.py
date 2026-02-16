import os
import hashlib
from collections import defaultdict
from typing import List, Dict

class FileDeduplicator:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir

    def get_all_files(self) -> List[str]:
        """
        Traverse directory using os.scandir (faster than os.walk).
        Returns a list of absolute file paths.
        """
        file_paths = []
        try:
            # Iterative BFS to avoid recursion depth issues
            queue = [self.root_dir]
            while queue:
                current_path = queue.pop(0)
                try:
                    with os.scandir(current_path) as it:
                        for entry in it:
                            if entry.is_file():
                                file_paths.append(entry.path)
                            elif entry.is_dir():
                                queue.append(entry.path)
                except PermissionError:
                    print(f"Permission denied: {current_path}")
                    continue
        except Exception as e:
            print(f"Error scanning directory: {e}")
        return file_paths

    def get_file_hash(self, file_path: str, partial: bool = False) -> str:
        """
        Compute SHA-256 hash.
        If partial=True, hash only the first 1KB (Fast check).
        If partial=False, stream the entire file (Collision check).
        """
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                if partial:
                    chunk = f.read(1024)
                    hasher.update(chunk)
                else:
                    # Stream in chunks to avoid loading large files into RAM
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        hasher.update(chunk)
        except OSError:
            return "" # Handle unreadable files
        return hasher.hexdigest()

    def find_duplicates(self) -> List[List[str]]:
        """
        Find duplicates using a multi-stage filtering approach (The "Funnel").
        1. Group by Size (O(1) stat call).
        2. Group by First 1KB Hash (Fast I/O).
        3. Group by Full Content Hash (Slow I/O).
        """
        all_files = self.get_all_files()
        
        # --- Stage 1: Group by Size ---
        size_map = defaultdict(list)
        for path in all_files:
            try:
                size = os.path.getsize(path)
                size_map[size].append(path)
            except OSError:
                continue
        
        # Filter: Keep only groups with >1 file
        candidates_by_size = [paths for paths in size_map.values() if len(paths) > 1]
        
        # --- Stage 2: Group by Partial Hash ---
        partial_hash_map = defaultdict(list)
        for group in candidates_by_size:
            for path in group:
                p_hash = self.get_file_hash(path, partial=True)
                if p_hash:
                    # Key: (Size, PartialHash) to be safe
                    # But since we iterate over size groups, just partial hash is fine strictly speaking?
                    # No, collisions across sizes possible if we just flattened.
                    # Safest: (Size, PartialHash) tuple as key
                    size = os.path.getsize(path) 
                    partial_hash_map[(size, p_hash)].append(path)
        
        candidates_by_partial = [paths for paths in partial_hash_map.values() if len(paths) > 1]
        
        # --- Stage 3: Group by Full Hash ---
        final_duplicates = []
        for group in candidates_by_partial:
            full_hash_map = defaultdict(list)
            for path in group:
                f_hash = self.get_file_hash(path, partial=False)
                if f_hash:
                    full_hash_map[f_hash].append(path)
            
            for paths in full_hash_map.values():
                if len(paths) > 1:
                    final_duplicates.append(paths)
                    
        return final_duplicates

if __name__ == "__main__":
    # --- Example usage with tempfile ---
    print("--- Running Example with Temp Dir ---")
    import tempfile
    
    # Create dummy env
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = os.path.join(tmpdir, "a.txt"); open(f1, "w").write("hello world")
        f2 = os.path.join(tmpdir, "b.txt"); open(f2, "w").write("hello world") # Duplicate
        f3 = os.path.join(tmpdir, "c.txt"); open(f3, "w").write("hello")       # Different
        f4 = os.path.join(tmpdir, "d.txt"); open(f4, "w").write("hello world") # Triplicate (nested)
        
        finder = FileDeduplicator(tmpdir)
        dups = finder.find_duplicates()
        
        print(f"Found {len(dups)} groups of duplicates in temp dir:")
        for group in dups:
            print(group)

    print("\n--- Running on User Directory ---")
    # user_requested_dir = r"C:\Users\Fred\Coding\python"
    target_dir = r"C:\Users\Fred\Coding\python"
    
    if os.path.exists(target_dir):
        print(f"Scanning {target_dir} for duplicates...")
        finder = FileDeduplicator(target_dir)
        try:
            dups = finder.find_duplicates()
            
            print(f"Found {len(dups)} groups of duplicates:")
            for i, group in enumerate(dups, 1):
                print(f"Group {i}:")
                for path in group:
                    print(f"  - {path}")
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print(f"Directory not found: {target_dir}")
