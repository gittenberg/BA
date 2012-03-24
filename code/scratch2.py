from datetime import datetime

tstart = datetime.now()

import pickle
import networkx as nx

from graphenumerator import convert_dict_to_graphs

ic = pickle.load(file("isomorphy_classes.txt"))
#print len(ic)

unique_networks = pickle.load(file("unique_networks.txt"))
#print len(unique_networks)

G = convert_dict_to_graphs(unique_networks, addzeros=False)

for netID in range(20):
    #print G[netID].edges()
    print(nx.is_connected(G[netID].to_undirected()))

print G[netID].edges()

#count[label] = len([edge for edge in network1 if network1[edge]==label])

tend = datetime.now()
print "total execution time:", tend-tstart
print "done."

