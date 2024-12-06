with open('p06.txt') as rb:
    data = [list(l) for l in rb]

x, y = 0, 0
for y in range(len(data)):
    if '^' in data[y]:
        x = data[y].index('^')
        break

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

    if next_spot[0] < 0 or next_spot[1] < 0 or next_spot[0] >= len(data[0]) or next_spot[1] >= len(data):
        break

    next_spot_data = data[next_spot[1]][next_spot[0]]
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

    data[y][x] = 'X'
    x, y = next_spot

total = sum(r.count('X') for r in data)  # 4938     664   666      665        4939
print(total)
