from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import argparse
import re
from typing import List, Tuple, Dict, Optional
import multiprocessing as mp

# Globals set once per worker process
_G_SHAPES = None  # type: ignore
Coord = Tuple[int, int]


def _init_worker(shapes):
    """Pool initializer: store shapes in a process-global variable."""
    global _G_SHAPES
    _G_SHAPES = shapes


def _region_worker(args) -> int:
    """
    Worker: returns 1 if region is solvable, else 0.
    args is (w, h, counts_tuple)
    """
    w, h, counts = args
    # _G_SHAPES is set by _init_worker
    ok = can_region_fit(w, h, _G_SHAPES, list(counts))
    return 1 if ok else 0


@dataclass
class Shape:
    """Represents a present shape as a list of unique orientations."""
    orientations: List[List[Coord]]  # each orientation is list of (x,y) with (0,0) top-left


def parse_input(text: str) -> Tuple[List[Shape], List[Tuple[int, int, List[int]]]]:
    """
    Parse the puzzle input.

    Returns:
        shapes: list of Shape in index order (0, 1, 2, ...)
        regions: list of (width, height, counts) where counts is a list[int] matching shapes
    """
    lines = [line.rstrip("\n") for line in text.splitlines()]
    i = 0
    n = len(lines)

    shape_dict: Dict[int, Shape] = {}

    # --- Helpers for detecting lines ---
    shape_header_re = re.compile(r"^(\d+):\s*$")
    region_header_re = re.compile(r"^(\d+)x(\d+):\s*(.*)$")

    # --- Parse shapes ---
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Region section starts here.
        if region_header_re.match(line):
            break

        m = shape_header_re.match(line)
        if not m:
            raise ValueError(f"Unexpected line while parsing shapes: {line!r}")
        idx = int(m.group(1))
        i += 1

        # Collect grid rows until blank or next header (shape or region).
        grid_rows: List[str] = []
        while i < n:
            next_line = lines[i]
            stripped = next_line.strip()
            if not stripped:
                i += 1
                break
            if shape_header_re.match(stripped) or region_header_re.match(stripped):
                break
            grid_rows.append(stripped)
            i += 1

        shape_dict[idx] = Shape(orientations=generate_orientations_from_grid(grid_rows))

    # Reorder shapes by index 0..max
    if not shape_dict:
        raise ValueError("No shapes parsed")
    max_idx = max(shape_dict.keys())
    shapes: List[Shape] = [shape_dict[i] for i in range(max_idx + 1)]

    # --- Parse regions ---
    regions: List[Tuple[int, int, List[int]]] = []
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        m = region_header_re.match(line)
        if not m:
            raise ValueError(f"Unexpected line while parsing regions: {line!r}")
        w = int(m.group(1))
        h = int(m.group(2))
        rest = m.group(3).strip()
        counts = [int(x) for x in rest.split()] if rest else []
        # Pad counts if shorter than shapes; AoC-style input should match exactly though.
        if len(counts) < len(shapes):
            counts += [0] * (len(shapes) - len(counts))
        regions.append((w, h, counts))

    return shapes, regions


def generate_orientations_from_grid(grid: List[str]) -> List[List[Coord]]:
    """Take list of strings with '#' and '.' and generate unique oriented polyominoes."""
    base_cells: List[Coord] = []
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "#":
                base_cells.append((x, y))
    if not base_cells:
        raise ValueError("Shape with no '#' cells")

    # Normalize base shape to top-left (0,0)
    base_cells = normalize_cells(base_cells)

    return generate_unique_orientations(base_cells)


def normalize_cells(cells: List[Coord]) -> List[Coord]:
    """Translate cells so that min x,y is (0,0) and sort them."""
    min_x = min(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    norm = sorted((x - min_x, y - min_y) for x, y in cells)
    return norm


def generate_unique_orientations(base_cells: List[Coord]) -> List[List[Coord]]:
    """
    Generate up to 8 unique orientations (4 rotations × flip/no-flip).
    Deduplicate symmetric ones.
    """
    seen = set()
    orientations: List[List[Coord]] = []

    for rot in range(4):
        for flip in (False, True):
            transformed: List[Coord] = []
            for x, y in base_cells:
                # rotate 90° rot times
                xx, yy = x, y
                for _ in range(rot):
                    xx, yy = -yy, xx
                # optional horizontal flip
                if flip:
                    xx = -xx
                transformed.append((xx, yy))
            norm = tuple(normalize_cells(transformed))
            if norm not in seen:
                seen.add(norm)
                orientations.append(list(norm))

    return orientations


def precompute_placements_for_region(
    width: int, height: int, shapes: List[Shape], counts: List[int]
) -> Tuple[List[List[int]], List[int], int]:
    """
    For a given region (width x height), precompute all possible placements for each shape.

    Returns:
        placements_by_shape: list[ list[int_bitmask] ] aligned with shapes
        shape_areas: list[int] number of '#' cells per shape
        total_cells_needed: total '#' cells needed across all requested presents
    """
    placements_by_shape: List[List[int]] = []
    shape_areas: List[int] = []
    total_cells_needed = 0

    board_size = width * height

    for i, shape in enumerate(shapes):
        if not shape.orientations:
            raise ValueError("Shape has no orientations")

        # All orientations have same number of cells
        area = len(shape.orientations[0])
        shape_areas.append(area)
        total_cells_needed += counts[i] * area

        if counts[i] == 0:
            placements_by_shape.append([])
            continue

        shape_masks: List[int] = []

        for ori in shape.orientations:
            # dimensions of this orientation
            max_x = max(x for x, _ in ori)
            max_y = max(y for _, y in ori)
            shape_w = max_x + 1
            shape_h = max_y + 1

            if shape_w > width or shape_h > height:
                continue

            # Try placing at every valid top-left
            for oy in range(height - shape_h + 1):
                base_row = oy * width
                for ox in range(width - shape_w + 1):
                    mask = 0
                    for sx, sy in ori:
                        idx = (oy + sy) * width + (ox + sx)
                        mask |= 1 << idx
                    shape_masks.append(mask)

        if counts[i] > 0 and not shape_masks:
            # This shape can't fit in this region at all.
            placements_by_shape.append([])
        else:
            placements_by_shape.append(shape_masks)

    # Quick impossible check: total required area can't exceed board area
    if total_cells_needed > width * height:
        # Mark by leaving placements as-is but with zero total_cells_needed for early failure.
        # We'll handle this in can_region_fit.
        pass

    return placements_by_shape, shape_areas, total_cells_needed


def can_region_fit(width: int, height: int, shapes: List[Shape], counts: List[int]) -> bool:
    """Return True if all requested presents can fit into this region."""
    placements_by_shape, shape_areas, total_cells_needed = precompute_placements_for_region(
        width, height, shapes, counts
    )
    board_size = width * height

    # If total required cells > board area, impossible.
    if total_cells_needed > board_size:
        return False

    # Build list of individual present instances (shape indices),
    # and order them to make search easier (biggest / most constrained first).
    instances: List[int] = []
    for i, c in enumerate(counts):
        instances.extend([i] * c)

    if not instances:
        # No presents to place, trivially fits.
        return True

    # Sort by (-area, number_of_placements) descending area & more constrained first
    instances.sort(
        key=lambda s_idx: (shape_areas[s_idx], len(placements_by_shape[s_idx])),
        reverse=True,
    )

    # Precompute remaining total area for each suffix of instances
    suffix_area: List[int] = [0] * (len(instances) + 1)
    for i in range(len(instances) - 1, -1, -1):
        suffix_area[i] = suffix_area[i + 1] + shape_areas[instances[i]]

    @lru_cache(maxsize=None)
    def dfs(instance_idx: int, used_mask: int) -> bool:
        """
        Backtracking search: place instance instance_idx onward.
        used_mask has bits set where they've been occupied (# cells).
        """
        if instance_idx == len(instances):
            return True

        # Prune by area: remaining required cells must fit in free cells.
        used_cells = used_mask.bit_count()
        free_cells = board_size - used_cells
        if suffix_area[instance_idx] > free_cells:
            return False

        s_idx = instances[instance_idx]
        placements = placements_by_shape[s_idx]
        if not placements:
            # No way to place this shape at all.
            return False

        for mask in placements:
            if mask & used_mask:
                continue
            if dfs(instance_idx + 1, used_mask | mask):
                return True

        return False

    return dfs(0, 0)


def count_fitting_regions(text: str) -> int:
    """High-level function: parse input and count how many regions are solvable."""
    shapes, regions = parse_input(text)
    count = 0
    for (w, h, counts) in regions:
        if can_region_fit(w, h, shapes, counts):
            count += 1
    return count


def count_fitting_regions_parallel(
    text: str,
    jobs: Optional[int] = None,
    chunksize: int = 1,
) -> int:
    """
    Parallel count: dispatch each region to a worker process.

    Args:
        text: full puzzle input
        jobs: number of processes (None -> mp.cpu_count())
        chunksize: Pool chunk size (tune: 1-8 is usually fine)

    Returns:
        number of regions that can fit all presents
    """
    # If only 1 job, keep it simple and avoid Pool overhead
    if jobs == 1:
        return count_fitting_regions(text)

    shapes, regions = parse_input(text)

    # Convert counts to tuple so it's cheap to send / hash / reuse
    work = [(w, h, tuple(counts)) for (w, h, counts) in regions]

    with mp.Pool(processes=jobs, initializer=_init_worker, initargs=(shapes,)) as pool:
        return sum(pool.imap_unordered(_region_worker, work, chunksize=chunksize))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, default="p12.txt",
                        help="Input file to run against.")
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help="Number of worker processes (default: CPU count). Use 1 to disable multiprocessing.")
    parser.add_argument("--chunksize", type=int, default=1,
                        help="Pool chunksize. Try 2, 4, or 8 if you have many regions.")
    args = parser.parse_args()

    with open(args.file) as rb:
        puzzle_input = rb.read()

    print(count_fitting_regions_parallel(puzzle_input, jobs=args.jobs, chunksize=args.chunksize))
