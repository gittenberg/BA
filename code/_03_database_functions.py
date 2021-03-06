import imp
import os
from os.path import join, exists
import networkx as nx
from itertools import chain, combinations
import sqlite3

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))

def create_database(path="C:\Users\MJS\git\BA\code", dbname='filter_results.db'):
    # We delete/rename the entire database. Alternatively, one could only DROP the results tables but this was difficult. # TODO:
    print "setting up database...",
    filepath = join(path, dbname)
    if exists(filepath+"~"): os.remove(filepath+"~")
    if exists(filepath): os.rename(filepath, filepath+"~")
    con = sqlite3.connect(filepath)
    print "done."
    return con

def create_tables(con, verbose=False):
    print "creating tables...",
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
    if verbose:
        con.execute("create table globalparametersets(iagraphID INT, gpsID VARCHAR(100), globalparameterset VARCHAR(500),\
            PRIMARY KEY (iagraphID, gpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")
    else:
        con.execute("create table globalparametersets(iagraphID INT, gpsID VARCHAR(100),\
            PRIMARY KEY (iagraphID, gpsID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.execute('''DROP TABLE IF EXISTS filters''')
    con.execute("create table filters(iagraphID INT, filterID INT, filterstring VARCHAR(500), filtertype VARCHAR(10), logictype VARCHAR(5),\
        PRIMARY KEY (iagraphID, filterID), FOREIGN KEY (iagraphID) REFERENCES iagraphs(iagraphID))")

    con.commit()
    print "done."
    
def insert_network(con, nwkey, networks):
    # write interaction graph to database
    print "inserting network...",
    querystring = "INSERT INTO iagraphs VALUES('%s', '%s')" % (nwkey, networks)
    #print querystring
    con.execute(querystring)
    con.commit()
    print "done."

def insert_edges(con, nwkey, edges, interactions, thresholds):
    print "inserting edges...",
    for edge in edges:
        # write edge to database
        querystring = "INSERT INTO edges VALUES('%s', '%s', '%s', '%s', '%s')" % (nwkey, edge[0], edge[1], 
            interactions[edge], thresholds[edge])
        #print querystring
        con.execute(querystring)
    con.commit()
    print "done."

def insert_nodes(con, nwkey, nodes):
    print "inserting nodes...",
    for node in nodes:
        # write node to database
        querystring = "INSERT INTO nodes VALUES('%s', '%s')" % (nwkey, node)
        #print querystring
        con.execute(querystring)
    con.commit()
    print "done."

def insert_contexts(con, nwkey, nodes, preds):
    print "inserting contexts...",
    for node in sorted(nodes):
        for contextID, context in enumerate(powerset(sorted(preds[node]))): 
            querystring = '''INSERT INTO contexts VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, contextID, context)
            #print querystring
            con.execute(querystring)
    con.commit()
    print "done."
    
def decode_contextID(preds, contextID):
    "Converts an integer to the string representation of the corresponding context"
    return list(powerset(sorted(preds)))[contextID]

def insert_local_parameter_sets(con, nwkey, nodes, preds, lpss):
    # TODO: geht das auch ohne preds, d.h. kann die Funktion die preds selbst ausrechnen?
    print "inserting local parameter sets...",
    for node in sorted(nodes):
        for lps in lpss[node]:
            lpsID = encode_lps(preds[node], lps, base=10)
            querystring = '''INSERT INTO localparametersets VALUES("%s", "%s", "%s", "%s")''' % (nwkey, node, lpsID, str(lps))
            #print querystring
            con.execute(querystring)
    con.commit()
    print "done."

def insert_global_parameter_sets(con, nwkey, gpss, verbose=False):
    print "inserting global parameter sets...",
    for gps in gpss:
        gpsID = encode_gps(gps, base=10)
        if verbose:
            querystring = '''INSERT INTO globalparametersets VALUES("%s", "%s", "%s")''' % (nwkey, gpsID, gps)
            #print querystring
        else:
            querystring = '''INSERT INTO globalparametersets VALUES("%s", "%s")''' % (nwkey, gpsID)
        con.execute(querystring)
    con.commit()
    print "done."

def store_filter(con, nwkey, filterID, filterstring, filtertype, logictype):
    print "inserting filter...",
    querystring = '''INSERT INTO filters VALUES("%s", "%s", "%s", "%s", "%s")''' % (nwkey, filterID, filterstring, filtertype, logictype)
    con.execute(querystring)
    con.commit()
    print "done."

def insert_filter_results(con, nwkey, gpss, filterID=1):
    print "inserting filter results...",
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
        #print "---------------------------updating with 1---------------------------"
        querystring3 = '''UPDATE %s SET %s = 1 WHERE gpsID = "%s";''' % (tablename, columnname, code)
        con.execute(querystring3)
    con.commit()
    print "done."

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

def decode_lps(preds, encoding, base=10):
    "Returns the string representation of an lps encoding - this could be converted into dict using ast.literal_eval"
    n = 2**len(preds)
    k = len(str(encoding))
    encodingstring = (n-k)*'0' + str(encoding)
    decoding = dict([(context, encodingstring[n-contextID-1]) for contextID, context in enumerate(powerset(sorted(preds)))])
    return decoding

def encode_gps(gps, base=10):
    "converts a global parameter set object into a string representation"
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

def encode_gps_full(gps, base=10):
    "converts a global parameter set object into a string representation"
    gps_encoding = ""
    totallength = 0
    nodes = gps.keys()
    edges = []
    for node in sorted(nodes):
        # first reverse engineer contexts, predecessors, lps
        contexts = gps[node].keys()
        n = len(contexts)
        preds = sorted(list(set().union(*contexts)))
        edges += [(pred, node) for pred in preds]
        #print node
        lps = gps[node]
        #print "lps (from encode_gps):", lps
        
        # then encode current lps
        code = encode_lps(preds, lps, base)
        
        # finally shift digits and add n-k zeros
        k = len(str(code))
        codestring = (n-k)*'0' + str(code)
        gps_encoding = codestring + gps_encoding
        totallength += n
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
    IGstring = "_".join(nx.generate_edgelist(IG, data=False))
    finalencoding = gps_encoding.zfill(totallength)+"."+IGstring
    return finalencoding

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

def decode_gps_full(code):
    '''Decodes GPS encodings of the form codestring.edgestring
    where codestring is in encode_gps and edgestring is 'e1 e2_e3 e4_...'''
    first, second = code.split(".")
    edgestrings = second.split("_")
    edges = [tuple(edgestring.split(" ")) for edgestring in edgestrings]
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
    return decode_gps(int(first), IG), IG

def export_STG(mc, gps, filename, initialRules=None):
    if initialRules:
        mc.set_initialRules(initialRules)
    mc.set_initialStates()
    transsys = TS.TransitionSystem(mc, gps)
    graph = transsys.stg()
    if graph:
        nx.write_gml(graph, filename)


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

    # create database
    con = create_database(path, dbname='filter_results.db')
    
    # create tables
    create_tables(con)
    
    filters_for_3_gene_networks = {
                            0:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                            1:["((rr=2&bb=0&gg=1)->EF(AG(gg=0)))&((rr=1&bb=0&gg=1)->EF(AG(gg=1)))&((rr=0&bb=0&gg=0)->EF(AG(gg=0)))", "forAll", "CTL"],
                            # tight BCs, forAll, EFAG, with rr decay
                            3:["((rr=2&bb=0&gg=1)->AF(AG(gg=0)))&((rr=1&bb=0&gg=1)->AF(AG(gg=1)))&((rr=0&bb=0&gg=0)->AF(AG(gg=0)))", "forAll", "CTL"],
                            # tight BCs, forAll, AFAG, with rr decay
                            5:["((rr=2&bb=0&gg=1)->EF(AG(gg=0)))&((rr=1&bb=0&gg=1)->EF(AG(gg=1)))&((rr=0&bb=0&gg=0)->EF(AG(gg=0)))", "exists", "CTL"],
                            # tight BCs, exists, EFAG, with rr decay
                            7:["((rr=2&bb=0&gg=1)->AF(AG(gg=0)))&((rr=1&bb=0&gg=1)->AF(AG(gg=1)))&((rr=0&bb=0&gg=0)->AF(AG(gg=0)))", "exists", "CTL"],
                            # tight BCs, exists, AFAG, with rr decay
                            9:["((rr=2)->EF(AG(gg=0)))&((rr=1)->EF(AG(gg=1)))&((rr=0)->EF(AG(gg=0)))", "forAll", "CTL"],
                            # loose BCs, forAll, EFAG, with rr decay
                            11:["((rr=2)->AF(AG(gg=0)))&((rr=1)->AF(AG(gg=1)))&((rr=0)->AF(AG(gg=0)))", "forAll", "CTL"],
                            # loose BCs, forAll, AFAG, with rr decay
                            13:["((rr=2)->EF(AG(gg=0)))&((rr=1)->EF(AG(gg=1)))&((rr=0)->EF(AG(gg=0)))", "exists", "CTL"],
                            # loose BCs, exists, EFAG, with rr decay
                            15:["((rr=2)->AF(AG(gg=0)))&((rr=1)->AF(AG(gg=1)))&((rr=0)->AF(AG(gg=0)))", "exists", "CTL"]
                            # loose BCs, exists, AFAG, with rr decay
                          }

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
    filters[1] = filters_for_3_gene_networks

    # example network: graph A in figure 2 of Cotterel/Sharpe
    # strict edge labels, without morphogene, green activated earlier than blue
    networks[2] = '(A) Incoherent type 1 feed-forward, with self-loop on rr @ threshold = 2'
    interactions[2] = {("rr","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[2] = {("rr","rr"):1, ("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
    filters[2] = filters_for_3_gene_networks

    # example network: graph A in figure 2 of Cotterel/Sharpe
    # strict edge labels, without morphogene, green activated earlier than blue
    networks[3] = '(A) Incoherent type 1 feed-forward, with self-loop on rr @ threshold = 2'
    interactions[3] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[3] = {("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
    filters[3] = filters_for_3_gene_networks

    '''
    # strict edge labels, with 1 morphogene, green activated earlier than blue
    networks[3] = '(A) Incoherent type 1 feed-forward, strict edge labels, different thresholds, with morphogene'
    interactions[3] = {("mm","mm"):"+", ("mm","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[3] = {("mm","mm"):1, ("mm","rr"):0, ("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
    filters[3] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                  2:["(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (anterior&medial&posterior), the gg=1 in anterior and medial is from the drawing on page 5
                  }

    # strict edge labels, with 2 morphogenes, green activated earlier than blue
    networks[4] = '(A) Incoherent type 1 feed-forward, strict edge labels, different thresholds, with 2 morphogenes'
    interactions[4] = {("aa1","aa1"):"+", ("aa2","aa2"):"+", ("aa1","rr"):"+", ("aa2","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[4] = {("aa1","aa1"):1, ("aa2","aa2"):1, ("aa1","rr"):1, ("aa2","rr"):2, ("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
    filters[4] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                  2:["(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (anterior&medial&posterior), the gg=1 in anterior and medial is from the drawing on page 5
                  }

    # strict edge labels, without morphogene, green activated earlier than blue, no rr-rr activation
    networks[5] = '(A) Incoherent type 1 feed-forward, strict edge labels, different thresholds, no rr-rr activation'
    interactions[5] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds[5] = {("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}
    valueConstraints[5] = {'rr':{():[0, 1, 2]}} # TODO: this should admit more than one set of valueConstraints
    filters[5] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # used to be ...&mitte.max(gg)=1 with the same number of results
                  2:["(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (anterior&medial&posterior), the gg=1 in anterior and medial is from the drawing on page 5
                  }
    '''

    # example network: graph B in figure 2 of Cotterel/Sharpe
    # strict edge labels, without morphogene, green activated earlier than blue, no rr-rr activation
    networks[6] = '(B) Mutual inhibition, strict edge labels, no rr-rr activation'
    interactions[6] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","bb"):"-"}
    thresholds[6] = {("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","bb"):1}
    valueConstraints[6] = {'rr':{():[0, 1, 2]}} # TODO: this should admit more than one set of valueConstraints
    filters[6] = {1:["?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.min(gg)=1)", None, "AL"], # TODO: check (new network!!)
                  2:["(rr=2&bb=1&gg=1->EF(AG(gg=0)))&(rr=1&bb=1&gg=1->EF(AG(gg=1)))&(rr=0&bb=1&gg=0->EF(AG(gg=0)))", "forAll", "CTL"]
                  #   (anterior&medial&posterior), the gg=1 in anterior and medial is from the drawing on page 5
                  }
    dynamics[6] = "asynchronous"
    
    '''
    #mc.filter_extremeAttractors('max', 'attrs', True, True)

    networks[7] = 'Lecture example p. 25'
    interactions[7] = {("X1","X2"):"+", ("X2","X1"):"-", ("X2","X2"):"+"}
    thresholds[7] = {("X1","X2"):1, ("X2","X1"):1, ("X2","X2"):2}
    filters[7] = {1:["#F=2", None, "AL"], 
                  2:["#F=1&#C=1", None, "AL"]}

    networks[8] = 'Two-element negative circuit'
    interactions[8] = {("X1","X2"):"+", ("X2","X1"):"-"}
    thresholds[8] = {("X1","X2"):1, ("X2","X1"):1}
    filters[8] = {1:["TRUE", "forAll", "CTL"]}

    networks[9] = 'Two-element positive circuit'
    interactions[9] = {("X1","X2"):"-", ("X2","X1"):"-"}
    thresholds[9] = {("X1","X2"):1, ("X2","X1"):1}
    filters[9] = {1:["(X1=0&X2=1)->EF(AG(X1=0))", "forAll", "CTL"]}
    '''
    
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
        mc._NuSMVpath = nusmvpath
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
        mc.initializePSC()
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
