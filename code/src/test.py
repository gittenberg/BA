import imp
import os
from os.path import join
import networkx as nx #@UnresolvedImport
import sqlite3


MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

def create_database(path="C:\Users\MJS\gitprojects_2\BA\code\src", dbname='filter_results.db'):
    con = sqlite3.connect(join(path, dbname))
    return con

def create_tables(con):
    con.execute('''DROP TABLE IF EXISTS iagraphs''')
    con.execute("create table iagraphs(iagraphID INT, iagraphsName VARCHAR(50), PRIMARY KEY (iagraphID))")
    
    con.execute('''DROP TABLE IF EXISTS edges''')
    con.execute("create table edges(iagraphID INT, edgestart VARCHAR(5), edgeend VARCHAR(5), edgelabel VARCHAR(4), threshold INT, PRIMARY KEY (edgestart, edgeend))")
    
    con.execute('''DROP TABLE IF EXISTS nodes''')
    con.execute("create table nodes(iagraphID INT, node VARCHAR(5), PRIMARY KEY (node))")

    con.execute('''DROP TABLE IF EXISTS contexts''')
    con.execute("create table contexts(iagraphID INT, node VARCHAR(5))")

    con.commit()
    
def insert_network(con, nwkey, networks):
    # write interaction graph to database
    exestring = "INSERT INTO iagraphs VALUES('%s', '%s')" % (nwkey, networks)
    print exestring
    con.execute(exestring)
    con.commit()

def insert_edges(con, nwkey, edges, interactions, thresholds):
    for edge in edges:
        # write edge to database
        exestring = "INSERT INTO edges VALUES('%s', '%s', '%s', '%s', '%s')" % (nwkey, edge[0], edge[1], 
            interactions[edge], thresholds[edge])
        print exestring
        con.execute(exestring)
    con.commit()

def insert_nodes(con, nwkey, nodes):
    for node in nodes:
        # write node to database
        exestring = "INSERT INTO nodes VALUES('%s', '%s')" % (nwkey, node)
        print exestring
        con.execute(exestring)
    con.commit()

def insert_contexts(con, nwkey, nodes):
    for node in nodes:
        # write node to database
        exestring = "INSERT INTO contexts VALUES('%s', '%s')" % (nwkey, node)
        print exestring
        con.execute(exestring)
    con.commit()

if __name__=='__main__':
    # create database
    con = create_database()
    
    # create tables
    create_tables(con)
    
    # setup objects
    networks = {1:'Incoherent type 1 feed-forward'}

    # example network: strict, without morphogene
    interactions = {1:{("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}}
    thresholds = {1:{("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}}
    edges = dict(zip(interactions.keys(), [interactions[key].keys() for key in interactions.keys()]))
    nodes = dict() # will be initialized below

    # this is graph A in figure 2 of Cotterel/Sharpe
    # including "mm" doubles the number of original parameter sets and the number of filtered parameter sets
    
    # non-strict, with morphogene
    #interactions = {("mm","rr"):"obs+", ("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}

    # non-strict, without morphogene
    #interactions = {("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    
    # strict, with morphogene
    #interactions = {("mm","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    #thresholds = {("mm","rr"):1, ("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}

    # main loop over different regulatory networks:
    for nwkey in networks:
        print "Considering network:", networks[nwkey]
        print "===================================================================================="

        # set up IG, MC, PSC
        IG = nx.DiGraph()
        IG.add_edges_from(edges[nwkey])
        mc = MC.ModelContainer()
        mc._NuSMVpath = r"C:\Progra~2\NuSMV\2.5.2\bin\NuSMV.exe"
        mc.set_IG(IG)
        mc.set_edgeLabels(interactions[nwkey])
        mc.set_thresholds(dict((edge, thresholds[nwkey][edge]) for edge in edges[nwkey]))
        mc.set_initialStates()
        mc.initializePSC()
        # TODO: replacing the previous by MC.parameterSetup() would allow more flexibility like local constraints etc.
            
        # write network to database
        insert_network(con, nwkey, networks[nwkey])

        # write interaction graph to database
        insert_edges(con, nwkey, edges[nwkey], interactions[nwkey], thresholds[nwkey])

        lpss = mc._psc._localParameterSets
        print "PSC:",len(mc._psc)
        nodes[nwkey] = lpss.keys()
        
        # write nodes to database
        insert_nodes(con, nwkey, nodes[nwkey])

        for gene in lpss:
            print "======="
            print gene
            print "======="
            for lps in lpss[gene]:
                print lps
    
        # write contexts to database
        # - for each node
        # - look at predecessors
        # - enumerate 2^n subsets of predecessors (= contexts)
        # - encode in binary, e.g. '010001' means that 1st and 5th predecessor are above threshold
        # - write binary contextID to DB
        # - write string to DB that explains which predecessors are active
        insert_contexts(con, nwkey, nodes[nwkey]) # , further arguments?

        # write local parameter sets to database
        # - for each node
        # - for each contextID
        # - write list of parameter values to BD (length - all or only active ones?)
        # - or is there a better structure (string, some encoding, etc.)?
        '''
        print "============"
        print "Filtering..."
    
        CTLformula, CTLsearch = "(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll" # (left&middle&right), the gg=1 in left and middle is from the drawing on page 5
    
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=0))", "exists" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&AF(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EG(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "!(rr>0&bb>0&gg>0&EF(gg=0))", "forAll" #  12/202 bei thresholds = 1, obs* # Negation von Modell fuer linke Region 
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=1))", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer mittlere Region
        #CTLformula, CTLsearch = "EF(rr=0&bb=0&gg=1)", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer rechte Region
        
        #mc.filter_extremeAttractors('max', 'attrs', True, True)
        
        mc.filter_byCTL(CTLformula, search=CTLsearch)
    
        #ALformula = "?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.max(gg)=1)"
        #mc.filter_byAL(ALformula)
    
        for parameterSet in mc._psc.get_parameterSets():
            print parameterSet 
    
        print "============"
        print "Exporting..."
        mc.export_commonSTG(Type="transitions", filename="A_commonSTG_transitions_strict.gml", initialRules=None)
        '''
    con.commit()
    con.close()
    print "Done."
