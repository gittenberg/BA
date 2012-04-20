
# obsolete functions
####################################################################################

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
            print network1
            print network2
            print nmr1
            print nmr2
            print shuffle
            return True
    return False


def check_isomorphism_OLD(networks, mode="_without_morphogene", tag_input_gene=False):
    ''' check for isomorphism: loop through all pairs of networks and check for isomorphy '''
    print "checking networks for isomorphism..."
    G = convert_dict_to_graphs(networks, addzeros=False)
    if tag_input_gene:
        # treat label 'rr' gene differently than others (input gene)
        print "labelling input genes in graphs...",
        for graph in G.values():
            graph.node['rr'] = 'input'
        match_fct = label_match
        print 'done.'
    else:
        match_fct = None
    
    skiplist = []
    isomorphy_classes = {}
    maxiter = len(networks)
    for netID1 in networks.keys():
        if netID1 not in skiplist:
            isomorphy_classes[netID1] = [netID1]
            for netID2 in range(netID1+1, maxiter):
                if netID2 not in skiplist:
                    if nx.is_isomorphic(G[netID1], G[netID2], node_match=match_fct, edge_match=label_match):
                        try:
                            #del networks[netID2]
                            skiplist.append(netID2)
                            isomorphy_classes[netID1].append(netID2)
                        except:
                            pass
            skiplist = list(set(skiplist)) # remove double entries
            print "isomorphy_classes[", netID1, "] =", isomorphy_classes[netID1]
        tend = datetime.now()
        print "total execution time:", tend-tstart

    unique_networks = dict()
    for netID in networks.keys():
        if isomorphy_classes.has_key(netID):
            unique_networks[netID] = networks[netID]

    picklename1 = "unique_networks" + mode + ".db"
    picklename2 = "isomorphy_classes" + mode + ".db"
    backup(picklename1)
    backup(picklename2)
    print "pickling", len(unique_networks), "unique networks to", picklename1, "."
    print "pickling", len(isomorphy_classes), "isomorphy classes to", picklename2, "."
    cPickle.dump(unique_networks, file(picklename1, "w"))
    cPickle.dump(isomorphy_classes, file(picklename2, "w"))
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done checking networks for isomorphism."


def dict_to_model(net, add_morphogene=True):
    ''' Convert single net in networkx format to model in ModelContainer format '''
    #print "converting to model:", net, "."
    # first set up the internal graph:
    labels = dict((edge, label) for (edge, label) in net.items() if label!='0') # TODO: obsolete iff addzeros==False in graph_enumerator
    # then set up the morphogene edges:
    if add_morphogene:
        morphogene_interactions = {("m1","m1"):"+", ("m1","rr"):"+", ("m2","m2"):"+", ("m2","rr"):"+"}
        for edge in morphogene_interactions: # TODO: simpler way to merge dicts labels and morphogene_interactions??
            labels[edge] = morphogene_interactions[edge]
    edges = labels.keys()
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
    
    mc = MC.ModelContainer()
    mc.set_IG(IG)
    mc.set_edgeLabels(labels)
    mc.set_thresholds(dict((edge, 1) for edge in edges)) # all thresholds are set to 1
    #print mc._thresholds
    mc._NuSMVpath = nusmvpath
    mc.set_initialStates()
    mc.set_dynamics("asynchronous")
    mc.initializePSC()
    return mc

