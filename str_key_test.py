import functools

def str_lru(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # The user suggested approach: stringify the sorted items AND args
        key = str(args) + str(sorted(kwargs.items()))
        
        if key in cache:
            # print(f"Cache HIT for key: {key}")
            return cache[key]
        
        # print(f"Cache MISS for key: {key}")
        result = func(*args, **kwargs)
        cache[key] = result
        return result
    return wrapper

@str_lru
def test_func(x):
    return f"Result: {x}"

print("=== 1. It 'works' for unhashable types (lists) ===")
print(test_func([1, 2]))
print(test_func([1, 2])) # Hit!

print("\n=== 2. The Danger: Repr Collision ===")
class BadRepr:
    def __repr__(self):
        return "1"

print(f"Calling with integer 1: {test_func(1)}")
print(f"Calling with BadRepr(): {test_func(BadRepr())}")
# Explain: str((1,)) is "(1,)" and str((BadRepr(),)) is also "(1,)"

print("\n=== 3. Correct Collision Handling (Repr includes type info usually) ===")
# But custom objects are risky if __repr__ is not unique
class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def __repr__(self):
        # Using a simplified repr for debugging/logging, but bad for caching
        return f"User({self.id})"

@str_lru
def process_user(u):
    return f"Processed {u.name}"

u1 = User(1, "Alice")
u2 = User(1, "Bob") # Same ID (for repr), different Name

print(f"User 1: {process_user(u1)}")
print(f"User 2: {process_user(u2)}") # FAIL: Returns Alice because User(1) == User(1) in string key
