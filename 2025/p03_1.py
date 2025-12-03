def max_two_digits(digits):
    """Given a list of integers, return the largest number that can be formed by picking any two digits"""
    n = len(digits)
    max_selection: list[int | None] = [None] * n  # max digit for location
    for i, digit in enumerate(digits[:-1]):
        max_selection[i] = digits[i + 1]
        for other_digit in digits[i + 2:]:
            max_selection[i] = max(other_digit, max_selection[i])

    best = float('-inf')
    for i in range(n - 1):
        tens = digits[i]
        ones = max_selection[i]

        if ones is None:
            continue

        candidate = tens * 10 + ones
        if candidate > best:
            best = candidate

    return best


# Step 1: Load data and format into data structure:
with open("p03.txt") as rb:
    battery_banks = [[int(x) for x in l.strip()] for l in rb.readlines()]


# Step 2: Solve the problem
answer = sum(max_two_digits(bank) for bank in battery_banks)


# Step 3: Output answer
print(answer)
