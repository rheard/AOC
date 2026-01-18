from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Generator, Iterable, List, Optional, Tuple
import re

from manim import (
    AnimationGroup, LaggedStart,
    Scene, VGroup, Square, Text, SurroundingRectangle,
    FadeIn, FadeOut, Create, Indicate, Circumscribe,
    LEFT, RIGHT, UP, DOWN, ORIGIN,
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

    for flip in (False, True):
        for rot in range(4):
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
    step_limit: int = None,
    oob_padding: int = 0,          # how far outside to "try" for animation
    show_every_try: int = 1,       # 1 = show all tries, 5 = show 1/5 tries, etc.
) -> Generator[Tuple[str, dict], None, bool | None]:
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

    instances: List[int] = []
    for i, c in enumerate(counts):
        instances.extend([i] * c)

    suffix_area = [0] * (len(instances) + 1)
    for k in range(len(instances) - 1, -1, -1):
        suffix_area[k] = suffix_area[k + 1] + shape_area(shapes[instances[k]])

    steps = 0

    def dfs(instance_i: int, used_mask: int) -> Generator[Tuple[str, dict], None, bool | None]:
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
                    if step_limit and steps >= step_limit:
                        return None
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

                    if ok is None:
                        return None

                    yield ("backtrack", {"indices": tuple(inds), "shape_idx": s_idx, "instance_i": instance_i})

        return False

    ok = yield from dfs(0, 0)
    if ok is False:
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
    """Animation for part 1, showing an actual packing algorithm"""

    INPUT_PATH = "p12_demo.txt"
    DEMO_REGION_INDICES = [0, 1]  # animate first 1–2 regions
    CELL_SIZE = 0.55
    PLACE_RUN_TIME = 0.9

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.to_delete = []
        self.highlight = None

    def construct(self):
        # Read puzzle
        with open(self.INPUT_PATH, "r", encoding="utf-8") as f:
            shapes, regions = parse_input(f.read())

        for demo_i, region_idx in enumerate(self.DEMO_REGION_INDICES):
            w, h, counts = regions[region_idx]
            self.animate_region(shapes, w, h, counts, region_idx=region_idx)

            if demo_i != len(self.DEMO_REGION_INDICES) - 1:
                # Transition between regions
                self.wait(0.2)

        self.wait(0.6)

    def create_title(self, w, h, region_idx: int):
        title = Text(f"Region {region_idx + 1}: {w}×{h}", font_size=30, color=BLUE_C)
        title.to_edge(UP)
        self.play(FadeIn(title, shift=DOWN * 0.1))
        self.wait(0.5)
        self.to_delete.append(title)

    def create_board(self, w, h, wait_time=0.5):
        """Create the board and frame"""
        board, board_cells = build_board_grid(w, h, cell_size=0.55)
        board.to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)
        board_frame = SurroundingRectangle(board, buff=0.15).set_stroke(GREY_B, width=2)
        self.play(Create(board), Create(board_frame))
        self.wait(wait_time)

        self.to_delete.append(board)
        self.to_delete.append(board_frame)

        return board, board_cells, board_frame

    def create_sidebar(self, shapes, counts, wait_time=2):
        """Create the sidebar showing how many of which shapes are needed"""
        sidebar_title = Text("Pieces needed", font_size=28)
        sidebar_title.to_edge(RIGHT, buff=0.8).shift(UP * 2.8)

        rows: List[VGroup] = []
        used_shape_indices = [i for i, c in enumerate(counts) if c > 0]
        shape_to_row = {s_idx: k for k, s_idx in enumerate(used_shape_indices)}
        for s_idx in used_shape_indices:
            icon = build_shape_icon(shapes[s_idx], cell_size=0.20)
            label = Text(f"x {counts[s_idx]}", font_size=24)
            row = VGroup(icon, label).arrange(RIGHT, buff=0.35)
            rows.append(row)

        sidebar = VGroup(*rows).arrange(DOWN, aligned_edge=LEFT, buff=0.25)
        sidebar.next_to(sidebar_title, DOWN, aligned_edge=ORIGIN, buff=0.35)
        sidebar.to_edge(ORIGIN, buff=0.8).shift(DOWN * 0.2)
        self.play(FadeIn(sidebar_title), FadeIn(sidebar))
        self.wait(wait_time)

        self.to_delete.append(sidebar)
        self.to_delete.append(sidebar_title)

        return rows, shape_to_row

    def create_end_marker(self, board_frame, ok_result):
        """Create the success or failure end marker"""
        if ok_result is True:
            mark = Text("✓", font_size=90, color=GREEN).next_to(board_frame, RIGHT, buff=0.35).shift(UP * 0.2)
            self.play(FadeIn(mark, scale=1.1), Circumscribe(board_frame, color=GREEN), run_time=0.5)
            self.to_delete.append(mark)
        elif ok_result is False:
            mark = Text("✗", font_size=90, color=RED).next_to(board_frame, RIGHT, buff=0.35).shift(UP * 0.2)
            self.play(FadeIn(mark, scale=1.1), Circumscribe(board_frame, color=RED), run_time=0.5)
            self.to_delete.append(mark)

    def highlight_row(self, rows, shape_to_row, shape_idx):
        """Draw a highlight or move it to a particular shape's row"""
        if shape_idx not in shape_to_row:
            raise ValueError("Something has gone terribly wrong! We cannot select a shape that was not drawn!")

        target_row = rows[shape_to_row[shape_idx]]
        if self.highlight is None:
            self.highlight = SurroundingRectangle(target_row, buff=0.12).set_stroke(YELLOW, width=3)
            self.to_delete.append(self.highlight)
            self.play(Create(self.highlight))
        else:
            self.play(
                self.highlight.animate.become(
                    SurroundingRectangle(target_row, buff=0.12).set_stroke(YELLOW, width=3)
                ),
                run_time=0.12
            )

    def sidebar_waittime(self, region_idx: int):
        """How long to wait after creating the sidebar"""
        return 4 if region_idx == 0 else 2

    def animate_region(self, shapes: List[Shape], w: int, h: int, counts: List[int], *, region_idx: int):
        """An entire end-to-end animation for a region, showing the title, board and solution"""
        self.highlight = None

        # Layout frame: board (left) and sidebar (right)
        self.create_title(w, h, region_idx)
        _, board_cells, board_frame = self.create_board(w, h, 2 if region_idx == 0 else 0.5)
        rows, shape_to_row = self.create_sidebar(shapes, counts, self.sidebar_waittime(region_idx))

        ok_result = self.animate_solution(w, h, shapes, counts, rows, shape_to_row,
                                          region_idx, board_frame, board_cells)

        # End marker
        self.create_end_marker(board_frame, ok_result)
        self.wait(0.8)

        # Clean up region visuals before next region
        self.play(*[FadeOut(m) for m in self.to_delete], run_time=0.35)

    def animate_solution(self, w, h, shapes, counts, rows, shape_to_row, region_idx, board_frame, board_cells):
        """Animate just the solution for a problem"""
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

        # Run trace + animate it
        placed_stack: List[Tuple[int, Tuple[int, ...]]] = []  # (shape_idx, indices) for quick clearing

        def set_cells(indices: Tuple[int, ...], color, opacity: float):
            return [board_cells[idx].animate.set_fill(color, opacity=opacity) for idx in indices]

        # Pre-map shape_idx -> sidebar row index
        ok_result: Optional[bool] = None
        ghost: Optional[VGroup] = None

        time_multiplier = 5 if region_idx == 0 else 0.5
        for event, payload in solve_with_trace(w, h, shapes, counts, step_limit=10000):
            if event == "focus_piece":
                s_idx = payload["shape_idx"]
                self.highlight_row(rows, shape_to_row, s_idx)

            elif event in ("try_oob", "try_overlap", "try_ok"):
                # remove previous ghost
                if ghost is not None:
                    self.remove(ghost)
                    ghost = None

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

        return ok_result


class PresentPackingAreaReveal(PresentPackingDemo):
    """Follow-up animation showing the trick: only area actually matters due to specially crafted input"""

    DEMO_REGION_INDICES = [0, 1, 2]

    def sidebar_waittime(self, region_idx: int):
        """How long to wait after creating the sidebar"""
        return 2

    def animate_solution(self, w, h, shapes, counts, rows, shape_to_row, region_idx, board_frame, board_cells):
        """Animate just the solution for a problem"""
        # We'll "fill" the board cells left-to-right, top-to-bottom.
        next_free = 0
        board_size = w * h

        # A staging spot to show the current present before it "breaks"
        staging = board_frame.get_right() + RIGHT * 1.55 + UP * 0.8

        def present_mobject_for_shape(s_idx: int, color) -> VGroup:
            """Create a little 'rigid present' made of squares using the first orientation."""
            ori = shapes[s_idx].orientations[0]
            s = self.CELL_SIZE * 0.62  # smaller than board cells so it feels like an object
            squares = []
            for x, y in ori.cells:
                sq = Square(side_length=s)
                sq.set_stroke(GREY_E, width=2)
                sq.set_fill(color, opacity=0.85)
                squares.append((sq, x, y))

            g = VGroup(*[sq for (sq, _, _) in squares])

            # Position squares in a grid-ish layout centered on the group
            # y grows downward in our coords, but manim y grows upward.
            min_x = min(x for _, x, _ in squares)
            min_y = min(y for _, _, y in squares)
            max_x = max(x for _, x, _ in squares)
            max_y = max(y for _, _, y in squares)

            for (sq, x, y) in squares:
                dx = (x - (min_x + max_x) / 2.0) * s
                dy = (-(y - (min_y + max_y) / 2.0)) * s
                sq.shift(RIGHT * dx + UP * dy)

            return g

        def place_unit_square(unit_sq: Square, target_idx: int):
            """Move a floating unit square to a board cell and commit the color."""
            # If we're out of space, slam it against the frame and show red.
            if target_idx >= board_size:
                bump = board_frame.get_right() + RIGHT * 0.15
                return AnimationGroup(
                    unit_sq.animate.move_to(bump),
                    Indicate(board_frame, color=RED),
                    run_time=self.PLACE_RUN_TIME,
                )

            target = board_cells[target_idx]
            unit_sq.set_stroke(target.get_stroke_color(), width=target.get_stroke_width())

            return AnimationGroup(
                unit_sq.animate.move_to(target.get_center()).scale_to_fit_width(target.width),
                run_time=self.PLACE_RUN_TIME * 2 if region_idx == 0 else self.PLACE_RUN_TIME,
            )

        # Animate consuming each present
        used_shape_indices = [i for i, c in enumerate(counts) if c > 0]
        for s_idx in used_shape_indices:
            self.highlight_row(rows, shape_to_row, s_idx)

            color = PALETTE[s_idx % len(PALETTE)]
            for _ in range(counts[s_idx]):
                # Show the present (rigid piece)
                piece = present_mobject_for_shape(s_idx, color).move_to(staging)
                self.play(FadeIn(piece, scale=1.05), run_time=0.2)

                # Now drag each unit square to the grid, one after another
                anims = []
                for sq in list(piece.submobjects):
                    self.to_delete.append(sq)
                    anims.append(place_unit_square(sq, next_free))
                    next_free += 1

                self.play(LaggedStart(*anims, lag_ratio=0.06))

        needed = sum(counts[i] * shape_area(shapes[i]) for i in range(len(shapes)))
        have = w * h
        return needed <= have

# =========================
# Orientation uniqueness demo (small "background" clip)
# =========================

def build_icon_from_cells(cells: Iterable[Coord], *, cell_size: float = 0.22, fill_color=WHITE) -> VGroup:
    """
    Build a tiny icon for an arbitrary set of occupied (x,y) cells.
    Cells are assumed normalized to min corner at (0,0).
    """
    norm = normalize_cells(cells)
    max_x = max(x for x, _ in norm)
    max_y = max(y for _, y in norm)
    w, h = max_x + 1, max_y + 1

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
    for (x, y) in norm:
        cell_lookup[(x, y)].set_fill(fill_color, opacity=1.0)
    return icon_grid


class OrientationUniquenessDemo(Scene):
    """
    A short clip illustrating why we *deduplicate* the 8 naïve orientations
    (4 rotations × mirrored 4 rotations).

    It can cycle through multiple example shapes. Between examples, we fade
    away everything except the title/subtitle.
    """

    def construct(self):
        title = Text("Unique orientations", font_size=34, color=BLUE_C).to_edge(UP)
        subtitle = Text("out of 4 rotations + 4 mirror rotations", font_size=26).next_to(title, DOWN, buff=0.18)
        self.play(FadeIn(title, shift=DOWN * 0.1), FadeIn(subtitle, shift=DOWN * 0.1), run_time=0.5)
        self.wait(1.0)

        demos = [
            (
                "C piece",
                [
                    #   ###
                    #   #..
                    #   ###
                    (0, 0), (1, 0), (2, 0),
                    (0, 1),
                    (0, 2), (1, 2), (2, 2),
                ],
                1.0,   # speed (1.0 = current)
                2,     # highlight loops at end
            ),
            (
                "I piece",
                [
                    #   ###
                    #   .#.
                    #   ###
                    (0, 0), (1, 0), (2, 0),
                    (1, 1),
                    (0, 2), (1, 2), (2, 2),
                ],
                0.65,  # faster
                1,
            ),
        ]

        for demo_i, (label_text, base_cells, speed, loops) in enumerate(demos):
            demo_group = self._animate_one_shape(base_cells, label_text=label_text, speed=speed, loops=loops)

            # Fade away everything except title/subtitle before the next shape.
            if demo_i != len(demos) - 1:
                self.play(FadeOut(demo_group), run_time=0.35)
                self.wait(0.15)

        self.wait(0.4)

    def _animate_one_shape(self, base_cells: List[Coord], *, label_text: str, speed: float, loops: int) -> VGroup:
        """Animate the 8 naïve transforms and visibly dim the duplicates."""
        base_shape = generate_unique_orientations(base_cells)

        # Show the piece we are talking about (left).
        big = build_icon_from_cells(base_shape.orientations[0].cells, cell_size=0.34).scale(1.15)
        big_box = SurroundingRectangle(big, buff=0.20).set_stroke(GREY_B, width=2)

        piece_label = Text(label_text, font_size=24, color=GREY_B)
        piece_label.next_to(big_box, DOWN, buff=0.25)

        big_group = VGroup(big, big_box, piece_label).to_edge(LEFT, buff=0.9).shift(DOWN * 0.2)
        self.play(FadeIn(big_group, scale=1.02), run_time=0.45 * speed)
        self.wait(0.45 * speed)

        # Precompute all 8 transformations *including duplicates*, and map duplicates -> first occurrence.
        transforms: List[Tuple[bool, int, Tuple[Coord, ...]]] = []
        for flip in (False, True):
            for rot in range(4):
                transformed: List[Coord] = []
                for x, y in normalize_cells(base_cells):
                    xx, yy = x, y
                    for _ in range(rot):
                        xx, yy = -yy, xx
                    if flip:
                        xx = -xx
                    transformed.append((xx, yy))
                key = normalize_cells(transformed)
                transforms.append((flip, rot, key))

        first_of: Dict[Tuple[Coord, ...], int] = {}
        dup_of: List[Optional[int]] = [None] * 8
        for i, (_, _, key) in enumerate(transforms):
            if key in first_of:
                dup_of[i] = first_of[key]
            else:
                first_of[key] = i

        # Build the 2×4 "naïve" orientation grid on the right.
        slots = VGroup()
        for _ in range(8):
            box = SurroundingRectangle(Square(side_length=0.9), buff=0.22).set_stroke(GREY_B, width=2)
            slots.add(box)

        slots.arrange_in_grid(rows=2, cols=4, buff=0.35)
        slots.to_edge(RIGHT, buff=0.75).shift(DOWN * 0.25)

        row0 = Text("rotate", font_size=22, color=GREY_B).next_to(slots[0], UP, buff=0.35).shift(LEFT * 1.45)
        row1 = Text("mirror + rotate", font_size=22, color=GREY_B).next_to(slots[4], DOWN, buff=0.35).shift(LEFT * 1.05)

        self.play(Create(slots), FadeIn(row0), FadeIn(row1), run_time=0.6 * speed)

        slot_icons: List[VGroup] = []
        slot_labels: List[Text] = []
        dup_tags: List[Text] = []

        def draw_slot(i: int, *, rt: float):
            flip, rot, key = transforms[i]
            icon = build_icon_from_cells(key, cell_size=0.20, fill_color=WHITE)
            icon.move_to(slots[i].get_center())

            deg = (rot * 90) % 360
            lbl = Text(f"{deg}°", font_size=22, color=GREY_B).next_to(slots[i], DOWN, buff=0.08)

            if dup_of[i] is not None:
                icon.set_opacity(0.32)
                self.play(FadeIn(icon), FadeIn(lbl), run_time=rt)

                j = dup_of[i]
                self.play(
                    Indicate(slots[i], color=RED),
                    Indicate(slots[j], color=YELLOW),
                    run_time=0.35 * speed,
                )

                # If this is the *first* mirrored duplicate, call out the relation.
                if i == 4 and j is not None:
                    note = Text("mirror = rotate 180°", font_size=24, color=YELLOW).next_to(slots, UP, buff=0.35)
                    self.play(FadeIn(note, shift=DOWN * 0.06), run_time=0.25 * speed)
                    self.wait(0.35 * speed)
                    self.play(FadeOut(note), run_time=0.2 * speed)

            else:
                self.play(FadeIn(icon), FadeIn(lbl), run_time=rt)

            self.wait(0.25 * speed)
            slot_icons.append(icon)
            slot_labels.append(lbl)

        # Draw the 8 naïve orientations, left-to-right.
        for i in range(8):
            draw_slot(i, rt=0.25 * speed)

        # Summarize: unique count.
        unique_count = len(first_of)
        summary = Text(f"Unique = {unique_count} (not 8)", font_size=30, color=GREEN).next_to(slots, DOWN, buff=0.55)
        self.play(FadeIn(summary, shift=DOWN * 0.12), run_time=0.4 * speed)

        # Gentle highlights over the unique slots.
        unique_slots = sorted(first_of.values())
        for _ in range(max(0, loops)):
            for i in unique_slots:
                self.play(Indicate(slots[i], color=GREEN), run_time=0.35 * speed)

        self.wait(0.2 * speed)

        # Group everything that should be faded out between demos.
        return VGroup(big_group, slots, row0, row1, *slot_icons, *slot_labels, *dup_tags, summary)
