import re

from dataclasses import dataclass
from typing import Sequence, Optional

import numpy as np

from scipy.optimize import milp, LinearConstraint, Bounds


@dataclass
class Puzzle:
    indicator_goal: list[bool]
    wiring_schematics: list[tuple[int]]
    joltage_requirements: list[int]


def min_button_presses(
    wirings: Sequence[Sequence[int]],
    targets: Sequence[bool],
) -> Optional[int]:
    """
    Given a set of buttons that toggle indicators, find the minimum
        number of buttons to press to reach the desired targets.

    Args:
        wirings:
            A sequence of length M (buttons). Each element is a sequence of
            indicator indices that this button toggles.
        targets:
            A sequence of length N of desired final states for each indicator.

    Returns:
        The minimal number of buttons presses, or None if no exact solution exists.
    """
    targets = np.asarray(targets, dtype=float)
    n_indicators = len(targets)
    n_buttons = len(wirings)
    n_vars = n_buttons + n_indicators

    # Build A matrix: shape (N, M)
    # A[i, j] = 1 if button j toggles indicator i
    A = np.zeros((n_indicators, n_buttons), dtype=float)
    for j, wiring in enumerate(wirings):
        for idx in wiring:
            if not (0 <= idx < n_indicators):
                raise ValueError(f"Wiring index {idx} out of range for targets of length {n_indicators}")
            A[idx, j] = 1.0

    # Decision vars: x (buttons) and k (parity helpers)
    #   x_j: 0/1 (pressed or not)
    #   k_i: integer >= 0
    # Constraint: sum_j A[i,j] * x_j - 2 * k_i = target_i
    A_ext = np.zeros((n_indicators, n_vars), dtype=float)
    A_ext[:, :n_buttons] = A
    for i in range(n_indicators):
        A_ext[i, n_buttons + i] = -2.0

    # Minimize sum_j x_j
    c = np.zeros(n_vars, dtype=float)
    c[:n_buttons] = 1.0

    constraint = LinearConstraint(A_ext, lb=targets, ub=targets)

    # Bounds: 0 <= x_j <= 1 (binary once integrality=1); 0 <= k_i < +inf
    ub = np.full(n_vars, np.inf, dtype=float)
    ub[:n_buttons] = 1.0

    bounds = Bounds(lb=np.zeros(n_vars, dtype=float), ub=ub)

    # All variables are integers; buttons become booleans via bounds
    integrality = np.ones(n_vars, dtype=int)   # 1 = integer

    result = milp(
        c=c,
        constraints=constraint,
        bounds=bounds,
        integrality=integrality,
    )

    if not result.success:
        # No feasible integer solution
        return None

    # Round to nearest integers
    x = np.rint(result.x[:n_buttons]).astype(int)

    # Optional sanity checks
    # - Parity matches targets
    final_parity = (A @ x) % 2
    if not np.array_equal(final_parity, targets):
        raise RuntimeError(
            "MILP solution violates parity constraints after rounding; "
            "this suggests numerical issues or a modelling bug."
        )

    return int(x.sum())


# Step 1: Load data and format into data structure:
with open("p10.txt") as rb:
    puzzles = []
    for raw_line in rb.readlines():
        line = raw_line.strip()
        if not line:
            continue

        # 1) Indicator goal: stuff inside [...]
        indicator_str = re.search(r"\[([.#]+)\]", line).group(1)
        indicator_goal = [c == "#" for c in indicator_str]

        # 2) Wiring schematics: each (...) group
        paren_groups = re.findall(r"\(([^)]*)\)", line)
        # All but the last {...} are schematics; safer to stop before '{'
        # but here curly is separate, so we can use all paren groups.
        wiring_schematics = []
        for g in paren_groups:
            g = g.strip()
            if not g:
                wiring_schematics.append(tuple())
            else:
                wiring_schematics.append(tuple(int(x) for x in g.split(",")))

        # 3) Joltage requirements: inside {...}
        joltage_str = re.search(r"\{([^}]*)\}", line).group(1)
        joltage_requirements = [int(x) for x in joltage_str.split(",") if x]

        puzzles.append(
            Puzzle(
                indicator_goal=indicator_goal,
                wiring_schematics=wiring_schematics,
                joltage_requirements=joltage_requirements,
            )
        )


# Step 2: Solve the problem
answer = 0
for p in puzzles:
    answer += min_button_presses(p.wiring_schematics, p.indicator_goal)


# Step 3: Output answer
print(answer)
