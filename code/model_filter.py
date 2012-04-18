from datetime import datetime
tstart = datetime.now()

import cPickle
#from shove import Shove
from database_functions import *
from regnet_generator import dict_to_model

if os.name != 'nt':
    print "running on linux."
    path="/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
elif os.name == 'nt':
    print "running on windows."
    path="C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
    #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop

filters_for_3_gene_networks = {
                        0:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                        1:["((m1=0&m2=0)->EF(AG(gg=0)))&((m1=0&m2=1)->EF(AG(gg=1)))&((m1=1&m2=1)->EF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, EFAG
                        2:["((m1=0&m2=0)->AF(AG(gg=0)))&((m1=0&m2=1)->AF(AG(gg=1)))&((m1=1&m2=1)->AF(AG(gg=0)))", "forAll", "CTL"],
                        # morphogene BCs, forAll, AFAG
                        3:["((m1=0&m2=0)->EF(AG(gg=0)))&((m1=0&m2=1)->EF(AG(gg=1)))&((m1=1&m2=1)->EF(AG(gg=0)))", "exists", "CTL"],
                        # morphogene BCs, exists, EFAG
                        4:["((m1=0&m2=0)->AF(AG(gg=0)))&((m1=0&m2=1)->AF(AG(gg=1)))&((m1=1&m2=1)->AF(AG(gg=0)))", "exists", "CTL"],
                        # morphogene BCs, exists, AFAG
                      }

if __name__=='__main__':
    #models_dict_name = "models_dictionary.db"
    #models_dict = Shove("file://"+models_dict_name, compress=True)
    #print "found", len(models_dict), "models."
    #print models_dict.keys()
    #print models_dict['1'] # error...
    
    # wenn das mit shove nicht funktioniert, dann muss man die models eben on-the-fly machen:
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    # create database
    con = create_database(path, dbname='filter_results.db')
    
    # create tables
    create_tables(con)
    
    for nwkey in networks:
        #if nwkey >= 1000: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        try:
            mc = dict_to_model(networks[nwkey], add_morphogene=False)
        except:
            print "failing to translate network to model, continuing."
            continue
        IG = mc._IG
        print nwkey, ":", len(mc._psc), "parameter sets."

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
        
        if not nwkey%10:
            tend = datetime.now()
            print "total execution time:", tend-tstart
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
    