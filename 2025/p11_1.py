def find_all_paths(
    graph,
    start: str = "you",
    goal: str = "out",
) -> int:
    """
    Find all possible paths from `start` to `goal` in a directed graph.

    Args:
        graph: Dict mapping node -> list of neighbor nodes.
        start: Starting node name ("you" by default).
        goal:  Goal node name ("out" by default).

    Returns:
        The number of possible paths from `start` to `goal`.
    """
    def dfs(node: str) -> int:
        # If we reached the goal, record this path
        if node == goal:
            return 1

        ans = 0
        for neighbor in graph.get(node, []):
            ans += dfs(neighbor)

        return ans

    return dfs(start)


# Step 1: Load data and format into data structure:
with open("p11.txt") as rb:
    entries = {}
    for l in rb.readlines():
        k, rest = l.strip().split(":")
        entries[k.strip()] = list(rest.strip().split())


# Step 2: Solve the problem
answer = find_all_paths(entries)


# Step 3: Output answer
print(answer)
