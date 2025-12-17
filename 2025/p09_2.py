from collections import defaultdict
from itertools import combinations
from typing import List, Tuple

Point = Tuple[int, int]
Segment = Tuple[int, int, int]    # (x, y0, y1) with y0 <= y1 (or y,x0,x1 with x0 <= x1)


# Step 1: Load data and format into data structure:
with open("p09.txt") as rb:
    points: List[Point] = [tuple(map(int, line.strip().split(","))) for line in rb]

# Build perimeter segments
points_by_x = defaultdict(list)  # x -> list of y's
points_by_y = defaultdict(list)  # y -> list of x's

for x, y in points:
    points_by_x[x].append(y)
    points_by_y[y].append(x)

vertical_segs: List[Segment] = []
horizontal_segs: List[Segment] = []

# For each fixed x, pair up sorted y's: (y0,y1), (y2,y3), ...
for x, ys in points_by_x.items():
    ys_sorted = sorted(ys)
    for i in range(0, len(ys_sorted) // 2):
        y0 = ys_sorted[2 * i]
        y1 = ys_sorted[2 * i + 1]
        if y0 > y1:
            y0, y1 = y1, y0
        vertical_segs.append((x, y0, y1))

# For each fixed y, pair up sorted x's: (x0,x1), (x2,x3), ...
for y, xs in points_by_y.items():
    xs_sorted = sorted(xs)
    for i in range(0, len(xs_sorted) // 2):
        x0 = xs_sorted[2 * i]
        x1 = xs_sorted[2 * i + 1]
        if x0 > x1:
            x0, x1 = x1, x0
        horizontal_segs.append((y, x0, x1))


# Step 2: Solve the problem
def segment_overlaps(seg0: int, seg1: int, open_lo: int, open_hi: int) -> bool:
    """Returns True if the closed segment [seg0, seg1] overlaps the open interval (open_lo, open_hi)."""
    if seg0 > seg1:
        seg0, seg1 = seg1, seg0
    return seg0 < open_hi and seg1 > open_lo


def rectangle_is_clear(minx: int, miny: int, maxx: int, maxy: int) -> bool:
    """A rectangle is 'valid' if no perimeter segment passes through its interior"""
    # Check vertical perimeter segments
    for x, y0, y1 in vertical_segs:
        if minx < x < maxx:
            if segment_overlaps(y0, y1, miny, maxy):
                return False

    # Check horizontal perimeter segments
    for y, x0, x1 in horizontal_segs:
        if miny < y < maxy:
            if segment_overlaps(x0, x1, minx, maxx):
                return False

    return True


# Search best rectangle
answer = 0
for (x1, y1), (x2, y2) in combinations(points, 2):
    minx, maxx = (x1, x2) if x1 <= x2 else (x2, x1)
    miny, maxy = (y1, y2) if y1 <= y2 else (y2, y1)

    if not rectangle_is_clear(minx, miny, maxx, maxy):
        continue

    area = (maxx - minx + 1) * (maxy - miny + 1)
    if area > answer:
        answer = area


# Step 3: Output answer
print(answer)
