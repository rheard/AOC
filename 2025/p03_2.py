def max_k_digits(digits, k):
    """Given a list of integers, return the largest number that can be formed by picking any k digits"""
    n = len(digits)
    digits_to_remove = n - k

    best = []
    for d in digits:
        # While the last digit is smaller than this digit (and we can still remove digits),
        while digits_to_remove > 0 and best and best[-1] < d:
            # remove it to replace with this digit.
            best.pop()
            digits_to_remove -= 1

        best.append(d)

    return digits_to_int(best[:k])  # only largest k digits needed


def digits_to_int(digits):
    """Just convert a list like [1, 2, 3] to a number like 123"""
    value = 0
    for d in digits:
        value = value * 10 + d
    return value


# Step 1: Load data and format into data structure:
with open("p03.txt") as rb:
    battery_banks = [[int(x) for x in l.strip()] for l in rb.readlines()]


# Step 2: Solve the problem
answer = sum(max_k_digits(bank, 12) for bank in battery_banks)


# Step 3: Output answer
print(answer)
