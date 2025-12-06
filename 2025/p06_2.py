import functools, operator

prod = lambda x: functools.reduce(operator.mul, x, 1)


# Step 1: Load data and format into data structure:
with open("p06.txt") as rb:
    data = rb.readlines()
    data, ops = data[:-1], data[-1]
    problems = []

    current_numbers = []
    current_op = None
    for i, op in enumerate(ops.strip('\n')):
        current_num = "".join(d[i] for d in data).strip()
        if op != ' ':
            if current_numbers:
                problems.append((current_op, current_numbers))
                current_numbers = []

            current_op = op

        if current_num:
            current_numbers.append(int(current_num))

    if current_numbers:
        problems.append((current_op, current_numbers))


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
