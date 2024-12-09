# Step 1: Load data
with open('p09.txt') as rb:
    data = [int(x) for x in rb.read().strip()]

# Build the disk:
disk_map = []
max_file_id = 0
for i in range(0, len(data), 2):
    file_blocks = data[i]
    max_file_id = i // 2
    disk_map.extend([str(max_file_id)] * file_blocks)
    if i + 1 != len(data):
        free_blocks = data[i + 1]
        disk_map.extend(['.'] * free_blocks)


# Step 2: Solve the problem
# Defrag:
def find_space(data_input, data_length):
    """Find free space of length data_length"""
    for input_i, char in enumerate(data_input):
        if char != '.':
            continue
        for j in range(data_length):
            if data_input[input_i + j] != '.':
                break
        else:
            return input_i

    return None


def swap_block(data_input, data_length, source, target):
    """Swap the source block of length data_length with the target block"""
    data_input[target:target + data_length], data_input[source:source + data_length] \
        = data_input[source:source + data_length], data_input[target:target + data_length]


def find_block(data_input, block_id):
    """Find the start position and length of block with block ID block_id"""
    block_id = str(block_id)
    start = data_input.index(block_id)
    leng = 0
    while start + leng < len(data_input) and block_id == data_input[start + leng]:
        leng += 1
    return start, leng


for b in range(max_file_id, 0, -1):
    this_block_start, block_len = find_block(disk_map, b)
    next_pos = find_space(disk_map, block_len)
    if next_pos is None or next_pos > this_block_start:
        continue

    swap_block(disk_map, block_len, this_block_start, next_pos)

# Compute checksum:
total = 0
for val_i, val in enumerate(disk_map):
    if val == '.':
        continue
    total += val_i * int(val)

print(total)