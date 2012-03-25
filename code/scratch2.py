
import networkx as nx

DG=nx.DiGraph()

DG.add_edges_from([(1, 2, {'label':'blue'}), 
                   (2, 3, {'label':8})])

print DG.edges()
print DG[1][2]['label']
print DG[2]
print DG[3]




print convert_graph_to_dict(DG)

#count[label] = len([edge for edge in network1 if network1[edge]==label])

print "done."

