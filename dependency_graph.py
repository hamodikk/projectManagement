import networkx as nx
import matplotlib.pyplot as plt

# Define task dependencies
edges = [
    ("A", "C"), ("A", "D1"),
    ("D1", "D2"), ("D1", "D3"),
    ("D2", "D4"), ("D3", "D4"),
    ("D4", "D5"), ("D4", "D6"),
    ("D6", "D7"), ("D5", "D8"), ("D7", "D8"),
    ("B", "E"), ("C", "E"),
    ("D8", "F"), ("E", "F"),
    ("A", "G"), ("D8", "G"),
    ("F", "H"), ("G", "H")
]

# Create a directed graph
G = nx.DiGraph()
G.add_edges_from(edges)

# Draw the graph
plt.figure(figsize=(10, 6))
pos = nx.spring_layout(G, seed=42)  # Position nodes for readability
nx.draw(G, pos, with_labels=True, node_color="lightblue", edge_color="black", 
        node_size=2500, font_size=10, font_weight="bold", arrowsize=15)
plt.title("Task Dependency Graph")
plt.show()