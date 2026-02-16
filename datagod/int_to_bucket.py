from collections import defaultdict

def bucket_counter(nums, num_buckets, bucket_width):

    buckets = defaultdict(list)

    for num in nums:
        bucketIdx = num // bucket_width

        if bucketIdx >= num_buckets:
            bucketIdx = num_buckets - 1

        buckets[bucketIdx].append(num)

    
    for idx, bucket in buckets.items():
        print(f"{idx * bucket_width}-{(idx + 1) * bucket_width - 1}: {len(bucket)} ({bucket})")

    return buckets

# def bucket_counter(nums, num_buckets, bucket_width):
#     """
#     Groups integers into buckets based on a specified bucket width and counts the number of elements in each bucket.

#     Args:
#         nums (list of int): List of integers to be categorized into buckets.
#         num_buckets (int): The number of buckets.
#         bucket_width (int): The width of each bucket.

#     Returns:
#         str: A formatted string displaying the count and elements in each bucket.
#     """

#     # Dictionary to store the count of numbers in each bucket
#     # bucket_counts = defaultdict(int)
#     # Dictionary to store the actual numbers in each bucket
#     buckets = defaultdict(list)

#     # Iterate through each number in the input list
#     for num in nums:
#         # Determine the bucket index using integer division
#         bucket_idx = num // bucket_width  
#         # If the calculated index exceeds the last valid bucket index, place it in the last bucket
#         if bucket_idx >= num_buckets - 1:
#             bucket_idx = num_buckets - 1  
#         # Increment the count of numbers in the corresponding bucket
#         # bucket_counts[bucket_idx] += 1
#         # Store the number in the corresponding bucket list
#         buckets[bucket_idx].append(num)

#     # Construct the result output
#     result = []
#     for i in range(num_buckets - 1):
#         # Format the range of the current bucket and append the count and contents
#         result.append(f"{i * bucket_width}-{(i+1) * bucket_width - 1}: {len(buckets[i])} ({buckets[i]})")

#     # Handle the last bucket which includes all numbers beyond its starting boundary
#     result.append(f"{(num_buckets - 1) * bucket_width}+: {len(buckets[num_buckets - 1])} ({buckets[num_buckets - 1]})")
   
#     # Join the results into a single formatted string
#     return "\n".join(result)

# Test case
nums = [1, 2, 11, 20, 100]
num_buckets = 3
bucket_width = 9
"""
Expected Output:
0-9: 2 ([1, 2])
10-19: 1 ([11])
20+: 2 ([20, 100])
"""
print(bucket_counter(nums, num_buckets, bucket_width))