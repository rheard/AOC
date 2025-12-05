def collapse_ranges(ranges):
    """Given a list of (start, stop) ranges, return a new list with all overlapping (or touching) ranges merged"""
    # Sort by start position
    ranges = sorted(ranges, key=lambda r: r[0])

    cur_start, cur_end = ranges[0]

    for start, end in ranges[1:]:
        # If this range overlaps or touches the current one, merge them
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            yield cur_start, cur_end
            cur_start, cur_end = start, end

    yield cur_start, cur_end


# Step 1: Load data and format into data structure:
with open("p05.txt") as rb:
    ranges = []
    possible_ids = []

    for line in rb.readlines():
        l = line.strip()
        if not l:
            break

        entry = l.split('-')
        ranges.append(tuple(map(int, entry)))


# Step 2: Solve the problem
answer = 0
for start, stop in collapse_ranges(ranges):
    answer += stop - start + 1


# Step 3: Output answer
print(answer)
