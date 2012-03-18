import itertools
import numpy as np
import pickle

# generate all 3^9 = 19683 combinations of networks
######################################################################
nodes = ["bb", "gg", "rr"]
labels = ["-", "0", "+"]
edges = [(node1, node2) for node1 in nodes for node2 in nodes]
labelcombinations = itertools.product(labels, repeat=len(edges)) # all combinations of len(edges) labels
networks = [dict(zip(edges, labelcombination)) for labelcombination in labelcombinations]

#for i in range(10):
#    print networks[i]
#print len(networks)


# check for isomorphism
######################################################################
def network_matrix_representation(nodelist=None, network=None):
    '''Returns (node x node) matrix with +1 for activation, -1 for inhibition, 0 for no interaction'''
    nwmatrep = np.zeros((len(nodelist),len(nodelist)))
    for mi, m in enumerate(nodelist):
        for nj, n in enumerate(nodelist):
            nwmatrep[mi, nj] = labels.index(network[(m, n)]) - 1
            # in this the ordering of labels matters
    return np.asmatrix(nwmatrep)

example_network = networks[19000]
print network_matrix_representation(nodes, example_network)


# pickle for later use
######################################################################
pickle.dump(networks, file("allnetworks.txt", "w" ))
#filecontent = pickle.load(file("allnetworks.txt"))
#print filecontent