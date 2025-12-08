from functools import cache


# Step 1: Load data and format into data structure:
with open("p07.txt") as rb:
    puzzle = [list(l.strip()) for l in rb.readlines()]


# Step 2: Solve the problem
start_x, start_y = None, None
for row_i, row in enumerate(puzzle):
    for col_i, col in enumerate(row):
        if col == 'S':
            start_x = col_i
            start_y = row_i
            break
    if start_x is not None:
        break


@cache
def follow_beam(beam_x, beam_y):
    total_count = set()
    while beam_y < len(puzzle) - 1:
        beam_y += 1
        cell = puzzle[beam_y][beam_x]

        if cell == '.':
            continue

        elif cell == '^':
            total_count.add((beam_x, beam_y))
            total_count |= follow_beam(beam_x + 1, beam_y)
            total_count |= follow_beam(beam_x - 1, beam_y)
            break

    return total_count


answer = follow_beam(start_x, start_y)


# Step 3: Output answer
print(len(answer))
