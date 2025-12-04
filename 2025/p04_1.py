def get_adjacent_coords(grid, x, y):
    """
    Return the coordinates of all valid adjacent cells (up to 8) around (x, y)
        in a 2D grid. Edges and corners naturally have fewer neighbors.
    """
    height = len(grid)
    width = len(grid[0])

    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue  # Skip the target itself

            nx = x + dx
            ny = y + dy

            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny



# Step 1: Load data and format into data structure:
with open("p04.txt") as rb:
    puzzle = [list(l.strip()) for l in rb.readlines()]


# Step 2: Solve the problem
answer = 0
for row_i, row in enumerate(puzzle):
    for col_i, item in enumerate(row):
        if item == '.':
            continue

        adjacent_count = sum(1
                             for adj_col_i, adj_row_i in get_adjacent_coords(puzzle, col_i, row_i)
                             if puzzle[adj_row_i][adj_col_i] == '@')

        if adjacent_count < 4:
            answer += 1


# Step 3: Output answer
print(answer)
