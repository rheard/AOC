from dataclasses import dataclass, field

# Step 1: Load data
with open('p12.txt') as rb:
    data = [list(l.strip()) for l in rb]


# Step 2: Solve the problem
@dataclass
class Region:
    points: set = field(default_factory=set)
    perimeter: int = 0
    
    @property
    def area(self):
        return len(self.points)
    
    @property
    def total_price(self):
        return self.area * self.perimeter


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

        near_positions = [
            (pos_x - 1, pos_y),
            (pos_x + 1, pos_y),
            (pos_x, pos_y - 1),
            (pos_x, pos_y + 1)
        ]

        for target_x, target_y in near_positions:
            if (target_x, target_y) in r.points:
                continue

            if target_x < 0 or target_y < 0 or target_x >= len(dataset[0]) or target_y >= len(dataset):
                r.perimeter += 1
                continue

            if dataset[target_y][target_x] != start_plant:
                r.perimeter += 1  # Not the right plant type!
                continue

            pos_to_process.append((target_x, target_y))

    return r


for y in range(len(data)):
    for x in range(len(data[0])):
        if not any((x, y) in r.points for r in regions):
            regions.append(crawl_region(data, x, y))

print(sum(r.total_price for r in regions))
