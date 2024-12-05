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

def fix_ordering(ordering):
    """
    Returns:
        bool: Needed fixing?
    """
    for rule, targets in rules.items():
        if rule not in ordering:
            continue

        rule_i = ordering.index(rule)
        for target in targets:
            if target not in ordering:
                continue

            target_i = ordering.index(target)
            if rule_i > target_i:
                ordering[rule_i], ordering[target_i] = ordering[target_i], ordering[rule_i]
                fix_ordering(ordering)  # Recursively keep fixing any problems
                return True

    return False

total = 0
for ordering_ in orderings:
    if not fix_ordering(ordering_):
        continue

    total += ordering_[len(ordering_) // 2]

print(total)
