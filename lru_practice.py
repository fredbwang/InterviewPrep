import functools

print("=== 1. Standard lru_cache behavior with unhashable args ===")
try:
    @functools.lru_cache(maxsize=None)
    def standard_cache(x):
        return x

    # Bug: Passing a list (mutable) to lru_cache raises TypeError
    print(standard_cache([1, 2, 3]))
except TypeError as e:
    print(f"Caught expected error: {e}")

print("\n=== 2. Naive Implementation Bug: Unhashable kwargs ===")
def naive_lru(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # BUG: key = (args, kwargs)  <-- kwargs is a dict, unhashable
        # key = (args, kwargs) 
        # try:
        #     if key in cache: return cache[key]
        # except TypeError:
        #     pass 

        # Let's show the failure
        try:
            key = (args, kwargs) # This line doesn't fail, but putting it in dict might? 
            # Actually, just creating the tuple is fine.
            # Using it as a dict key fails.
            if key in cache:
                return cache[key]
        except TypeError as e:
            print(f"Naive wrapper failed: {e}")
            return func(*args, **kwargs)
            
        result = func(*args, **kwargs)
        try:
            cache[key] = result
        except TypeError:
            pass
        return result
    return wrapper

@naive_lru
def test_naive(a, b):
    print(f"Calculating {a} + {b}")
    return a + b

test_naive(a=1, b=2)
test_naive(a=1, b=2) # Should hit cache but fails to hash

print("\n=== 3. Better Implementation (Handling kwargs) ===")
def better_lru(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Fix 1: Convert kwargs to a sorted tuple of items to make it hashable
        # Sorting ensures f(a=1, b=2) and f(b=2, a=1) hit the same cache key
        frozen_kwargs = tuple(sorted(kwargs.items()))
        
        # Key includes args and the frozenset/tuple of kwargs
        key = (args, frozen_kwargs)
        
        if key in cache:
            print("Cache hit!")
            return cache[key]
            
        print("Cache miss - calculating...")
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    return wrapper

@better_lru
def test_improved(a, b):
    return a + b

test_improved(a=1, b=2)
test_improved(b=2, a=1) # Should be a hit because we sorted items

print("\n=== 4. The 'Argument Equivalence' Issue (args vs kwargs) ===")
# Even with sorted kwargs, f(1, 2) and f(a=1, b=2) are treated as different keys!
@better_lru
def test_mixed(a, b):
    print(f"Calculating mixed {a} + {b}")
    return a + b

print("Call 1: test_mixed(1, 2)")
test_mixed(1, 2)
print("Call 2: test_mixed(a=1, b=2)")
test_mixed(a=1, b=2) # This will be a MISS (re-calculates) because (1, 2) != ((), (('a', 1), ('b', 2))) behavior.

print("\n=== 5. Robust Implementation (Using inspect to handle args/kwargs matching) ===")
import inspect

def robust_lru(func):
    cache = {}
    
    # We need the signature to bind arguments
    sig = inspect.signature(func)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Bind arguments to parameter names
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults() # Fill in default values so f(1) matches f(1, b=default)
        
        # Now we have a canonical representation of arguments
        # bound_args.arguments is an OrderedDict
        # We need to make it hashable. We can convert it to tuple of sorted items (if keys matter) 
        # or just tuple of values if order is preserved by bind (it is ordered by signature).
        
        # However, argument values might still be unhashable (e.g. lists).
        # A robust solution would try to make them hashable or fail.
        
        # Create the key
        # We use tuple(bound_args.arguments.items()) to be safe and explicit
        key_items = tuple(bound_args.arguments.items())
        
        if key_items in cache:
            print("Robust Cache HIT!")
            return cache[key_items]
            
        print("Robust Cache MISS - Calculating...")
        result = func(*args, **kwargs) # Call original
        cache[key_items] = result
        return result
        
    return wrapper

@robust_lru
def test_robust(a, b=10):
    return a + b

print("\nTesting Robust Cache:")
print("1. test_robust(1, 2)")
test_robust(1, 2)

print("2. test_robust(a=1, b=2) [Should HIT]")
test_robust(a=1, b=2)

print("3. test_robust(1) [Should MISS new calculation (using default b=10)]")
test_robust(1)

print("4. test_robust(a=1) [Should HIT previous calculation for (1, 10)]")
test_robust(a=1)

print("\n=== Summary of Bugs demonstrated ===")
print("1. Unhashable kwargs: dicts cannot be dictionary keys.")
print("2. Kwargs order: {'a':1, 'b':2} != {'b':2, 'a':1} unless sorted.")
print("3. Argument aliasing: f(1, 2) != f(a=1, b=2) unless bound to signature.")

