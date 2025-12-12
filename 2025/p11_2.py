from functools import cache


def find_all_paths(
    graph,
    start: str = "you",
    goal: str = "out",
    required_nodes = None,
) -> int:
    """
    Find all possible paths from `start` to `goal` in a directed graph
        that visit every node in `required_nodes` at least once.

    Args:
        graph: Dict mapping node -> list of neighbor nodes.
        start: Starting node name ("you" by default).
        goal:  Goal node name ("out" by default).
        required_nodes: Iterable of node names that must appear in the path.

    Returns:
        The number of valid possible paths from `start` to `goal`.
    """
    required = list(required_nodes or ())
    # Map each required node to a bit position
    req_index = {name: i for i, name in enumerate(required)}
    # Bitmask with all required bits set (e.g., for 3 nodes -> 0b111 == 7)
    full_mask = (1 << len(required)) - 1

    @cache
    def dfs(node: str, seen_mask: int) -> int:
        """
        DFS with memoization.

        node: current node name
        seen_mask: bitmask indicating which required nodes have been visited
        """
        # If this node is one of the required ones, mark it as seen
        if node in req_index:
            bit = 1 << req_index[node]
            seen_mask |= bit

        # If we reached the goal, it is a valid path iff all required nodes are seen
        if node == goal:
            return 1 if seen_mask == full_mask else 0

        total = 0
        for neighbor in graph.get(node, []):
            total += dfs(neighbor, seen_mask)
        return total

    # Start with no required nodes seen (mask = 0)
    return dfs(start, 0)


# Step 1: Load data and format into data structure:
with open("p11.txt") as rb:
    entries = {}
    for l in rb.readlines():
        k, rest = l.strip().split(":")
        entries[k.strip()] = list(rest.strip().split())


# Step 2: Solve the problem
answer = find_all_paths(entries, start="svr", required_nodes=["dac", "fft"])


# Step 3: Output answer
print(answer)
