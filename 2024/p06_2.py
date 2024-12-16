from collections import defaultdict

with open('p06.txt') as rb:
    data = [list(l) for l in rb]


def next_pos(direction, pos_x, pos_y):
    near_positions = {
        '<': (pos_x - 1, pos_y),  # Left
        '>': (pos_x + 1, pos_y),  # Right
        '^': (pos_x, pos_y - 1),  # Up
        'v': (pos_x, pos_y + 1),  # Down
    }
    return near_positions[direction]


RIGHT_TURN = {
    '<': '^',
    '>': 'v',
    '^': '>',
    'v': '<',
}

start_x, start_y = 0, 0
for start_y in range(len(data)):
    if '^' in data[start_y]:
        start_x = data[start_y].index('^')
        break

def gets_stuck_in_loop(puzzle):
    previous_position_directions = defaultdict(lambda: defaultdict(set))
    x, y = start_x, start_y

    direction = '^'
    while True:
        next_spot = next_pos(direction, x, y)

        if next_spot[0] < 0 or next_spot[1] < 0 or next_spot[0] >= len(puzzle[0]) or next_spot[1] >= len(puzzle):
            return False

        next_spot_data = puzzle[next_spot[1]][next_spot[0]]
        if next_spot_data == '#':
            direction = RIGHT_TURN[direction]
            continue

        if direction in previous_position_directions[y][x]:
            return True

        previous_position_directions[y][x].add(direction)
        x, y = next_spot

total = 0
for target_y in range(len(data)):
    for target_x in range(len(data[target_y])):
        if data[target_y][target_x] != '.':
            continue

        data[target_y][target_x] = '#'
        if gets_stuck_in_loop(data):
            total += 1
        data[target_y][target_x] = '.'

print(total)
