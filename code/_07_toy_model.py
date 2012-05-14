import imp
import os
from os.path import join, exists
import networkx as nx
from itertools import chain, combinations
import sqlite3
import itertools

from _03_database_functions import *
from _05_psc_functions import *

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))


if __name__=='__main__':

    if os.name != 'nt':
        print "running on linux."
        path="/home/bude/mjseeger/git/BA/code"
        nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
    elif os.name == 'nt':
        print "running on windows."
        path="C:\Users\MJS\git\BA\code"
        nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
        #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop

    # setup objects
    add_morphogene = False
    
    if add_morphogene:
        mode_token = 'with_morphogene'
    else:
        mode_token = 'without_morphogene'
    dbname = 'filter_results_toy_model_'+mode_token+'.db'
    verbose = True
    morphogene_interactions = {("m1","m1"):"+", ("m1","aa"):"+"}
    networks = dict()
    #labels = ["+", "-"]
    labels = ["free"]
    #edges = [('aa', 'bb'), ('bb', 'aa')] 
    edges = [('aa', 'bb'), ('bb', 'aa'), ('aa', 'aa')]
    #edges = [('aa', 'bb'), ('bb', 'aa'), ('aa', 'aa'), ('bb', 'bb')]
    all_gps_codes = []
    
    def generate_networks(edges, add_morphogene):
        print "generating all networks..."
        labelcombinations = [list(x) for x in itertools.product(labels, repeat=len(edges))] # all combinations of len(edges) labels
        if add_morphogene:
            edges.extend(morphogene_interactions.keys())
            for x in labelcombinations:
                x.extend(["+", "+"])
            
        networks = dict(enumerate(dict(zip(edges, labelcombination)) for labelcombination in labelcombinations))
    
        print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained
        print "done."
        return networks
    
    networks = generate_networks(edges, add_morphogene)
    nodes = dict() # will be initialized below
    
    # create database
    con = create_database(path, dbname)
    # create tables
    create_tables(con, verbose)

    # main loop over different regulatory networks:
    for nwkey in networks:
        print "===================================================================================="
        print "Considering network:", networks[nwkey]

        # set up IG, MC, PSC
        IG = nx.DiGraph()
        IG.add_edges_from(networks[nwkey].keys())
                    
        mc = MC.ModelContainer()
        mc._NuSMVpath = nusmvpath
        mc.set_IG(IG)
        mc.set_edgeLabels(networks[nwkey])
        thresholds = dict((edge, 1) for edge in networks[nwkey].keys())
        mc.set_thresholds(thresholds)

        mc.set_initialStates()
        mc.set_dynamics("asynchronous")
        mc.initializePSC()
            
        lpss = mc._psc._localParameterSets
        #print len(mc._psc)
        nodes[nwkey] = lpss.keys()
        preds = dict([(node, IG.predecessors(node)) for node in nodes[nwkey]]) # dict containing node:[preds of node]

        print "===================================================================================="
        print "Database operations"

        # write network to database
        insert_network(con, nwkey, str(nwkey))
        # write interaction graph to database
        insert_edges(con, nwkey, networks[nwkey].keys(), networks[nwkey], thresholds)
        # write nodes to database
        insert_nodes(con, nwkey, nodes[nwkey])
        # write contexts to database
        insert_contexts(con, nwkey, nodes[nwkey], preds)        
        # write local parameter sets to database
        insert_local_parameter_sets(con, nwkey, nodes[nwkey], preds, lpss)
        # write global parameter sets to database
        gpss = mc._psc.get_parameterSets()
        insert_global_parameter_sets(con, nwkey, gpss, verbose)
        
        print "===================================================================================="
        print "Exporting .gml..."
        mc.initializePSC()
        print "number of parameter sets:", len(mc._psc)
        #mc._psc.reject([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])
        
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            #print gps
            print strictest_labels(edges, [gps])
            all_gps_codes.append(encode_gps(gps))
            print encode_gps(gps)
            #print decode_gps(encode_gps(gps, base=10), IG, base=10)
            #print TS.TransitionSystem(mc, gps)
            export_STG(mc, gps, filename=join("gml", str(nwkey).zfill(3)+"_"+encode_gps(gps, base=10)+".gml"), initialRules=None)
            #pass

        #mc.export_commonSTG(Type="transitions", filename="A_commonSTG_transitions_strict.gml", initialRules=None)

    con.commit()
    con.close()
    
    print all_gps_codes
    # diese gps_codes jetzt in 2 Teile zerlegen:
    # den teil mit m1==0 und den teil mit m1==1.
    # hierzu:
    # welche stellen des codes gehoeren ueberhaupt zu m1
    # diese stellen streichen, es entstehen codes fuer den graphen ohne morphogen
    # diese auf duplikate ueberpruefen (es muessen ja die 72 irgendwie auf die 64 ohne morphogen abbildbar sein).
    # anschliessend die "kleinen" GPS speichern
    # neue/modifizierte CTL-Formeln aufstellen
    # model checken
    
    print len(all_gps_codes)
    print "Done."
