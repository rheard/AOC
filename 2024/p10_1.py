# Step 1: Load data
with open('p10.txt') as rb:
    data = [[int(x) for x in l.strip()] for l in rb]


# Step 2: Solve the problem
def walk_trail(trail_map, start_x: int, start_y: int):
    """
    Walk the trail from the given starting point

    Returns:
        A set containing the ending positions
    """
    cur_height = trail_map[start_y][start_x]
    if cur_height == 9:
        return {(start_x, start_y)}

    near_positions = [(start_x - 1, start_y), (start_x + 1, start_y), (start_x, start_y - 1), (start_x, start_y + 1)]
    end_points = set()
    for near_pos in near_positions:
        if near_pos[0] < 0 or near_pos[1] < 0 or near_pos[0] >= len(trail_map) or near_pos[1] >= len(trail_map[0]):
            continue

        near_pos_height = trail_map[near_pos[1]][near_pos[0]]
        if near_pos_height != cur_height + 1:
            continue

        end_points |= walk_trail(trail_map, near_pos[0], near_pos[1])

    return end_points


total = 0
for s_x in range(len(data[0])):
    for s_y in range(len(data)):
        if data[s_y][s_x] == 0:
            total += len(walk_trail(data, s_x, s_y))

print(total)
