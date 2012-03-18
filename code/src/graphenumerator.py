import itertools
#import networkx
import pickle

nodes = ["bb", "gg", "rr"]
labels = ["+", "0", "-"]
edges = [(node1, node2) for node1 in nodes for node2 in nodes]

labelcombinations = itertools.product(labels, repeat=len(edges)) # all combinations of len(edges) labels

networks = [dict(zip(edges, labelcombination)) for labelcombination in labelcombinations]

#for i in range(10):
#    print networks[i]

print len(networks)

pickle.dump(networks, file("allnetworks.py", "w" ))
filecontent = pickle.load(file("allnetworks.py"))
#print filecontent