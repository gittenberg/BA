
import imp
import os
import networkx as nx
from _03_database_functions import *

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                  # Samsung laptop

def dict_to_model(net, add_morphogene=True, thresholds=None):
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
                                              extendedValueConstraints={'rr': {('m1', 'm2'): [1]}}),  # gibt 7 PS
                                              #extendedValueConstraints={}),                           # gibt 9 PS
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

##########################################
net = {('rr', 'bb'):'+', ('bb', 'rr'):'+'}

mc = dict_to_model(net)

gpss = mc._psc.get_parameterSets()
for gps in gpss:
    print gps
    export_STG(mc, gps, filename="test_STG_"+encode_gps(gps, base=10)+"2.gml", initialRules=None)

