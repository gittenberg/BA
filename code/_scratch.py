from datetime import datetime
tstart = datetime.now()

import imp
import os
import networkx as nx
import cPickle

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                  # Samsung laptop

def dict_to_model_experimental(net, add_morphogene=True):
    ''' Convert single net in networkx format to model in ModelContainer format '''
    #print "converting to model:", net, "."
    # first set up the internal graph:
    morphogene_interactions = {("m1","m1"):"+", ("m1","rr"):"+", ("m2","m2"):"+", ("m2","rr"):"+"}
    labels = dict((edge, label) for (edge, label) in net.items() if label!='0') # TODO: obsolete iff addzeros==False in graph_enumerator
    # then set up the morphogene edges:
    if add_morphogene:
        for edge in morphogene_interactions:
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
    #mc.initializePSC()
    ###########################################################################
    # BAUSTELLE
    ###########################################################################
    interactions = {'edges':0, 'thresholds':0, 'labels':0}
    settings = {'interactions':interactions}
    mc.parameterSetup(settings)
    ###########################################################################
    # /BAUSTELLE
    ###########################################################################
    return mc

if __name__=='__main__':
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    for nwkey in networks:
        if nwkey >= 10: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        mc = dict_to_model_experimental(networks[nwkey], add_morphogene=True)
        IG = mc._IG
        print nwkey, ":", len(mc._psc), "parameter sets."

tend = datetime.now()
print "total execution time:", tend-tstart
print "done."
