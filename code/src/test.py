import imp
import os
from os.path import join
import networkx as nx #@UnresolvedImport
from itertools import chain, combinations
import sqlite3


MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

def create_database(path="C:\Users\MJS\gitprojects_2\BA\code\src", dbname='filter_results.db'):
    con = sqlite3.connect(join(path, dbname))
    return con

def create_tables(con):
    con.execute('''DROP TABLE IF EXISTS iagraphs''')
    con.execute("create table iagraphs(iagraphID INT, iagraphsName VARCHAR(50), PRIMARY KEY (iagraphID))")
    
    con.execute('''DROP TABLE IF EXISTS edges''')
    con.execute("create table edges(iagraphID INT, edgestart VARCHAR(5), edgeend VARCHAR(5), edgelabel VARCHAR(4), threshold INT,\
        PRIMARY KEY (iagraphID, edgestart, edgeend), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID)\
        FOREIGN KEY (edgestart) REFERENCES nodes(node), FOREIGN KEY (edgeend) REFERENCES nodes(node))")
    
    con.execute('''DROP TABLE IF EXISTS nodes''')
    con.execute("create table nodes(iagraphID INT, node VARCHAR(5), PRIMARY KEY (iagraphID, node), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.execute('''DROP TABLE IF EXISTS contexts''')
    con.execute("create table contexts(iagraphID INT, node VARCHAR(5), contextID INT, context VARCHAR(100),\
        PRIMARY KEY (iagraphID, node, contextID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID), FOREIGN KEY (iagraphID, node) REFERENCES nodes(iagraphID, node))")

    con.execute('''DROP TABLE IF EXISTS localparametersets''')
    con.execute("create table localparametersets(iagraphID INT, node VARCHAR(5), lpsID INT, localparameterset VARCHAR(500),\
        PRIMARY KEY (iagraphID, node, lpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID), FOREIGN KEY (iagraphID, node) REFERENCES nodes(iagraphID, node))")

    con.execute('''DROP TABLE IF EXISTS globalparametersets''')
    con.execute("create table globalparametersets(iagraphID INT, gpsID INT, globalparameterset VARCHAR(500),\
        PRIMARY KEY (iagraphID, gpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.execute('''DROP TABLE IF EXISTS filters''')
    con.execute("create table filters(iagraphID INT, filterID INT, filterstring VARCHAR(500), filtertype VARCHAR(10), logictype VARCHAR(5),\
        PRIMARY KEY (iagraphID, filterID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.commit()
    
def insert_network(con, nwkey, networks):
    # write interaction graph to database
    exestring = "INSERT INTO iagraphs VALUES('%s', '%s')" % (nwkey, networks)
    #print exestring
    con.execute(exestring)
    con.commit()

def insert_edges(con, nwkey, edges, interactions, thresholds):
    for edge in edges:
        # write edge to database
        exestring = "INSERT INTO edges VALUES('%s', '%s', '%s', '%s', '%s')" % (nwkey, edge[0], edge[1], 
            interactions[edge], thresholds[edge])
        #print exestring
        con.execute(exestring)
    con.commit()

def insert_nodes(con, nwkey, nodes):
    for node in nodes:
        # write node to database
        exestring = "INSERT INTO nodes VALUES('%s', '%s')" % (nwkey, node)
        #print exestring
        con.execute(exestring)
    con.commit()

def insert_contexts(con, nwkey, nodes, preds):
    for node in sorted(nodes):
        for contextID, context in enumerate(powerset(sorted(preds[node]))): 
            exestring = '''INSERT INTO contexts VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, contextID, context)
            #print exestring
            con.execute(exestring)
    con.commit()
    
def decode_contextID(preds, contextID):
    "Converts an integer to the string representation of the corresponding context"
    return list(powerset(sorted(preds)))[contextID]

# TODO: geht das auch ohne preds, d.h. kann die Funktion die preds selbst ausrechnen?
def insert_local_parameter_sets(con, nwkey, nodes, preds, lpss):
    for node in sorted(nodes):
        for lps in lpss[node]:
            lpsID = encode_lps(preds[node], lps, base=10)
            exestring = '''INSERT INTO localparametersets VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, lpsID, str(lps))
            #print exestring
            con.execute(exestring)
    con.commit()

def insert_global_parameter_sets(con, nwkey, gpss):
    for gps in gpss:
        gpsID = encode_gps(gps, base=10)
        exestring = '''INSERT INTO globalparametersets VALUES("%s", "%s", "%s")''' % (nwkey, gpsID, gps)
        con.execute(exestring)
    con.commit()

def store_filter(con, nwkey, filterID, filterstring, filtertype, logictype):
    exestring = '''INSERT INTO filters VALUES("%s", "%s", "%s", "%s", "%s")''' % (nwkey, filterID, filterstring, filtertype, logictype)
    con.execute(exestring)
    con.commit()

def insert_filter_results(con, filterID=1):
    filterstring = 'filterID_'
    exestring = '''ALTER TABLE globalparametersets ADD %s INT DEFAULT -1;''' % (filterstring+str(filterID).zfill(3))
    con.execute(exestring)
    con.commit()

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

def encode_lps(preds, lps, base=10):
    ''' Returns the base-ary representation of a local parameter set as an integer.
        Number of digits is equal to number of contexts (power set of predecessors).
        Value of k-th digit equals local parameter value in k-th context'''
    code = 0
    for contextID, context in enumerate(powerset(sorted(preds))):
        code += lps[context]*pow(base, contextID)
    return code        

def decode_lps(node, preds, encoding, base=10):
    "Returns the string representation of an lps encoding - this could be converted into dict using ast.literal_eval"
    n = 2**len(preds)
    k = len(str(encoding))
    encodingstring = (n-k)*'0' + str(encoding)
    decoding = dict([(context, encodingstring[n-contextID-1]) for contextID, context in enumerate(powerset(sorted(preds)))])
    return decoding

def encode_gps(gps, base=10):
    "converts a global parameter set object into an integer representation"
    gps_encoding = ""
    nodes = gps.keys()
    for node in sorted(nodes):
        # first reverse engineer contexts, predecessors, lps
        contexts = gps[node].keys()
        n = len(contexts)
        preds = sorted(list(set().union(*contexts)))
        lps = gps[node]
        #print "lps (from encode_gps):", lps
        
        # then encode current lps
        code = encode_lps(preds, lps, base)
        
        # finally shift digits and add n-k zeros
        k = len(str(code))
        codestring = (n-k)*'0' + str(code)
        gps_encoding = codestring + gps_encoding   
    return long(gps_encoding)

def decode_gps(encoding, IG, base=10):
    decoded = dict()
    for node in sorted(IG.nodes()):
        decoded[node] = dict()
        for context in powerset(sorted(IG.predecessors(node))):
            # we iterate through the digits of encoding and shorten it by one digit in each iteration
            digit = encoding % base
            encoding = encoding / base
            decoded[node][context] = int(digit)
    return decoded


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
        nodes[nwkey] = lpss.keys()
        preds = dict([(node, IG.predecessors(node)) for node in nodes[nwkey]]) # dict containing node:[preds of node]
        
        # write nodes to database
        insert_nodes(con, nwkey, nodes[nwkey])

        # write contexts to database
        insert_contexts(con, nwkey, nodes[nwkey], preds)        

        '''
        for node in lpss:
            print "node:", node
            print "=========="
            for lps in lpss[node]:
                print "lps:", lps
                print "lpsID:", encode_lps(preds[node], lps, base=10)
                print "decoded lpsID:", decode_lps(node, preds[node], encode_lps(preds[node], lps, base=10), base=10)
                print "========================================="
        '''

        # write local parameter sets to database
        insert_local_parameter_sets(con, nwkey, nodes[nwkey], preds, lpss)
        
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            print "====================================================================="
            print gps
            #print encode_gps(gps, base=10)
            #print decode_gps(encode_gps(gps, base=10), IG, base=10)
        
        # write global parameter sets to database
        # need to re-generate since in python generators cannot be rewound
        gpss = mc._psc.get_parameterSets()
        insert_global_parameter_sets(con, nwkey, gpss)
        
        print "============"
        print "Filtering..."
    
        filterID, CTLformula, CTLsearch = 1, "(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll" # (left&middle&right), the gg=1 in left and middle is from the drawing on page 5

        store_filter(con, nwkey, filterID, CTLformula, CTLsearch, logictype="CTL")        
        insert_filter_results(con, filterID)
    
        '''
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=0))", "exists" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&AF(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EG(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
        #CTLformula, CTLsearch = "!(rr>0&bb>0&gg>0&EF(gg=0))", "forAll" #  12/202 bei thresholds = 1, obs* # Negation von Modell fuer linke Region 
        #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=1))", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer mittlere Region
        #CTLformula, CTLsearch = "EF(rr=0&bb=0&gg=1)", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer rechte Region
        
        #mc.filter_extremeAttractors('max', 'attrs', True, True)
        
        mc.filter_byCTL(CTLformula, search=CTLsearch)
        '''
    

        '''
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
