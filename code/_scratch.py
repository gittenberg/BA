
import imp
import os
from os.path import join, exists
import networkx as nx
from _03_database_functions import encode_gps, encode_gps_full

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if __name__=='__main__':
    # setup objects
    networks = dict()
    interactions = dict()
    thresholds = dict()
    filters = dict()
    valueConstraints = dict()
    dynamics = dict()
    
    # example network: graph A in figure 2 of Cotterel/Sharpe
    # strict edge labels, without morphogene, green activated earlier than blue
    networks[1] = '(A) Incoherent type 1 feed-forward, with self-loop on rr @ threshold = 1'
    interactions[1] = {("rr","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[1] = {("rr","rr"):1, ("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}

    edges = dict(zip(interactions.keys(), [interactions[key].keys() for key in interactions.keys()]))
    # this dict = {key : [(edgestart, edgeend), ...]}
    nodes = dict() # will be initialized below
    
    # main loop over different regulatory networks:
    for nwkey in networks:
        print "===================================================================================="
        print "Considering network:", networks[nwkey]

        # set up IG, MC, PSC
        IG = nx.DiGraph()
        if edges.has_key(nwkey):
            IG.add_edges_from(edges[nwkey])
                    
        mc = MC.ModelContainer()
        mc.set_IG(IG)

        if interactions.has_key(nwkey):
            mc.set_edgeLabels(interactions[nwkey])

        if thresholds.has_key(nwkey):
            mc.set_thresholds(dict((edge, thresholds[nwkey][edge]) for edge in edges[nwkey]))

        mc.set_initialStates()
        
        if valueConstraints.has_key(nwkey):
            mc.set_valueConstraints(valueConstraints[nwkey])

        if dynamics.has_key(nwkey):
            mc.set_dynamics(dynamics[nwkey])
        else:
            mc.set_dynamics("asynchronous")
        
        mc.initializePSC()
            
        lpss = mc._psc._localParameterSets
        #print len(mc._psc)
        nodes[nwkey] = lpss.keys()
        preds = dict([(node, IG.predecessors(node)) for node in nodes[nwkey]]) # dict containing node:[preds of node]

        '''
        for node in lpss:
            print "node:", node
            print "=========="
            for lps in lpss[node]:
                print "lps:", lps
                print "lpsID:", encode_lps(preds[node], lps, base=10)
                print "decoded lpsID:", decode_lps(node, preds[node], encode_lps(preds[node], lps, base=10), base=10)
        '''
        
        # write global parameter sets to database
        gpss = mc._psc.get_parameterSets()
        
        print "===================================================================================="

        mc.initializePSC()
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            print gps
            print encode_gps(gps, base=10)
            print encode_gps_full(gps, base=10)
            #print decode_gps(encode_gps(gps, base=10), IG, base=10)
            #print TS.TransitionSystem(mc, gps)
            print "===================================================================================="

        #mc.export_commonSTG(Type="transitions", filename="A_commonSTG_transitions_strict.gml", initialRules=None)

    print "Done."
