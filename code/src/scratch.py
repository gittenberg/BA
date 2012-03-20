from datetime import datetime

tstart = datetime.now()

import pickle
import copy
import itertools
import numpy as np

nets = pickle.load(file("allnetworks.txt"))
nets = nets[0:400]
unique_nets = copy.copy(nets)

nodes = ["bb", "gg", "rr"]
labels = ["-", "0", "+"]

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
    count1 = dict()
    count2 = dict()
    for label in labels:
        count1[label] = len([edge for edge in network1 if network1[edge]==label])
        count2[label] = len([edge for edge in network2 if network2[edge]==label])
        if count1[label] != count2[label]: return False
    nmr1 = network_matrix_representation(nodes, network1)
    for perm in itertools.permutations(range(len(nodes))):
        # shuffle matrix belonging to network2 and compare to network1
        nmr2 = network_matrix_representation(nodes, network2)
        shuffle = permute_array(nmr2, perm)
        if np.all(shuffle == nmr1): # the shuffle of network2 equals network1
            print shuffle - nmr1
            return True
    return False

for num1, net1 in enumerate(nets):
    for num2, net2 in enumerate(nets):
        if num2 > num1:
            if is_isomorphic(net1, net2):
                print "isomorphic:", num1, num2
                #print len([edge for edge in net if net[edge]=='+'])    
                #print len([edge for edge in net if net[edge]=='0'])
                #print len([edge for edge in net if net[edge]=='-'])
    
tend = datetime.now()
print tend-tstart
