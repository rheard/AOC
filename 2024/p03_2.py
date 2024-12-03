import re

pattern = r"(do\(\)|don't\(\))"

with open('p03.txt') as rb:
    data = rb.read()

split_data = re.split(pattern, data)
enabled = True
pattern = r"mul\((\d{1,3}),(\d{1,3})\)"
total = 0

for match in split_data:
    if match == 'do()':
        enabled = True
        continue
    if match == "don't()":
        enabled = False
        continue
    if not enabled or not match.strip():
        continue

    matches = re.findall(pattern, match)

    int_matches = [(int(x), int(y)) for x, y in matches]

    total += sum(x * y for x, y in int_matches)
print(total)
