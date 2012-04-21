from datetime import datetime
tstart = datetime.now()

import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import *

if os.name != 'nt':
    print "running on linux."
    path="/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
elif os.name == 'nt':
    print "running on windows."
    path="C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
    #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop

filters = {}

filters["with_morphogene"] = {
                        0:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                        1:["((m1=0&m2=0)->EF(AG(gg=0)))&((m1=0&m2=1)->EF(AG(gg=1)))&((m1=1&m2=0)->EF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, EFAG
                        2:["((m1=0&m2=0)->AF(AG(gg=0)))&((m1=0&m2=1)->AF(AG(gg=1)))&((m1=1&m2=0)->AF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, AFAG
                        3:["((m1=0&m2=0)->EF(AG(gg=0)))&((m1=0&m2=1)->EF(AG(gg=1)))&((m1=1&m2=0)->EF(AG(gg=0)))", "exists", "CTL"],
                        # morphogene BCs, exists, EFAG
                        4:["((m1=0&m2=0)->AF(AG(gg=0)))&((m1=0&m2=1)->AF(AG(gg=1)))&((m1=1&m2=0)->AF(AG(gg=0)))", "exists", "CTL"]
                        # morphogene BCs, exists, AFAG
                      }

filters["without_morphogene"] = {
                        0:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                        1:["((rr=0)->EF(AG(gg=0)))&((rr=1)->EF(AG(gg=1)))&((rr=1)->EF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, EFAG
                        2:["((rr=0)->AF(AG(gg=0)))&((rr=1)->AF(AG(gg=1)))&((rr=1)->AF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, AFAG
                        3:["((rr=0)->EF(AG(gg=0)))&((rr=1)->EF(AG(gg=1)))&((rr=1)->EF(AG(gg=0)))", "exists", "CTL"],
                        # morphogene BCs, exists, EFAG
                        4:["((rr=0)->AF(AG(gg=0)))&((rr=1)->AF(AG(gg=1)))&((rr=1)->AF(AG(gg=0)))", "exists", "CTL"]
                        # morphogene BCs, exists, AFAG
                      }

if __name__=='__main__':
    mode = "without_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    # create database
    con = create_database(path, dbname="filter_results."+mode+".db")
    
    # create tables
    create_tables(con)
    
    for nwkey in networks:
        #if nwkey >= 100: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        try:
            mc = dict_to_model(networks[nwkey], add_morphogene)
        except:
            # this should never happen
            print "failing to translate network to model, continuing."
            continue
        IG = mc._IG
        #print nwkey, ":", len(mc._psc), "parameter sets."

        lpss = mc._psc._localParameterSets
        nodes = IG.nodes()
        preds = dict([(node, IG.predecessors(node)) for node in nodes]) # dict containing node:[preds of node]

        print "===================================================================================="
        print "database operations"

        # write nwkey to database
        insert_network(con, nwkey, str(nwkey))
        
        # write interaction graph to database
        edges = IG.edges()
        interactions = mc._edgeLabels
        thresholds = mc._thresholds
        insert_edges(con, nwkey, edges, interactions, thresholds)

        # write nodes to database
        insert_nodes(con, nwkey, nodes)

        # write contexts to database
        insert_contexts(con, nwkey, nodes, preds)        

        # write local parameter sets to database
        insert_local_parameter_sets(con, nwkey, nodes, preds, lpss)
        
        # write global parameter sets to database
        gpss = mc._psc.get_parameterSets()
        insert_global_parameter_sets(con, nwkey, gpss)
        
        for filterID in filters[mode]:
            mc = dict_to_model(networks[nwkey], add_morphogene)
            formula, searchtype, logictype = filters[mode][filterID]
    
            if logictype=="AL":
                mc.filter_byAL(formula)
            elif logictype=="CTL":
                mc.filter_byCTL(formula, search=searchtype)
                
            # write filter details to database
            store_filter(con, nwkey, filterID, formula, searchtype, logictype)        
            
            # write filter results to database
            gpss = mc._psc.get_parameterSets()
            insert_filter_results(con, nwkey, gpss, filterID)

        tend = datetime.now()
        print "total execution time:", tend-tstart
    
    print "done."
    