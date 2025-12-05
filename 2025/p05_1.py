# Step 1: Load data and format into data structure:
with open("p05.txt") as rb:
    ranges = []
    possible_ids = []

    ranges_loading = True
    for line in rb.readlines():
        l = line.strip()
        if not l:
            ranges_loading = False
            continue

        if ranges_loading:
            entry = l.split('-')
            ranges.append(tuple(map(int, entry)))

        else:
            possible_ids.append(int(l))


# Step 2: Solve the problem
answer = 0
for entry in possible_ids:
    for start, stop in ranges:
        if start <= entry <= stop:
            answer += 1
            break


# Step 3: Output answer
print(answer)
