import imp
import os
import networkx as nx 

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if __name__=='__main__':
    # this is graph A in figure 2 of Cotterel/Sharpe
    interactions = {("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    edges = interactions.keys()
    mc = MC.ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
    mc.set_IG(IG)
    for edge in edges:
        mc.set_thresholds(dict((edge, 1) for edge in edges))
    mc.set_edgeLabels(interactions)
    mc.compute_constraint_parameterSets()
    mc.set_initialStates()
    mc.initializePSC()
    
    psc = mc._psc._localParameterSets
    print "PSC:",len(psc)
    
    for set in psc:
        print set, psc[set]

    #print psc

    print "Done."