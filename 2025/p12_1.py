from collections import defaultdict


def count_fitting_regions(regions, areas) -> int:
    total_ok = 0

    for w, h, counts in regions:
        region_area = w * h
        required_area = sum(c * areas[i] for i, c in enumerate(counts))
        if required_area <= region_area:
            total_ok += 1

    return total_ok


# Step 1: Load data and format into data structure:
with open('p12.txt') as rb:
    lines = [l.strip() for l in rb.readlines()]
    regions_start = 0

    # region First loop, get package areas
    package_areas = defaultdict(int)  # index -> total '#' squares
    cur_package_index = None

    for regions_start, line in enumerate(lines):
        if not line:
            continue

        if 'x' in line:
            break

        if ":" in line:
            cur_package_index = int(line.split(":", 1)[0])
        else:
            package_areas[cur_package_index] += line.count("#")
    # endregion

    # region Second loop, parse regions
    regions = []

    for raw in lines[regions_start:]:
        line = raw.strip()
        if not line:
            continue

        # Format: "WxH: c0 c1 c2 ..."
        dims, rest = line.split(":", 1)
        w_str, h_str = dims.split("x")
        width = int(w_str)
        height = int(h_str)
        counts = [int(x) for x in rest.strip().split()]

        regions.append((width, height, counts))
    # endregion


# Step 2: Solve the problem
answer = count_fitting_regions(regions, package_areas)


# Step 3: Output answer
print(answer)
