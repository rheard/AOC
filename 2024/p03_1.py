import re

pattern = r"mul\((\d{1,3}),(\d{1,3})\)"

with open('p03.txt') as rb:
    data = rb.read()

matches = re.findall(pattern, data)

int_matches = [(int(x), int(y)) for x, y in matches]

total = sum(x * y for x, y in int_matches)
print(total)
