from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List, Optional, Tuple
import re

from manim import (
    Scene, VGroup, Square, Text, Line, SurroundingRectangle,
    FadeIn, FadeOut, Create, Indicate, Circumscribe,
    LEFT, RIGHT, UP, DOWN,
    WHITE, BLACK, GREY_B, GREY_E, BLUE_C,
    RED, GREEN, YELLOW, BLUE, ORANGE, PURPLE, TEAL
)

Coord = Tuple[int, int]


# =========================
# Parsing + shape geometry
# =========================

@dataclass(frozen=True)
class Orientation:
    cells: Tuple[Coord, ...]  # (x,y) with min corner at (0,0)
    w: int
    h: int


@dataclass(frozen=True)
class Shape:
    orientations: Tuple[Orientation, ...]


def normalize_cells(cells: Iterable[Coord]) -> Tuple[Coord, ...]:
    xs = [x for x, _ in cells]
    ys = [y for _, y in cells]
    min_x, min_y = min(xs), min(ys)
    norm = sorted((x - min_x, y - min_y) for x, y in cells)
    return tuple(norm)


def build_orientation(cells: Iterable[Coord]) -> Orientation:
    norm = normalize_cells(cells)
    max_x = max(x for x, _ in norm)
    max_y = max(y for _, y in norm)
    return Orientation(cells=norm, w=max_x + 1, h=max_y + 1)


def generate_unique_orientations(base_cells: List[Coord]) -> Shape:
    """
    Generate up to 8 unique orientations (4 rotations x optional mirror).
    """
    base = list(normalize_cells(base_cells))
    seen = set()
    out: List[Orientation] = []

    for rot in range(4):
        for flip in (False, True):
            transformed = []
            for x, y in base:
                xx, yy = x, y
                # rotate around origin
                for _ in range(rot):
                    xx, yy = -yy, xx
                # mirror horizontally
                if flip:
                    xx = -xx
                transformed.append((xx, yy))
            key = normalize_cells(transformed)
            if key in seen:
                continue
            seen.add(key)
            out.append(build_orientation(key))

    return Shape(orientations=tuple(out))


def parse_input(text: str) -> Tuple[List[Shape], List[Tuple[int, int, List[int]]]]:
    """
    Format:
      <idx>:
      ###...
      ...
      (blank lines)
      WxH: c0 c1 c2 ...
    """
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    i = 0
    n = len(lines)

    shape_header = re.compile(r"^(\d+):\s*$")
    region_header = re.compile(r"^(\d+)x(\d+):\s*(.*)$")

    shapes_map: Dict[int, Shape] = {}

    # Parse shapes until first region line
    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if region_header.match(line):
            break

        m = shape_header.match(line)
        if not m:
            raise ValueError(f"Unexpected line in shapes section: {line!r}")
        idx = int(m.group(1))
        i += 1

        grid: List[str] = []
        while i < n:
            ln = lines[i].strip()
            if not ln:
                i += 1
                break
            if shape_header.match(ln) or region_header.match(ln):
                break
            grid.append(ln)
            i += 1

        cells: List[Coord] = []
        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                if ch == "#":
                    cells.append((x, y))
        if not cells:
            raise ValueError(f"Shape {idx} has no '#' cells")

        shapes_map[idx] = generate_unique_orientations(cells)

    if not shapes_map:
        raise ValueError("No shapes parsed")
    max_idx = max(shapes_map.keys())
    shapes = [shapes_map[j] for j in range(max_idx + 1)]

    # Parse regions
    regions: List[Tuple[int, int, List[int]]] = []
    while i < n:
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        m = region_header.match(line)
        if not m:
            raise ValueError(f"Unexpected line in regions section: {line!r}")

        w = int(m.group(1))
        h = int(m.group(2))
        counts = [int(x) for x in m.group(3).split()] if m.group(3).strip() else []
        if len(counts) < len(shapes):
            counts += [0] * (len(shapes) - len(counts))
        regions.append((w, h, counts))

    return shapes, regions


# =========================
# Solver trace (the “animation script”)
# =========================

@dataclass(frozen=True)
class Placement:
    mask: int
    indices: Tuple[int, ...]  # board indices (y*w + x)
    shape_idx: int


def precompute_placements(width: int, height: int, shapes: List[Shape], counts: List[int]) -> List[List[Placement]]:
    placements_by_shape: List[List[Placement]] = []
    for s_idx, shape in enumerate(shapes):
        if counts[s_idx] == 0:
            placements_by_shape.append([])
            continue

        plist: List[Placement] = []
        for ori in shape.orientations:
            if ori.w > width or ori.h > height:
                continue
            for oy in range(height - ori.h + 1):
                for ox in range(width - ori.w + 1):
                    mask = 0
                    inds = []
                    for sx, sy in ori.cells:
                        x = ox + sx
                        y = oy + sy
                        idx = y * width + x
                        mask |= 1 << idx
                        inds.append(idx)
                    plist.append(Placement(mask=mask, indices=tuple(inds), shape_idx=s_idx))

        placements_by_shape.append(plist)
    return placements_by_shape


def shape_area(shape: Shape) -> int:
    return len(shape.orientations[0].cells)


def solve_with_trace(
    width: int,
    height: int,
    shapes: List[Shape],
    counts: List[int],
    *,
    step_limit: int = 2500,
    oob_padding: int = 1,          # how far outside to "try" for animation
    show_every_try: int = 1,       # 1 = show all tries, 5 = show 1/5 tries, etc.
) -> Generator[Tuple[str, dict], None, bool]:
    """
    Events:
      - focus_piece: {"instance_i": int, "shape_idx": int}
      - try_oob: {"coords": tuple[(x,y)...], "shape_idx": int}
      - try_overlap: {"coords": tuple[(x,y)...], "shape_idx": int}
      - try_ok: {"coords": tuple[(x,y)...], "shape_idx": int}
      - place: {"indices": tuple[int,...], "coords": tuple[(x,y)...], "shape_idx": int, "instance_i": int}
      - backtrack: {"indices": tuple[int,...], "shape_idx": int, "instance_i": int}
      - success: {}
      - fail: {}
    """
    board_size = width * height

    total_needed = sum(counts[i] * shape_area(shapes[i]) for i in range(len(shapes)))
    if total_needed > board_size:
        yield ("fail", {})
        return False

    instances: List[int] = []
    for i, c in enumerate(counts):
        instances.extend([i] * c)

    if not instances:
        yield ("success", {})
        return True

    # Order instances: larger first, then fewer orientations first (constrained)
    instances.sort(
        key=lambda s_idx: (shape_area(shapes[s_idx]), -len(shapes[s_idx].orientations)),
        reverse=True,
    )

    suffix_area = [0] * (len(instances) + 1)
    for k in range(len(instances) - 1, -1, -1):
        suffix_area[k] = suffix_area[k + 1] + shape_area(shapes[instances[k]])

    steps = 0

    def dfs(instance_i: int, used_mask: int) -> Generator[Tuple[str, dict], None, bool]:
        nonlocal steps
        if instance_i == len(instances):
            yield ("success", {})
            return True

        used_cells = used_mask.bit_count()
        free_cells = board_size - used_cells
        if suffix_area[instance_i] > free_cells:
            return False

        s_idx = instances[instance_i]
        shape = shapes[s_idx]
        yield ("focus_piece", {"instance_i": instance_i, "shape_idx": s_idx})

        # Iterate candidate origins including a small out-of-bounds halo (for animation)
        # Correct placements are still only those fully in-bounds & non-overlapping.
        for ori in shape.orientations:
            # origins range extended by oob_padding so we can show "outside grid" tries
            for oy in range(-oob_padding, height + oob_padding):
                for ox in range(-oob_padding, width + oob_padding):
                    if steps >= step_limit:
                        return False
                    steps += 1

                    # throttle rendering if desired
                    do_show = (show_every_try <= 1) or (steps % show_every_try == 0)

                    coords = tuple((ox + sx, oy + sy) for (sx, sy) in ori.cells)

                    # OOB check
                    oob = any((x < 0 or x >= width or y < 0 or y >= height) for (x, y) in coords)
                    if oob:
                        if do_show:
                            yield ("try_oob", {"coords": coords, "shape_idx": s_idx})
                        continue

                    # Compute mask
                    mask = 0
                    inds = []
                    for x, y in coords:
                        idx = y * width + x
                        mask |= 1 << idx
                        inds.append(idx)

                    # Overlap check
                    if mask & used_mask:
                        if do_show:
                            yield ("try_overlap", {"coords": coords, "shape_idx": s_idx})
                        continue

                    # This is a valid try
                    if do_show:
                        yield ("try_ok", {"coords": coords, "shape_idx": s_idx})

                    yield ("place", {"indices": tuple(inds), "coords": coords, "shape_idx": s_idx, "instance_i": instance_i})

                    ok = yield from dfs(instance_i + 1, used_mask | mask)
                    if ok:
                        return True

                    yield ("backtrack", {"indices": tuple(inds), "shape_idx": s_idx, "instance_i": instance_i})

        return False

    ok = yield from dfs(0, 0)
    if not ok:
        yield ("fail", {})
    return ok


# =========================
# Manim visuals
# =========================

PALETTE = [BLUE, TEAL, YELLOW, ORANGE, PURPLE, GREEN]


def build_board_grid(width: int, height: int, cell_size: float = 0.5) -> Tuple[VGroup, List[Square]]:
    cells: List[Square] = []
    for _ in range(width * height):
        sq = Square(side_length=cell_size)
        sq.set_stroke(GREY_B, width=1)
        sq.set_fill(BLACK, opacity=0.0)
        cells.append(sq)
    grid = VGroup(*cells).arrange_in_grid(rows=height, cols=width, buff=0.0)
    return grid, cells


def build_shape_icon(shape: Shape, cell_size: float = 0.18) -> VGroup:
    """
    Show the first (normalized) orientation as an icon.
    (We’re *not* trying to show all symmetries in the sidebar.)
    """
    ori = shape.orientations[0]
    w, h = ori.w, ori.h

    icon_cells: List[Square] = []
    cell_lookup: Dict[Coord, Square] = {}

    for y in range(h):
        for x in range(w):
            sq = Square(side_length=cell_size)
            sq.set_stroke(GREY_E, width=1)
            sq.set_fill(BLACK, opacity=0.0)
            icon_cells.append(sq)
            cell_lookup[(x, y)] = sq

    icon_grid = VGroup(*icon_cells).arrange_in_grid(rows=h, cols=w, buff=0.0)

    for (x, y) in ori.cells:
        cell_lookup[(x, y)].set_fill(WHITE, opacity=1.0)

    return icon_grid


class PresentPackingDemo(Scene):
    """
    Edit INPUT_PATH and DEMO_REGION_INDICES to pick which regions you want to animate.
    """

    INPUT_PATH = "p12_demo.txt"
    DEMO_REGION_INDICES = [0, 1]  # animate first 1–2 regions

    def construct(self):
        # Read puzzle
        with open(self.INPUT_PATH, "r", encoding="utf-8") as f:
            shapes, regions = parse_input(f.read())

        title = Text("Present Packing", font_size=36, color=BLUE_C)
        title.to_edge(UP)
        self.play(FadeIn(title))
        self.wait(2)

        for demo_i, region_idx in enumerate(self.DEMO_REGION_INDICES):
            w, h, counts = regions[region_idx]
            self.animate_region(shapes, w, h, counts, region_idx=region_idx)

            if demo_i != len(self.DEMO_REGION_INDICES) - 1:
                # Transition between regions
                self.play(title.animate.set_opacity(0.25))
                self.wait(0.2)
                self.play(title.animate.set_opacity(1.0))

        self.wait(0.6)

    def animate_region(self, shapes: List[Shape], w: int, h: int, counts: List[int], *, region_idx: int):
        # Layout frame: board (left) and sidebar (right)
        subtitle = Text(f"Region {region_idx + 1}: {w}×{h}", font_size=30)
        subtitle.next_to(self.mobjects[0], DOWN, buff=0.2)  # under title, near top
        self.play(FadeIn(subtitle, shift=DOWN * 0.1))
        self.wait(0.5)

        board, board_cells = build_board_grid(w, h, cell_size=0.55)
        board.to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)

        # --- geometry helpers for ghost placements (including outside the board) ---
        cell0 = board_cells[0].get_center()
        dx = board_cells[1].get_center() - board_cells[0].get_center() if w > 1 else (RIGHT * 0.55)
        dy = board_cells[w].get_center() - board_cells[0].get_center() if h > 1 else (DOWN * 0.55)
        cell_size = board_cells[0].side_length

        def pos_for_xy(x: int, y: int):
            return cell0 + dx * x + dy * y

        def ghost_from_coords(coords: Tuple[Tuple[int,int], ...], color, opacity: float):
            g = VGroup()
            for (x, y) in coords:
                sq = Square(side_length=cell_size)
                sq.set_stroke(color, width=2)
                sq.set_fill(color, opacity=opacity)
                sq.move_to(pos_for_xy(x, y))
                g.add(sq)
            return g

        board_frame = SurroundingRectangle(board, buff=0.15).set_stroke(GREY_B, width=2)
        self.play(Create(board), Create(board_frame))
        self.wait(2 if region_idx == 0 else 0.5)

        # Sidebar: required pieces with counts
        sidebar_title = Text("Pieces needed", font_size=28)
        sidebar_title.to_edge(RIGHT, buff=0.8).shift(UP * 2.8)

        rows: List[VGroup] = []
        used_shape_indices = [i for i, c in enumerate(counts) if c > 0]
        for s_idx in used_shape_indices:
            icon = build_shape_icon(shapes[s_idx], cell_size=0.20)
            label = Text(f"x{counts[s_idx]} (shape {s_idx})", font_size=24)
            row = VGroup(icon, label).arrange(RIGHT, buff=0.35)
            rows.append(row)

        sidebar = VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        sidebar.next_to(sidebar_title, DOWN, aligned_edge=LEFT, buff=0.35)
        sidebar.to_edge(RIGHT, buff=0.8).shift(DOWN * 0.2)
        self.play(FadeIn(sidebar_title), FadeIn(sidebar))
        self.wait(4 if region_idx == 0 else 2)

        highlight = SurroundingRectangle(rows[0], buff=0.12).set_stroke(YELLOW, width=3)
        self.play(Create(highlight))

        # Run trace + animate it
        placed_stack: List[Tuple[int, Tuple[int, ...]]] = []  # (shape_idx, indices) for quick clearing

        def set_cells(indices: Tuple[int, ...], color, opacity: float):
            anims = []
            for idx in indices:
                anims.append(board_cells[idx].animate.set_fill(color, opacity=opacity))
            return anims

        # Pre-map shape_idx -> sidebar row index
        shape_to_row = {s_idx: k for k, s_idx in enumerate(used_shape_indices)}

        ok_result: Optional[bool] = None
        ghost: Optional[VGroup] = None

        time_multiplier = 5 if region_idx == 0 else 1
        for event, payload in solve_with_trace(w, h, shapes, counts, step_limit=2500, oob_padding=1, show_every_try=1):
            if event == "focus_piece" and highlight is not None:
                s_idx = payload["shape_idx"]
                if s_idx in shape_to_row:
                    target_row = rows[shape_to_row[s_idx]]
                    self.play(
                        highlight.animate.become(
                            SurroundingRectangle(target_row, buff=0.12).set_stroke(YELLOW, width=3)
                        ),
                        run_time=0.12
                    )

            elif event in ("try_oob", "try_overlap", "try_ok"):
                # remove previous ghost
                if ghost is not None:
                    self.remove(ghost)
                    ghost = None

                s_idx = payload["shape_idx"]
                coords = payload["coords"]

                if event == "try_ok":
                    ghost = ghost_from_coords(coords, YELLOW, 0.25)
                    self.add(ghost)
                    self.wait(0.03 * time_multiplier)

                elif event == "try_overlap":
                    ghost = ghost_from_coords(coords, RED, 0.18)
                    self.add(ghost)
                    self.wait(0.08 * time_multiplier)
                    self.remove(ghost)
                    ghost = None

                elif event == "try_oob":
                    ghost = ghost_from_coords(coords, RED, 0.12)
                    self.add(ghost)
                    # Emphasize boundary failure by flashing the frame too
                    # self.play(Circumscribe(board_frame, color=RED), run_time=0.08 * time_multiplier)
                    self.wait(0.08 * time_multiplier)
                    self.remove(ghost)
                    ghost = None

            elif event == "place":
                inds = payload["indices"]
                s_idx = payload["shape_idx"]
                color = PALETTE[s_idx % len(PALETTE)]

                # If a ghost exists, fade it out as we commit the placement
                if ghost is not None:
                    self.play(FadeOut(ghost), run_time=0.05)
                    ghost = None

                self.play(*set_cells(inds, color, 0.95), run_time=0.10 * time_multiplier)
                placed_stack.append((s_idx, inds))

            elif event == "backtrack":
                inds = payload["indices"]
                self.play(*set_cells(inds, BLACK, 0.0), run_time=0.08 * time_multiplier)
                if placed_stack and placed_stack[-1][1] == inds:
                    placed_stack.pop()

            elif event == "success":
                ok_result = True
                break

            elif event == "fail":
                ok_result = False
                break

        # End marker
        if ok_result:
            mark = Text("✓", font_size=90, color=GREEN).next_to(board_frame, RIGHT, buff=0.35).shift(UP * 0.2)
            self.play(FadeIn(mark, scale=1.1), Circumscribe(board_frame, color=GREEN), run_time=0.5)
        else:
            mark = Text("✗", font_size=90, color=RED).next_to(board_frame, RIGHT, buff=0.35).shift(UP * 0.2)
            self.play(FadeIn(mark, scale=1.1), Circumscribe(board_frame, color=RED), run_time=0.5)

        self.wait(0.6)

        # Clean up region visuals before next region
        to_remove = [subtitle, board, board_frame, sidebar_title, sidebar, mark]
        if highlight is not None:
            to_remove.append(highlight)
        self.play(*[FadeOut(m) for m in to_remove], run_time=0.35)
