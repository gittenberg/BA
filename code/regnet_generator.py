from datetime import datetime
tstart = datetime.now()

import cPickle
import os
import imp
import networkx as nx

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if os.name!='nt':
    print "running on linux."
    path = "/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
elif os.name=='nt':
    print "running on windows."
    path = "C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
    #global nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"     # Acer laptop

def setup_models(networks):
    for net in networks.values():
        labels = dict((edge, label) for (edge, label) in net if label!='0') # TODO: obsolete iff addzeros==False in graph_enumerator
        edges = net.keys()
        IG = nx.DiGraph()
        IG.add_edges_from(edges)
        
        mc = MC.ModelContainer()
        mc.set_IG(IG)
        mc.set_edgeLabels(labels)
        mc.set_thresholds(dict((edge, 1) for edge in edges)) # all thresholds are set to 1
        mc._NuSMVpath = nusmvpath
        mc.set_initialStates()
        mc.set_dynamics("asynchronous")
        mc.initializePSC()

    
if __name__=='__main__':
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))
    print len(networks)
    setup_models(networks)

    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
