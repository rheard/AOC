# Step 1: Load data
robot_x, robot_y = 0, 0
with open('p15.txt') as rb:
    data = []

    while (l := rb.readline().strip()):
        raw_r = list(l)
        r = []
        # Build replacement board:
        for c in raw_r:
            if c == '#':
                r.extend('##')
            elif c == 'O':
                r.extend('[]')
            elif c == '.':
                r.extend('..')
            elif c == '@':
                r.extend('@.')

        if '@' in r:
            robot_x = r.index('@')

        if not robot_x:
            robot_y += 1

        data.append(r)

    moves = [x for x in rb.read() if x in '<>^v']


# Step 2: Solve the problem
def next_pos(direction, pos_x, pos_y):
    near_positions = {
        '<': (pos_x - 1, pos_y),  # Left
        '>': (pos_x + 1, pos_y),  # Right
        '^': (pos_x, pos_y - 1),  # Up
        'v': (pos_x, pos_y + 1),  # Down
    }
    return near_positions[direction]


def move_robot_vert(board, direction, pos_x, pos_y):
    """
    Handle robot movement vertically.
        Because of the width was doubled but not vertical space, this should be handled differently
    """
    orig_pos_x, orig_pos_y = pos_x, pos_y
    target_pos_x, target_pos_y = next_pos(direction, pos_x, pos_y)
    pos_to_process = [(pos_x, pos_y)]  # Positions which need to be looked above for free space
    pos_processed = []  # Positions that contain an item that will need moving
    while pos_to_process:
        pos_x, pos_y = pos_to_process.pop()
        pos_processed.append((pos_x, pos_y))
        pos_x, pos_y = next_pos(direction, pos_x, pos_y)
        spot_val = board[pos_y][pos_x]

        # Add both parts of a box found to the spaces to be processed
        if spot_val == ']':
            pos_to_process.append((pos_x, pos_y))
            pos_to_process.append((pos_x - 1, pos_y))
        elif spot_val == '[':
            pos_to_process.append((pos_x, pos_y))
            pos_to_process.append((pos_x + 1, pos_y))
        elif spot_val == '#':
            return orig_pos_x, orig_pos_y  # Found a wall, so nothing can move

    # Make sure to move in correct order: furthest away from the robot first!
    pos_processed = sorted(set(pos_processed), key=lambda x: (x[1], x[0]))
    if direction == 'v':
        pos_processed = list(reversed(pos_processed))

    for pos_x, pos_y in pos_processed:
        next_pos_x, next_pos_y = next_pos(direction, pos_x, pos_y)
        # Move item forward and replace its old spot with free space
        board[next_pos_y][next_pos_x] = board[pos_y][pos_x]
        board[pos_y][pos_x] = '.'

    return target_pos_x, target_pos_y


def move_robot_horiz(board, direction, pos_x, pos_y):
    """Handle robot movement horizontally."""
    orig_pos_x, orig_pos_y = pos_x, pos_y
    target_pos_x, target_pos_y = next_pos(direction, pos_x, pos_y)

    while (spot_val := board[pos_y][pos_x]) in ['[', ']', '@']:
        pos_x, pos_y = next_pos(direction, pos_x, pos_y)

    if spot_val == '#':
        return orig_pos_x, orig_pos_y

    # Now walk backwards to the robot, moving along the way
    while (pos_x, pos_y) != (orig_pos_x, orig_pos_y):
        prev_positions = {
            '<': (pos_x + 1, pos_y),  # Reverse direction for left
            '>': (pos_x - 1, pos_y),  # Reverse direction for right
        }
        prev_pos_x, prev_pos_y = prev_positions[direction]

        board[pos_y][pos_x] = board[prev_pos_y][prev_pos_x]
        pos_x, pos_y = prev_pos_x, prev_pos_y

    # Place the robot in the final position
    board[orig_pos_y][orig_pos_x] = '.'
    return target_pos_x, target_pos_y


for move in moves:
    next_pos_x, next_pos_y = next_pos(move, robot_x, robot_y)
    next_pos_val = data[next_pos_y][next_pos_x]

    if next_pos_val == '#':
        continue

    if move in '^v':
        robot_x, robot_y = move_robot_vert(data, move, robot_x, robot_y)
    else:
        robot_x, robot_y = move_robot_horiz(data, move, robot_x, robot_y)

total = 0
for spot_y, r in enumerate(data):
    for spot_x, spot in enumerate(r):
        if spot != '[':
            continue

        # Add GPS coordinates of this box:
        total += spot_y * 100 + spot_x

print(total)
