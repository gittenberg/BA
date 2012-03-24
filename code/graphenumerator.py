from datetime import datetime

tstart = datetime.now()

import itertools
import copy
import networkx as nx
import pickle

def generate_all_networks():
    # generate all 3^9 = 19683 combinations of networks
    ######################################################################
    print "generating all networks...",
    nodes = ["bb", "gg", "rr"]
    labels = ["-", "0", "+"]
    edges = [(node1, node2) for node1 in nodes for node2 in nodes]
    labelcombinations = itertools.product(labels, repeat=len(edges)) # all combinations of len(edges) labels
    networks = [dict(zip(edges, labelcombination)) for labelcombination in labelcombinations]
    pickle.dump(networks, file("allnetworks.txt", "w" ))
    print "done."

def convert_dict_to_graphs(networks, addzeros=True):
    # create digraph with labels from dictionary
    print "converting dictionaries to graphs...",
    G = dict() # dictionary of digraphs
    for netID, net in enumerate(networks):
        G[netID] = nx.DiGraph()
        for edge in net:
            if net[edge]!='0' or addzeros:
                G[netID].add_edge(edge[0], edge[1], label=net[edge])
                #print edge[0], edge[1], G[netID][edge[0]][edge[1]]
    print "done."
    return G
    
def check_isomorphism(networks):
    # check for isomorphism
    ######################################################################
    print "checking networks for isomorphism..."
    G = convert_dict_to_graphs(networks)
    
    def label_match(label1, label2):
        return label1==label2
    
    # loop through all pairs of networks and check for isomorphy
    # takes about 6 hrs
    unique_networks = copy.copy(networks)
    skiplist = []
    isomorphy_classes = {}
    for netID1 in range(len(networks)):
        if netID1 not in skiplist:
            isomorphy_classes[netID1] = [netID1]
            for netID2 in range(netID1+1, len(networks)):
                if netID2 not in skiplist:
                    if nx.is_isomorphic(G[netID1], G[netID2], node_match=None, edge_match=label_match):
                        try:
                            unique_networks.remove(networks[netID2])
                            skiplist.append(netID2)
                            isomorphy_classes[netID1].append(netID2)
                        except:
                            pass
            print "isomorphy_classes[", netID1, "] =", isomorphy_classes[netID1]
        tend = datetime.now()
        print "total execution time:", tend-tstart
    
    print "pickling", len(unique_networks), "unique networks."
    pickle.dump(unique_networks, file("unique_networks.txt", "w"))
    print "pickling", len(isomorphy_classes), "isomorphy classes."
    pickle.dump(isomorphy_classes, file("isomorphy_classes.txt", "w"))
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."

if __name__ == '__main__':
    generate_all_networks()
    networks = pickle.load(file("allnetworks.txt"))
    networks = networks[:500] # enable for quick check
    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained
    check_isomorphism(networks)
