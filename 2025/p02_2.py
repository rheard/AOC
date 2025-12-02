# Step 1: Load data and format into data structure:
with open("p02.txt") as rb:
    ranges = [tuple(map(int, x.split('-'))) for x in rb.read().strip().split(",")]


# Step 2: Solve the problem
answer = 0
for start, stop in ranges:
    for i in range(start, stop + 1):
        i_str = str(i)
        for l in range(1, len(i_str) // 2 + 1):
            if len(i_str) % l != 0:
                continue  # Cannot be repeating of a length that won't repeat evenly
            chunks = {i_str[i:i+l] for i in range(0, len(i_str), l)}
            if len(chunks) == 1:
                answer += i
                break


# Step 3: Output answer
print(answer)
