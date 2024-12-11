from functools import cache

MAX_BLINKS = 75

# Step 1: Load data
with open('p11.txt') as rb:
    data = list(x for x in rb.readline().strip().split())

@cache
def stone_count(stone, _blink_cnt=0) -> int:
    """How many stones does the input stone become after MAX_BLINKS? _blink_cnt is how many blinks have been passed"""
    if _blink_cnt == MAX_BLINKS:
        return 1

    if stone == '0':
        return stone_count('1', _blink_cnt + 1)

    elif len(stone) % 2 == 0:
        mid = len(stone) // 2
        first = stone[:mid]
        second = str(int(stone[mid:]))

        return stone_count(first, _blink_cnt + 1) + stone_count(second, _blink_cnt + 1)

    return stone_count(str(2024 * int(stone)), _blink_cnt + 1)


total = sum(stone_count(stone) for stone in data)
print(total)
