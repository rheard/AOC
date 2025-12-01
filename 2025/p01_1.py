position = 50

with open("p01.txt") as rb:
    movements = rb.readlines()


zero_points = 0
for move in movements:
    direction, amount = move[0], move[1:]
    modifier = 1 if direction == "R" else -1

    position += modifier * int(amount.strip())
    position %= 100

    if position == 0:
        zero_points += 1

print(zero_points)
