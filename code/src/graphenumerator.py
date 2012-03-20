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
#print len(networks) # 3^9 = 19683


# check for isomorphism
######################################################################
def network_matrix_representation(nodelist=None, network=None):
    '''Returns (node x node) matrix with +1 for activation, -1 for inhibition, 0 for no interaction'''
    nwmatrep = np.zeros((len(nodelist),len(nodelist)))
    for mi, m in enumerate(nodelist):
        for nj, n in enumerate(nodelist):
            nwmatrep[mi, nj] = labels.index(network[(m, n)]) - 1
            # here the ordering of labels matters
    return np.asmatrix(nwmatrep)

def permute_array(MM, perm):
    tempMM0 = np.asarray(MM)
    tempMM1 = np.asarray([tempMM0[i, :] for i in perm])
    tempMM2 = np.asarray([tempMM1[:, i] for i in perm])
    return tempMM2

# Later: loop over all networks and remove equivalent ones; recount

example_network = networks[19000]
nmr = network_matrix_representation(nodes, example_network)

for perm in itertools.permutations(range(len(nodes))):
    print permute_array(nmr, perm)

# pickle for later use
######################################################################
pickle.dump(networks, file("allnetworks.txt", "w" ))
#filecontent = pickle.load(file("allnetworks.txt"))
#print filecontent