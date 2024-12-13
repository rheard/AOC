import re

from sympy import symbols, Eq, solve


# Step 1: Load data
with open('p13.txt', 'r') as file:
    data = []
    for raw_game in file.read().split('\n\n'):
        game = {}

        # Find Button and Prize data
        button_matches = re.findall(r"^(Button [A-B]): X\+(\d+), Y\+(\d+)$", raw_game, re.MULTILINE)
        prize_match = re.search(r"^Prize: X=(\d+), Y=(\d+)$", raw_game, re.MULTILINE)

        for button_name, x_offset, y_offset in button_matches:
            game[button_name] = (int(x_offset), int(y_offset))

        prize_x = int(prize_match.group(1))
        prize_y = int(prize_match.group(2))
        game['Prize'] = (prize_x, prize_y)
        data.append(game)


# Step 2: Solve the problem
Cost = lambda sol: sol[0] * 3 + sol[1] * 1


def solve_prize_equation(prize, button_a, button_b):
    """Solve the equation (for both X and Y): Prize = A * A_presses + B * B_presses"""
    A_presses, B_presses = symbols('A_presses B_presses', integer=True, nonnegative=True)

    eq_x = Eq(prize[0], A_presses * button_a[0] + B_presses * button_b[0])
    eq_y = Eq(prize[1], A_presses * button_a[1] + B_presses * button_b[1])

    # Solve the equations
    solutions = solve((eq_x, eq_y), (A_presses, B_presses), dict=True)
    if not solutions:
        return None

    min_cost_sol = min([(s[A_presses], s[B_presses]) for s in solutions], key=Cost)

    return min_cost_sol


total = 0
for entry in data:
    prize = (entry['Prize'][0], entry['Prize'][1])
    button_a = (entry['Button A'][0], entry['Button A'][1])
    button_b = (entry['Button B'][0], entry['Button B'][1])

    solution = solve_prize_equation(prize, button_a, button_b)
    if solution:
        total += Cost(solution)

print(total)
