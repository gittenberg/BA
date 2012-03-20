import itertools
import copy
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

def is_isomorphic(network1, network2):
    return True

comparematrix = np.asarray([[1., -1.,  1.], [1., -1., -1.], [1.,  0.,  0.]])
unique_networks = copy.copy(networks) # to be reduced

for count1, network1 in enumerate(networks):
    print "considering network no.", count1
    nmr1 = network_matrix_representation(nodes, network1)
    for count2, network2 in enumerate(networks):
        if count2 > count1:
            eplus1 = len([edge for edge in network1 if network1[edge]=='+'])
            eplus2 = len([edge for edge in network2 if network2[edge]=='+'])
            ezero1 = len([edge for edge in network1 if network1[edge]=='0'])
            ezero2 = len([edge for edge in network2 if network2[edge]=='0'])
            if eplus1 == eplus2 and ezero1 == ezero2:
                for perm in itertools.permutations(range(len(nodes))):
                    # shuffle matrix belonging to network2 and compare to network1
                    nmr2 = network_matrix_representation(nodes, network2)
                    shuffle = permute_array(nmr2, perm)
                    if np.all(shuffle == nmr1): # the shuffle of network2 equals network1
                        try:
                            unique_networks.remove(network2)
                            networks.remove(network2)
                        except:
                            pass
                        print "network", count2, "is isomorphic to network", count1

# pickle for later use
######################################################################
pickle.dump(networks, file("allnetworks.txt", "w" ))
pickle.dump(unique_networks, file("unique_networks.txt", "w" ))
#filecontent = pickle.load(file("allnetworks.txt"))
#print filecontent