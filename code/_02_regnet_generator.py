from datetime import datetime
tstart = datetime.now()

import cPickle
import os
import imp
import networkx as nx
#import shelve
from shove import Shove

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if os.name!='nt':
    print "running on linux."
    path = "/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV" # Linux
elif os.name=='nt':
    print "running on windows."
    path = "C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                  # Samsung laptop
    #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"         # Acer laptop
    
def dict_to_model(net, thresholds=None, add_morphogene=True):
    ''' Convert single net in dict format to model in ModelContainer format '''
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
    if not thresholds:
        thresholds = dict((edge, 1) for edge in edges) # all thresholds are set to 1 unless stated otherwise
    else:
        thresholds[("m1","m1")] = 1
        thresholds[("m1","rr")] = 1
        thresholds[("m2","m2")] = 1
        thresholds[("m2","rr")] = 1
    mc.set_thresholds(thresholds) 
    #print mc._thresholds
    mc._NuSMVpath = nusmvpath
    mc.set_initialStates()
    #mc.initializePSC() #obsolete, now using settings as follows:
    settings = dict(interactions={'edges':edges, 'thresholds':thresholds, 'labels':labels},
                    componentConstraints=dict(valueConstraints=dict(),
                                              takeMin=[],
                                              takeMax=[],
                                              Bformulas=[],
                                              simplified=[],
                                              extendedValueConstraints={'rr': {('m1', 'm2'): [1]}, 'bb':{}, 'gg':{}}),
                                              #extendedValueConstraints={'rr': {('m1', 'm2'): [1]}}),
                                              #extendedValueConstraints={}),
                    priorityClasses={},
                    priorityTypes={},
                    dynamics="asynchronous",
                    unitary=True,
                    CTLformula='',
                    search='',
                    PCTLformula='',
                    attractorLogic='',
                    filterExtreme=None)
    mc.parameterSetup(settings)
    return mc


def setup_models(networks, add_morphogene=True):
    ''' Convert dict of networks in networkx format to models in ModelContainer format (batch mode) '''
    ''' This runs out of memory on the laptop. '''
    models_dict_name = "models_dictionary.db"
    #models_dict = shelve.open(models_dict_name)
    models_dict = Shove("file://"+models_dict_name, compress=True)
    for localparset, net in enumerate(networks.values()):
        print localparset, ":",
        #if localparset>=50: break # enable for quick run
        mc = dict_to_model(net, add_morphogene)
        print len(mc._psc), "parameter sets, shoving."
        if not localparset%10:
            tend = datetime.now()
            print "total execution time:", tend-tstart
        models_dict[str(localparset)] = mc
        models_dict.sync()
    #models_dict.close()
    print "shoved", localparset+1, "model containers to", models_dict_name, "."


if __name__=='__main__':
    mode = "with_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    '''
    # only printing    
    for nwkey in networks:
        mc = dict_to_model(networks[nwkey], add_morphogene)
        print nwkey, ":", len(mc._psc), "parameter sets."
        if not nwkey%10:
            tend = datetime.now()
            print "total execution time:", tend-tstart
    '''    
    #print "found", len(models_dict), "models."
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
