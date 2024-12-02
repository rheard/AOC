with open('p02.txt') as rb:
    reports = [[int(x) for x in l.split()] for l in rb]

def evaluate_report(r):
    if r[0] < r[1]:
        increasing = True
    elif r[0] > r[1]:
        increasing = False
    else:
        # Not increasing or decreasing
        return False

    limit = r[0]
    for level in r[1:]:
        if increasing:
            if level <= limit:
                return False
            difference = level - limit
        else:
            if level >= limit:
                return False
            difference = limit - level
        if not (1 <= difference <= 3):
            return False
        limit = level

    return True


total = sum(1 for report in reports if evaluate_report(report))
print(total)
