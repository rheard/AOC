from collections import defaultdict

with open('p01.txt') as rb:
    left_data, right_data = zip(*(map(int, line.split()) for line in rb))

parsed_entries = defaultdict(int)
for rd in right_data:
    parsed_entries[rd] += 1

total = sum(parsed_entries[entry] * entry for entry in left_data)
print(total)
