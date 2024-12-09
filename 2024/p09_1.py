# Step 1: Load data
with open('p09.txt') as rb:
    data = [int(x) for x in rb.read().strip()]

# Build the disk:
disk_map = []
for i in range(0, len(data), 2):
    file_blocks = data[i]
    disk_map.extend([str(i // 2)] * file_blocks)
    if i + 1 != len(data):
        free_blocks = data[i + 1]
        disk_map.extend(['.'] * free_blocks)

# Step 2: Solve the problem
# Defrag:
for i in range(len(disk_map) - 1, -1, -1):
    if disk_map[i] == '.':
        continue

    next_pos = disk_map.index('.')
    if next_pos > i:
        break
    disk_map[i], disk_map[next_pos] = disk_map[next_pos], disk_map[i]

# Compute checksum:
total = 0
for val_i, val in enumerate(disk_map):
    if val == '.':
        break
    total += val_i * int(val)

print(total)