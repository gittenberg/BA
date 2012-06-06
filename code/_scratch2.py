
import networkx as nx

G=nx.DiGraph()
G.add_edges_from([(1,2),(1,3)])

print G.edges()

for line in nx.generate_edgelist(G, data=False):
    print line
    
    
Gstring = "_".join(nx.generate_edgelist(G, data=False))

print Gstring

lines = Gstring.split("_")
print lines

H=nx.DiGraph()
H.add_edges_from(nx.parse_edgelist(lines, nodetype = int).edges())
#H = nx.parse_edgelist(lines, nodetype = int)
print H.edges()

print nx.is_isomorphic(H, G)
print H==G
