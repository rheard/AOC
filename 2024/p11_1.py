# Step 1: Load data
with open('p11.txt') as rb:
    data = list(int(x) for x in rb.readline().strip().split())

def blink(data_set):
    for i in range(len(data_set)):
        stone = data_set[i]
        if stone == 0:
            data_set[i] = 1
        elif len(str_stone := str(stone)) % 2 == 0:
            half_i = len(str_stone) // 2
            data_set[i] = int(str_stone[:half_i])
            data_set.append(int(str_stone[half_i:]))
        else:
            data_set[i] *= 2024

for _ in range(25):
    blink(data)

print(len(data))
