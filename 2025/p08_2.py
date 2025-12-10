class DSU:
    """Disjoint-set union (union-find) with path compression + union by size."""
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        # Iterative path compression
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False  # already same component

        # Union by size
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra

        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return True


def shortest_edges(points):
    """
    Return the shortest edges between points as a list of
        (dist2, i, j), sorted by dist2 ascending.
    """
    n = len(points)
    edges = []  # max-heap on -dist2

    for i in range(n):
        x1, y1, z1 = points[i]
        for j in range(i + 1, n):
            x2, y2, z2 = points[j]
            dx = x1 - x2
            dy = y1 - y2
            dz = z1 - z2
            dist2 = dx * dx + dy * dy + dz * dz
            edges.append((dist2, i, j))

    edges.sort(key=lambda t: t[0])
    return edges


# Step 1: Load data and format into data structure:
with open("p08.txt") as rb:
    entries = [l.strip().split(",") for l in rb.readlines()]
    entries = [tuple(int(x) for x in e) for e in entries]


# Step 2: Solve the problem
n = len(entries)

edges = shortest_edges(entries)

# keep joining until 1 giant circuit
dsu = DSU(n)
components = n
i = j = None

for dist2, i, j in edges:
    if dsu.union(i, j):
        components -= 1
        if components == 1:
            break


x1 = entries[i][0]
x2 = entries[j][0]
answer = x1 * x2


# Step 3: Output answer
print(answer)
