# Step 1: Load data
with open('p11.txt') as rb:
    data = list(x for x in rb.readline().strip().split())

stone_level_cache = {}

def stone_count(stone, _blink_cnt=0, max_blinks=75) -> int:
    """How many stones does the input stone become after max_blinks? _blink_cnt is how many blinks have been passed"""
    cache_key = (stone, _blink_cnt)
    if cache_key in stone_level_cache:
        return stone_level_cache[cache_key]

    if _blink_cnt == max_blinks:
        stone_level_cache[cache_key] = 1
        return 1

    if stone == '0':
        cache_key = ('1', _blink_cnt + 1)
        stone_level_cache[cache_key] = stone_count(*cache_key)
        return stone_level_cache[cache_key]

    elif len(stone) % 2 == 0:
        mid = len(stone) // 2
        first = stone[:mid]
        second = str(int(stone[mid:]))

        stone_level_cache[(first, _blink_cnt + 1)] = stone_count(first, _blink_cnt + 1)
        stone_level_cache[(second, _blink_cnt + 1)] = stone_count(second, _blink_cnt + 1)

        return stone_level_cache[(first, _blink_cnt + 1)] + stone_level_cache[(second, _blink_cnt + 1)]

    else:
        cache_key = (str(2024 * int(stone)), _blink_cnt + 1)
        stone_level_cache[cache_key] = stone_count(*cache_key)
        return stone_level_cache[cache_key]


total = sum(stone_count(stone, max_blinks=75) for stone in data)
print(total)
