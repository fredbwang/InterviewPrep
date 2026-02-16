
data = "hello world"
idx = 0
space_left = 100  # much larger than length of "hello world"

chunk = data[idx : idx + space_left]

print(f"Data length: {len(data)}")
print(f"Requested slice end: {idx + space_left}")
print(f"Actual chunk: '{chunk}'")
print(f"Chunk length: {len(chunk)}")
