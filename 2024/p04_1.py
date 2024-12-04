with open('p04.txt') as rb:
    data = [list(l) for l in rb]

def column_i(matrix, column_index):
    return ''.join(row[column_index] for row in matrix)

instances = 0
# Look for in row
for r in data:
    r = ''.join(r)
    instances += r.count('XMAS') + r.count('SAMX')

# Look for in column
for i in range(len(data[0])):
    c = column_i(data, i)
    instances += c.count('XMAS') + c.count('SAMX')

# Look for forward diag
for row_i in range(len(data) - 3):
    for col_i in range(len(data[0]) - 3):
        if data[row_i][col_i] + data[row_i + 1][col_i + 1] + data[row_i + 2][col_i + 2] + data[row_i + 3][col_i + 3] in ['XMAS', 'SAMX']:
            instances += 1

# Look for reverse diag
for row_i in range(len(data) - 3):
    for col_i in range(3, len(data[0])):
        if data[row_i][col_i] + data[row_i + 1][col_i - 1] + data[row_i + 2][col_i - 2] + data[row_i + 3][col_i - 3] in ['XMAS', 'SAMX']:
            instances += 1

print(instances)