from itertools import product

with open('p07.txt') as rb:
    data = []

    for l in rb:
        num, targets = l.split(':')
        data.append((int(num), [int(x) for x in targets.strip().split(' ')]))

def calculate_result(values, operators):
    result = values[0]
    for value, operator in zip(values[1:], operators):
        if operator == '+':
            result += value
        elif operator == '*':
            result *= value
    return result

total = 0
for num, targets in data:
    for combo in product('*+', repeat=len(targets) - 1):
        calced_val = calculate_result(targets, combo)
        if calced_val == num:
            total += calced_val
            break


print(total)