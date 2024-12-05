from collections import defaultdict

with open('p05.txt') as rb:
    rules = defaultdict(set)
    orderings = []

    while (line := rb.readline().strip()):
        a, b = line.split('|')
        a, b = int(a), int(b)
        rules[a].add(b)

    while (line := rb.readline().strip()):
        orderings.append([int(x) for x in line.split(',')])

total = 0
for ordering in orderings:
    works = True
    for rule, targets in rules.items():
        if rule not in ordering:
            continue

        rule_i = ordering.index(rule)
        for target in targets:
            if target not in ordering:
                continue

            target_i = ordering.index(target)
            if rule_i > target_i:
                works = False
                break

        if not works:
            break

    if not works:
        continue

    total += ordering[len(ordering) // 2]


print(total)
