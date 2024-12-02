with open('p02.txt') as rb:
    reports = [[int(x) for x in l.split()] for l in rb]

def remove_i(r, i):
    """Remove level with index i from report"""
    return r[:i] + r[i + 1:]

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

# Its a good thing AOC is dead simple, otherwise this would actually need to be efficient
total = 0
for report in reports:
    if evaluate_report(report):
        total += 1
        continue

    for i in range(len(report)):
        if evaluate_report(remove_i(report, i)):
            total += 1
            break
            
print(total)
