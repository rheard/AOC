# Step 1: Load data
robot_x, robot_y = 0, 0
with open('p15.txt') as rb:
    data = []

    while (l := rb.readline().strip()):
        r = list(l)
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
        '^': (pos_x, pos_y - 1),  # Bottom
        'v': (pos_x, pos_y + 1),  # Top
    }
    return near_positions[direction]


def move_robot(board, direction, pos_x, pos_y):
    orig_pos_x, orig_pos_y = pos_x, pos_y
    target_pos_x, target_pos_y = next_pos(direction, pos_x, pos_y)  # The immediate position the robot will move in to
    # Find the nearest free space or wall
    while (spot_val := board[pos_y][pos_x]) in 'O@':
        pos_x, pos_y = next_pos(direction, pos_x, pos_y)

    if spot_val == '#':
        return orig_pos_x, orig_pos_y

    # Place a box at the farthest empty space found,
    board[pos_y][pos_x] = 'O'
    #   place the robot in the nearest box's space (thereby moving the box)
    board[target_pos_y][target_pos_x] = '@'
    #   and an empty space where the robot was...
    board[orig_pos_y][orig_pos_x] = '.'

    return target_pos_x, target_pos_y


for move in moves:
    robot_x, robot_y = move_robot(data, move, robot_x, robot_y)

total = 0
for spot_y, r in enumerate(data):
    for spot_x, spot in enumerate(r):
        if spot != 'O':
            continue

        # Add GPS coordinates of this box:
        total += spot_y * 100 + spot_x

print(total)
