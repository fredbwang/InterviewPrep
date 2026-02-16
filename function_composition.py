import math
from typing import List, Union, Callable, Any

Number = Union[int, float]
InputType = Union[Number, List[Number]]

def compose(*functions: Callable):
    """
    Takes an arbitrary number of functions as arguments and returns a new function
    representing their composition. The arguments are passed to the first function,
    its output to the second, and so on.
    """
    def composed_function(*args: Any) -> Any:
        if not functions:
            return args[0] if len(args) == 1 else args
        
        # Apply the first function to the initial arguments.
        # This handles the case where the first function takes *args (like add).
        result = functions[0](*args)
        
        # Apply the remaining functions strictly to the result of the previous one
        for func in functions[1:]:
            result = func(result)
            
        return result
    
    return composed_function

def add(*args: Number) -> Number:
    """
    Takes a variable number of arguments and returns the sum of the arguments.
    """
    return sum(args)

def square(a: InputType) -> InputType:
    """
    Takes a number or list of numbers as an argument and returns the square of
    (each element in) a.
    """
    if isinstance(a, list):
        return [x * x for x in a]
    return a * a

def splitter(a: InputType) -> List[Number]:
    """
    Takes a number as an argument, divides the number by 2, and returns a list
    of length 2: [floor of division, value - floor of division].
    If a is a list, splitter() concatenates the output of the other lists.
    """
    # Helper for a single number
    def split_single(n: Number) -> List[Number]:
        floor_val = n // 2
        return [floor_val, n - floor_val]

    if isinstance(a, list):
        result = []
        for item in a:
            result.extend(split_single(item))
        return result
    
    return split_single(a)

def my_max(a: InputType) -> Number:
    """
    Takes a number or list of numbers as an argument and returns the maximum value.
    """
    if isinstance(a, list):
        return max(a)
    return a

def my_min(a: InputType) -> Number:
    """
    Takes a number or list of numbers as an argument and returns the minimum value.
    """
    if isinstance(a, list):
        return min(a)
    return a

if __name__ == "__main__":
    # Test based on description
    
    # 1. add(*args) -> sum
    # 2. square(sum) -> sum^2
    # 3. splitter(sum^2) -> [floor(sum^2/2), sum^2 - floor(sum^2/2)]
    # 4. my_max(list) -> max element
    
    # Example 1: add(1, 2) = 3 -> square(3) = 9 -> splitter(9) = [4, 5] -> my_max([4, 5]) = 5
    print("Testing compose(add, square, splitter, my_max)(1, 2)")
    f1 = compose(add, square, splitter, my_max)
    result1 = f1(1, 2)
    print(f"Result: {result1}") 
    
    # Example 2: square([2, 3]) -> [4, 9] -> splitter([4, 9]) -> [2, 2, 4, 5] -> my_min(...) -> 2
    # Note: compose functions must handle list inputs if previous function returns list
    print("\nTesting compose(square, splitter, my_min)([2, 3])")
    # Using lambda wrapper for first func because square implies single arg 'a', but compose passes *args.
    # However, Python handles *args passed to function with one arg 'a' as error unless handled.
    # The problem description says "The arguments given to the function returned by compose are passed to functionsList[1]".
    # This implies functionsList[1] handles *args or the caller must pass arguments compatible with functionsList[1].
    # But square(a) takes one argument.
    # If the user calls f(2, 3), that is 2 arguments. If f is composed starting with square, it needs to handle *args?
    # Actually, square(a) is defined to take "a number or list".
    # If we call composed_f(1), then *args is (1,). We unpack it to square(1). Working.
    
    f2 = compose(square, splitter, my_min)
    # Passing single list as argument
    result2 = f2([2, 3]) 
    print(f"Result: {result2}")

    # Example 3: Floats
    # add(1.5, 2.5) -> 4.0 -> square(4.0) -> 16.0
    print("\nTesting compose(add, square)(1.5, 2.5) with floats")
    f3 = compose(add, square)
    result3 = f3(1.5, 2.5)
    print(f"Result: {result3}")

    # Example 4: Negatives
    # add(-5, -5) -> -10 -> splitter(-10) -> [-5, -5]
    print("\nTesting compose(add, splitter)(-5, -5) with negatives")
    f4 = compose(add, splitter)
    result4 = f4(-5, -5)
    print(f"Result: {result4}")

    # Example 5: Single Function
    # add(10, 20) -> 30
    print("\nTesting compose(add)(10, 20) single function")
    f5 = compose(add)
    result5 = f5(10, 20)
    print(f"Result: {result5}")
    
    # Example 6: Complex Chain
    # add(2, 3) -> 5
    # square(5) -> 25
    # splitter(25) -> [12, 13]
    # square([12, 13]) -> [144, 169]
    # my_max([144, 169]) -> 169
    print("\nTesting compose(add, square, splitter, square, my_max)(2, 3)")
    f6 = compose(add, square, splitter, square, my_max)
    result6 = f6(2, 3)
    print(f"Result: {result6}")
