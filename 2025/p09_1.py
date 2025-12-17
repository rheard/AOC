from itertools import combinations


# Step 1: Load data and format into data structure:
with open("p09.txt") as rb:
    points = [tuple(map(int, l.strip().split(','))) for l in rb.readlines()]


# Step 2: Solve the problem
answer = 0
for (x1, y1), (x2, y2) in combinations(points, 2):
    area = (x1 - x2 + 1) * (y1 - y2 + 1)
    if area > answer:
        answer = area


# Step 3: Output answer
print(answer)
