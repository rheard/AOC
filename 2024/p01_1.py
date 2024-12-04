with open('p01.txt') as rb:
    left_data, right_data = zip(*(map(int, line.split()) for line in rb))

left_data = sorted(left_data)
right_data = sorted(right_data)

total = sum(rd - ld if rd > ld else ld - rd for ld, rd in zip(left_data, right_data))
print(total)