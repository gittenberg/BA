import imp
import os
from os.path import join, exists
import networkx as nx #@UnresolvedImport
from itertools import chain, combinations
import sqlite3

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))

def create_database(path="C:\Users\MJS\gitprojects_2\BA\code\src", dbname='filter_results.db'):
    # We delete/rename the entire database. Alternatively, one could only DROP the results tables but this was difficult. # TODO:
    filepath = join(path, dbname)
    if exists(filepath+"~"): os.remove(filepath+"~")
    if exists(filepath): os.rename(filepath, filepath+"~")
    con = sqlite3.connect(filepath)
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
    con.execute("create table localparametersets(iagraphID INT, node VARCHAR(5), lpsID VARCHAR(50), localparameterset VARCHAR(500),\
        PRIMARY KEY (iagraphID, node, lpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID), FOREIGN KEY (iagraphID, node) REFERENCES nodes(iagraphID, node))")

    con.execute('''DROP TABLE IF EXISTS globalparametersets''')
    con.execute("create table globalparametersets(iagraphID INT, gpsID VARCHAR(100), globalparameterset VARCHAR(500),\
        PRIMARY KEY (iagraphID, gpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.execute('''DROP TABLE IF EXISTS filters''')
    con.execute("create table filters(iagraphID INT, filterID INT, filterstring VARCHAR(500), filtertype VARCHAR(10), logictype VARCHAR(5),\
        PRIMARY KEY (iagraphID, filterID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.commit()
    
def insert_network(con, nwkey, networks):
    # write interaction graph to database
    querystring = "INSERT INTO iagraphs VALUES('%s', '%s')" % (nwkey, networks)
    #print querystring
    con.execute(querystring)
    con.commit()

def insert_edges(con, nwkey, edges, interactions, thresholds):
    for edge in edges:
        # write edge to database
        querystring = "INSERT INTO edges VALUES('%s', '%s', '%s', '%s', '%s')" % (nwkey, edge[0], edge[1], 
            interactions[edge], thresholds[edge])
        #print querystring
        con.execute(querystring)
    con.commit()

def insert_nodes(con, nwkey, nodes):
    for node in nodes:
        # write node to database
        querystring = "INSERT INTO nodes VALUES('%s', '%s')" % (nwkey, node)
        #print querystring
        con.execute(querystring)
    con.commit()

def insert_contexts(con, nwkey, nodes, preds):
    for node in sorted(nodes):
        for contextID, context in enumerate(powerset(sorted(preds[node]))): 
            querystring = '''INSERT INTO contexts VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, contextID, context)
            #print querystring
            con.execute(querystring)
    con.commit()
    
def decode_contextID(preds, contextID):
    "Converts an integer to the string representation of the corresponding context"
    return list(powerset(sorted(preds)))[contextID]

def insert_local_parameter_sets(con, nwkey, nodes, preds, lpss):
    # TODO: geht das auch ohne preds, d.h. kann die Funktion die preds selbst ausrechnen?
    for node in sorted(nodes):
        for lps in lpss[node]:
            lpsID = encode_lps(preds[node], lps, base=10)
            querystring = '''INSERT INTO localparametersets VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, lpsID, str(lps))
            #print querystring
            con.execute(querystring)
    con.commit()

def insert_global_parameter_sets(con, nwkey, gpss):
    for gps in gpss:
        gpsID = encode_gps(gps, base=10)
        querystring = '''INSERT INTO globalparametersets VALUES("%s", "%s", "%s")''' % (nwkey, gpsID, gps)
        con.execute(querystring)
    con.commit()

def store_filter(con, nwkey, filterID, filterstring, filtertype, logictype):
    querystring = '''INSERT INTO filters VALUES("%s", "%s", "%s", "%s", "%s")''' % (nwkey, filterID, filterstring, filtertype, logictype)
    con.execute(querystring)
    con.commit()

def insert_filter_results(con, nwkey, gpss, filterID=1):
    tablename = "results_iagraphID_"+str(nwkey).zfill(3)

    # if it does not exist aleady, create table
    querystring1 = "CREATE TABLE IF NOT EXISTS %s AS SELECT * FROM globalparametersets WHERE iagraphID=%s;" % (tablename, nwkey)
    con.execute(querystring1)
    
    # insert filter results
    columnname = 'filterID_'+str(filterID).zfill(3)
    #con.execute('''ALTER TABLE %s DROP COLUMN %s''' % (tablename, columnname)) # not allowed in sqlite: http://www.sqlite.org/faq.html#q11
    querystring2 = '''ALTER TABLE %s ADD %s INT DEFAULT 0;''' % (tablename, columnname)
    con.execute(querystring2)
    for gps in gpss:
        code = encode_gps(gps, base=10)
        querystring3 = '''UPDATE %s SET %s = 1 WHERE gpsID = "%s";''' % (tablename, columnname, code)
        con.execute(querystring3)
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
    return str(code).zfill(contextID+1) # we use the last contextID to generate enough leading zeros

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
    totallength = 0
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
        totallength += n
    #return long(gps_encoding)
    return gps_encoding.zfill(totallength)

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

def export_STG(mc, gps, filename, initialRules=None):
    if initialRules:
        mc.set_initialRules(initialRules)
    mc.set_initialStates()
    transsys = TS.TransitionSystem(mc, gps)
    graph = transsys.stg()
    if graph:
        nx.write_gml(graph, filename)


if __name__=='__main__':
    # create database
    con = create_database()
    
    # create tables
    create_tables(con)
    
    # setup objects
    networks = dict()
    interactions = dict()
    thresholds = dict()
    filters = dict()
    
    # example network: graph A in figure 2 of Cotterel/Sharpe
    # strict edge labels, without morphogene
    networks[1] = 'Incoherent type 1 feed-forward, strict edge labels'
    interactions[1] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[1] = {("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}
    filters[1] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                  2:["(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (left&middle&right), the gg=1 in left and middle is from the drawing on page 5
                  }

    # non-strict edge labels, without morphogene
    networks[2] = 'Incoherent type 1 feed-forward, non-strict edge labels'
    interactions[2] = {("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    thresholds[2] = {("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}
    filters[2] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                  2:["(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (left&middle&right), the gg=1 in left and middle is from the drawing on page 5
                  }
    
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=0))", "exists" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&AF(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EG(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "!(rr>0&bb>0&gg>0&EF(gg=0))", "forAll" #  12/202 bei thresholds = 1, obs* # Negation von Modell fuer linke Region 
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=1))", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer mittlere Region
    #CTLformula, CTLsearch = "EF(rr=0&bb=0&gg=1)", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer rechte Region
    
    #mc.filter_extremeAttractors('max', 'attrs', True, True)

    networks[3] = 'Two-element positive circuit'
    interactions[3] = {("X1","X2"):"-", ("X2","X1"):"-"}
    thresholds[3] = {("X1","X2"):1, ("X2","X1"):1}
    filters[3] = {1:["(X1=0&X2=1)->EF(AG(X1=0))", "forAll", "CTL"]}

    networks[4] = 'Lecture example p. 25'
    interactions[4] = {("X1","X2"):"+", ("X2","X1"):"-", ("X2","X2"):"+"}
    thresholds[4] = {("X1","X2"):1, ("X2","X1"):1, ("X2","X2"):2}
    filters[4] = {1:["#F=2", None, "AL"], 
                  2:["#F=1&#C=1", None, "AL"]}

    networks[5] = 'Two-element negative circuit'
    interactions[5] = {("X1","X2"):"+", ("X2","X1"):"-"}
    thresholds[5] = {("X1","X2"):1, ("X2","X1"):1}
    filters[5] = {1:["TRUE", "forAll", "CTL"]}

    edges = dict(zip(interactions.keys(), [interactions[key].keys() for key in interactions.keys()]))
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
        mc._NuSMVpath = r"C:\Progra~2\NuSMV\2.5.2\bin\NuSMV.exe"

        mc.set_IG(IG)
        if interactions.has_key(nwkey):
            mc.set_edgeLabels(interactions[nwkey])

        if thresholds.has_key(nwkey):
            mc.set_thresholds(dict((edge, thresholds[nwkey][edge]) for edge in edges[nwkey]))

        mc.set_initialStates()
        mc.initializePSC()
        # TODO: replacing the previous by MC.parameterSetup() would allow more flexibility like local constraints etc.
            
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
        
        print "===================================================================================="
        print "Database operations"

        # write network to database
        insert_network(con, nwkey, networks[nwkey])

        # write interaction graph to database
        insert_edges(con, nwkey, edges[nwkey], interactions[nwkey], thresholds[nwkey])

        # write nodes to database
        insert_nodes(con, nwkey, nodes[nwkey])

        # write contexts to database
        insert_contexts(con, nwkey, nodes[nwkey], preds)        

        # write local parameter sets to database
        insert_local_parameter_sets(con, nwkey, nodes[nwkey], preds, lpss)
        
        # write global parameter sets to database
        gpss = mc._psc.get_parameterSets()
        insert_global_parameter_sets(con, nwkey, gpss)
        
        print "===================================================================================="
        print "Filtering on resetted parameter set container..."
        if filters.has_key(nwkey):
            for filterID in filters[nwkey]:
                mc.initializePSC()
        
                formula, searchtype, logictype = filters[nwkey][filterID]
        
                if logictype=="AL":
                    mc.filter_byAL(formula)
                elif logictype=="CTL":
                    mc.filter_byCTL(formula, search=searchtype)
                    
                # write filter details to database
                store_filter(con, nwkey, filterID, formula, searchtype, logictype)        
                
                # write filter results to database
                gpss = mc._psc.get_parameterSets()
                insert_filter_results(con, nwkey, gpss, filterID)

        print "===================================================================================="
        print "Exporting .gml..."
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            print gps
            #print encode_gps(gps, base=10)
            #print decode_gps(encode_gps(gps, base=10), IG, base=10)
            #print TS.TransitionSystem(mc, gps)
            export_STG(mc, gps, filename=str(nwkey).zfill(3)+"_"+encode_gps(gps, base=10)+".gml", initialRules=None)
    
        #mc.export_commonSTG(Type="transitions", filename="A_commonSTG_transitions_strict.gml", initialRules=None)

    con.commit()
    con.close()
    print "Done."
