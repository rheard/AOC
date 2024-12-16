import re

from itertools import count

GRID_X = 101
GRID_Y = 103

# Step 1: Load data
data_pattern = re.compile(r"p=(-?\d+),(-?\d+)\s+v=(-?\d+),(-?\d+)")
data = []

with open('p14.txt', 'r') as file:
    for line in file:
        match = data_pattern.search(line)
        if not match:
            continue
        px, py, vx, vy = map(int, match.groups())
        data.append({'p': [px, py], 'v': [vx, vy]})


# Step 2: Solve the problem
def process_second(robots):
    for r in robots:
        r['p'][0] += r['v'][0]
        r['p'][0] %= GRID_X

        r['p'][1] += r['v'][1]
        r['p'][1] %= GRID_Y


# Step 2: Solve the problem
for i in count(0):
    # Create an empty grid filled with dots
    grid = [['.' for _ in range(GRID_X)] for _ in range(GRID_Y)]

    # Place points on the grid
    for r in data:
        x, y = r['p']
        grid[y][x] = 'X'  # Mark the point with an X

    # 12 in a row seems reasonable enough to be statistically significant?    EDIT: Yup, that works :)
    if any('XXXXXXXXXXXX' in ''.join(row) for row in grid):
        # Print the grid
        print(f"Seconds passed: {i}")
        for row in grid:
            print(''.join(row))
        break

    process_second(data)
