import functools, operator

prod = lambda x: functools.reduce(operator.mul, x, 1)


def transpose(matrix):
    """Transpose a 2D list (list of rows) into a list of columns"""
    return [list(row) for row in zip(*matrix)]


# Step 1: Load data and format into data structure:
with open("p06.txt") as rb:
    problems = [l.strip().split() for l in rb.readlines()]
    problems = transpose(problems)
    problems = [(l[-1], l[:-1]) for l in problems]


# Step 2: Solve the problem
answer = 0
for op, vals in problems:
    if op == '*':
        answer += prod(int(x) for x in vals)
    elif op == '+':
        answer += sum(int(x) for x in vals)
    else:
        raise ValueError(f"unknown operator: {op}")


# Step 3: Output answer
print(answer)
