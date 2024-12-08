from collections import defaultdict
from itertools import count

# Step 1: Load data
with open('p08.txt') as rb:
    data = [list(l.strip()) for l in rb]

antennas = defaultdict(list)

for y, r in enumerate(data):
    for x, loc in enumerate(r):
        if loc == '.':
            continue
        antennas[loc].append((x, y))


# Step 2: Solve the problem
def find_anti_nodes(points, max_x, max_y):
    anti_nodes = set()

    # Either do 2 directions for each pair, and limit the pairs,
    #   or do every pair and 1 direction each... thats easier
    for i, (x1, y1) in enumerate(points):
        for j, (x2, y2) in enumerate(points):
            if i == j:  # Avoid comparing the point with itself
                continue

            # Calculate difference
            mx, my = x1 - x2, y1 - y2

            for k in count(0):
                # Calculate the anti-node for x1, y1 relative to x2, y2
                anti_x, anti_y = x1 + mx * k, y1 + my * k

                # Add anti-node
                if int(anti_x) >= max_x or int(anti_y) >= max_y or anti_x < 0 or anti_y < 0:
                    break
                anti_nodes.add((int(anti_x), int(anti_y)))

    return anti_nodes


antinode_locations = set()
for antenna_type, locations in antennas.items():
    for antinode in find_anti_nodes(locations, len(data[0]), len(data)):
        antinode_locations.add(antinode)


print(len(antinode_locations))