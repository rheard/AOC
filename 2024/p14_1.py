import functools
import operator
import re

prod = lambda x: functools.reduce(operator.mul, x, 1)  # Like sum but for multiplication
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


def divide_points(points):
    """Part 2: Divides a list of (x, y) points into 4 quadrants based on the given max grid size"""
    mid_x, mid_y = GRID_X // 2, GRID_Y // 2

    top_left = []
    top_right = []
    bot_left = []
    bot_right = []

    for x, y in points:
        # Skip points in the central row or column (if there is one)
        if (GRID_X % 2 != 0 and x == mid_x) or (GRID_Y % 2 != 0 and y == mid_y):
            continue

        if x < mid_x and y < mid_y:
            top_left.append((x, y))
        elif x >= mid_x and y < mid_y:
            top_right.append((x, y))
        elif x < mid_x and y >= mid_y:
            bot_left.append((x, y))
        elif x >= mid_x and y >= mid_y:
            bot_right.append((x, y))

    return top_left, top_right, bot_left, bot_right


for _ in range(100):
    process_second(data)

quads = divide_points([r['p'] for r in data])
total = prod(len(q) for q in quads)
print(total)
