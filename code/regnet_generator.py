from datetime import datetime
tstart = datetime.now()

import cPickle
import os
import imp
import networkx as nx
import shelve

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

morphogene_interactions = {("m1","m1"):"+", ("m1","rr"):"+", ("m2","m2"):"+", ("m2","rr"):"+"}


def setup_models(networks, add_morphogene=True):
    models_dict_name = "models_dictionary.db"
    models_dict = shelve.open(models_dict_name)
    #models_dict = {} # this only for pickling, not for shelving
    for i, net in enumerate(networks.values()):
        key = str(i)
        #if i>=50: break # enable for quick run
        # first set up the internal graph:
        labels = dict((edge, label) for (edge, label) in net.items() if label!='0') # TODO: obsolete iff addzeros==False in graph_enumerator
        # then set up the morphogene edges:
        if add_morphogene:
            for edge in morphogene_interactions: # TODO: simpler way to merge dicts labels and morphogene_interactions??
                labels[edge] = morphogene_interactions[edge]
        edges = labels.keys()
        IG = nx.DiGraph()
        IG.add_edges_from(edges)
        
        mc = MC.ModelContainer()
        mc.set_IG(IG)
        mc.set_edgeLabels(labels)
        print key, ":",
        mc.set_thresholds(dict((edge, 1) for edge in edges)) # all thresholds are set to 1
        #print mc._thresholds
        mc._NuSMVpath = nusmvpath
        mc.set_initialStates()
        mc.set_dynamics("asynchronous")
        mc.initializePSC()
        print len(mc._psc), "parameter sets, shelving."
        if not i%10:
            tend = datetime.now()
            print "total execution time:", tend-tstart
        models_dict[key] = mc
    models_dict.close()
    print "shelved", i, "model containers to", models_dict_name, "."
    #cPickle.dump(models_dict, file(models_dict_name, "w"))
    
if __name__=='__main__':
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))
    #print len(networks)
    setup_models(networks)

    models_dict_name = "models_dictionary.db"
    models_dict = shelve.open(models_dict_name)
    #models = cPickle.load(file(models_dict_name)) # this only for pickling, not for shelving
    
    print "found", len(models_dict), "models."

    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
