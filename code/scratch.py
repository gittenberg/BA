from datetime import datetime

tstart = datetime.now()

import pickle
import copy
import itertools
import numpy as np
import networkx as nx

nets = pickle.load(file("allnetworks.txt"))
#print len(nets) # should be 3^9=19683
#nets = pickle.load(file("unique_networks.txt"))
#print len(nets) # 2889 - check what this means!!

#nets = nets[:250]
unique_nets = copy.copy(nets)

nodes = ["bb", "gg", "rr"]
labels = ["-", "0", "+"]

# create digraph with labels from dictionary
G = dict() # dictionary of digraphs
for netID, net in enumerate(nets):
    G[netID] = nx.DiGraph()
    for edge in net:
        G[netID].add_edge(edge[0], edge[1], label=net[edge])
        #print edge[0], edge[1], G[netID][edge[0]][edge[1]]

def label_match(label1, label2):
    return label1==label2

skiplist = []
isomorphy_classes = {}
for netID1 in range(len(nets)):
    if netID1 not in skiplist:
        isomorphy_classes[netID1] = [netID1]
        for netID2 in range(netID1+1, len(nets)):
            if netID2 not in skiplist:
                if nx.is_isomorphic(G[netID1], G[netID2], node_match=None, edge_match=label_match):
                    try:
                        unique_nets.remove(nets[netID2])
                        skiplist.append(netID2)
                        isomorphy_classes[netID1].append(netID2)
                    except:
                        pass
        print "isomorphy_classes[", netID1, "] =", isomorphy_classes[netID1]
    tend = datetime.now()
    print "Total execution time:", tend-tstart

print "Pickling", len(unique_nets), "unique networks."
pickle.dump(unique_nets, file("unique_networks.txt", "w"))
print "Pickling", len(isomorphy_classes), "isomorphy classes."
pickle.dump(isomorphy_classes, file("isomorphy_classes.txt", "w"))
ic = pickle.load(file("isomorphy_classes.txt"))
print ic

tend = datetime.now()
print "Total execution time:", tend-tstart
