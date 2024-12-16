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

x, y = 0, 0
for y in range(len(data)):
    if '^' in data[y]:
        x = data[y].index('^')
        break

direction = '^'
while True:
    next_spot = next_pos(direction, x, y)

    if next_spot[0] < 0 or next_spot[1] < 0 or next_spot[0] >= len(data[0]) or next_spot[1] >= len(data):
        break

    next_spot_data = data[next_spot[1]][next_spot[0]]
    if next_spot_data == '#':
        direction = RIGHT_TURN[direction]
        continue

    data[y][x] = 'X'
    x, y = next_spot

total = sum(r.count('X') for r in data)  # 4938     664   666      665        4939
print(total)
