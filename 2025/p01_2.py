position = 50

with open("p01.txt") as rb:
    movements = rb.readlines()


zero_points = 0
at_zero = False
for move in movements:
    direction, amount = move[0], move[1:]
    modifier = 1 if direction == "R" else -1

    movement = int(amount.strip())

    zero_points += movement // 100  # This was the annoying part I was missing; data contains rotations larger than 100
    movement %= 100
    position += modifier * movement

    if position >= 100 and not at_zero:
        zero_points += 1
    elif position <= 0 and not at_zero:
        zero_points += 1

    position %= 100
    at_zero = position == 0


print(zero_points)
