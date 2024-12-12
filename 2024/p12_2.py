from dataclasses import dataclass, field
from collections import defaultdict

# Step 1: Load data
with open('p12.txt') as rb:
    data = [list(l.strip()) for l in rb]


def count_sections(points, vertical: bool):
    """
    Counts continuous sections of points in a specific direction (horizontal or vertical).

    Args:
        points (list of tuples): A list of (x, y) points.
        vertical (bool): If True, count sections vertically; otherwise, horizontally.

    Returns:
        int: The number of continuous sections in the specified direction.
    """
    # Organize points by rows or columns based on the direction
    organized = {}
    for dx, dy in points:
        key = dy if vertical else dx
        if key not in organized:
            organized[key] = []
        organized[key].append(dx if vertical else dy)

    # Count continuous sections
    section_count = 0
    for key, values in organized.items():
        values.sort()  # Sort values to process in order
        previous = None
        for value in values:
            if previous is None or value != previous + 1:
                section_count += 1
            previous = value

    return section_count


# Step 2: Solve the problem
@dataclass
class Region:
    points: set = field(default_factory=set)
    perimeter: dict = field(default_factory=lambda: defaultdict(set))  # side -> points with that side as an edge

    @property
    def area(self):
        return len(self.points)

    @property
    def sides(self):
        return sum(count_sections(points, d in ['b', 't']) for d, points in self.perimeter.items())

    @property
    def total_price(self):
        return self.area * self.sides


regions = list()
def crawl_region(dataset, start_x, start_y):
    r = Region()
    start_plant = dataset[start_y][start_x]
    pos_to_process = [(start_x, start_y)]

    while pos_to_process:
        pos_x, pos_y = pos_to_process.pop()

        if (pos_x, pos_y) in r.points:
            continue

        r.points.add((pos_x, pos_y))

        near_positions = {
            'l': (pos_x - 1, pos_y),  # Left
            'r': (pos_x + 1, pos_y),  # Right
            'b': (pos_x, pos_y - 1),  # Bottom
            't': (pos_x, pos_y + 1),  # Top
        }

        for side, (target_x, target_y) in near_positions.items():
            if (target_x, target_y) in r.points:
                continue

            if target_x < 0 or target_y < 0 or target_x >= len(dataset[0]) or target_y >= len(dataset):
                r.perimeter[side].add((pos_x, pos_y))
                continue

            if dataset[target_y][target_x] != start_plant:
                r.perimeter[side].add((pos_x, pos_y))  # Not the right plant type!
                continue

            pos_to_process.append((target_x, target_y))

    return r


for y in range(len(data)):
    for x in range(len(data[0])):
        if not any((x, y) in r.points for r in regions):
            regions.append(crawl_region(data, x, y))

print(sum(r.total_price for r in regions))
