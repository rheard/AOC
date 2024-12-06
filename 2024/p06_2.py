from collections import defaultdict

with open('p06.txt') as rb:
    data = [list(l) for l in rb]

start_x, start_y = 0, 0
for start_y in range(len(data)):
    if '^' in data[start_y]:
        start_x = data[start_y].index('^')
        break

def gets_stuck_in_loop(puzzle):
    previous_position_directions = defaultdict(lambda: defaultdict(set))
    x, y = start_x, start_y

    direction = 'up'
    while True:
        if direction == 'up':
            next_spot = (x, y - 1)
        elif direction == 'down':
            next_spot = (x, y + 1)
        elif direction == 'left':
            next_spot = (x - 1, y)
        else:
            next_spot = (x + 1, y)

        if next_spot[0] < 0 or next_spot[1] < 0 or next_spot[0] >= len(puzzle[0]) or next_spot[1] >= len(puzzle):
            return False

        next_spot_data = puzzle[next_spot[1]][next_spot[0]]
        if next_spot_data == '#':
            if direction == 'up':
                direction = 'right'
            elif direction == 'right':
                direction = 'down'
            elif direction == 'down':
                direction = 'left'
            elif direction == 'left':
                direction = 'up'

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
