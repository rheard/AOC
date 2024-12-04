with open('p04.txt') as rb:
    data = [list(l) for l in rb]

def verify_x_i(matrix, i_y, i_x):
    if matrix[i_y][i_x] != 'A':
        return False

    a, b, c, d = matrix[i_y - 1][i_x - 1], matrix[i_y - 1][i_x + 1], matrix[i_y + 1][i_x - 1], matrix[i_y + 1][i_x + 1]
    if a == d or b == c:
        return False

    return ['M', 'M', 'S', 'S'] == sorted([a, b, c, d])

instances = 0

for row_i in range(1, len(data) - 1):
    for col_i in range(1, len(data[0]) - 1):
        if verify_x_i(data, row_i, col_i):
            instances += 1

print(instances)
