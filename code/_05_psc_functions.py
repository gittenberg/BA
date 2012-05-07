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

def strictest_label((predecessor, node), gpslist):
    '''returns the strictest label for the edge (predecessor, node) which is compatible with the gpslist'''
    constant = True
    plus = True
    minus = True
    plusminus = True
    monplus = True
    monminus = True
    obs = True
    plusobs = True
    minusobs = True
    notplus = True
    notminus = True
        
    for gps in gpslist:
        alwaysIncreasing = True
        alwaysDecreasing = True
        everStrictlyIncreasing = False
        everStrictlyDecreasing = False
        lps = gps[node] # a local parameter set is just a global parameter viewed from a node
        for context in lps:
            contextList = list(context)
            contextList.append(predecessor)
            extendedContext = tuple(sorted(set(contextList))) # set to uniquefy, sorted to make comparable, tuple so we have the right type
            if lps[context] == lps[extendedContext]: 
                continue
            elif lps[context] < lps[extendedContext]:
                everStrictlyIncreasing = True
                alwaysDecreasing = False
            elif lps[context] > lps[extendedContext]:
                everStrictlyDecreasing = True
                alwaysIncreasing = False
        constant = constant and (not everStrictlyIncreasing and not everStrictlyDecreasing)
        plus = plus and (alwaysIncreasing and everStrictlyIncreasing)
        minus = minus and (alwaysDecreasing and everStrictlyDecreasing)
        plusminus = plusminus and (everStrictlyIncreasing and everStrictlyDecreasing)
        monplus = monplus and not (everStrictlyDecreasing)
        monminus = monminus and not (everStrictlyIncreasing)
        plusobs = plusobs and (everStrictlyIncreasing)
        minusobs = minusobs and (everStrictlyDecreasing)
        obs = obs and (everStrictlyIncreasing or everStrictlyDecreasing)
        notplus = notplus and (not (alwaysIncreasing and everStrictlyIncreasing))
        notminus = notminus and (not (alwaysDecreasing and everStrictlyDecreasing))
    if constant:
        strictestLabel = '=' # this means it is constant
    elif plus:
        strictestLabel = '+'
    elif minus:
        strictestLabel = '-'
    elif plusminus:
        strictestLabel = '+-'
    elif monplus:
        strictestLabel = 'mon+'
    elif monminus:
        strictestLabel = 'mon-'
    elif plusobs:
        strictestLabel = 'obs+'
    elif minusobs:
        strictestLabel = 'obs-'
    elif obs:
        strictestLabel = 'obs'
    elif notplus:
        strictestLabel = 'not+'
    elif notminus:
        strictestLabel = 'not-'
    else:
        strictestLabel = 'free' #self.edgeLabel((predecessor, varname))
    return strictestLabel

def strictest_labels(edges, gpslist):
    ''' To be used after model checking: returns a {edge:edgeLabels} with strictest edgeLabels consistent with _parameterSets '''
    strictestEdgeLabels = {}
    for edge in edges:
        strictestEdgeLabels[edge] = strictest_label(edge, gpslist)
    return strictestEdgeLabels

if __name__=='__main__':
    mode = "without_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."
    pstotal = 0
    graphcount = 0
    
    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    for nwkey in networks:
        #if nwkey >= 100: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        #print networks[nwkey]

        ##############################################################################
        # <HACK>
        ##############################################################################
        #the following block is a hack to remove graphs with indegree(rr) > 3:
        net = networks[nwkey]        
        morphogene_interactions = {("m1","m1"):"+", ("m1","rr"):"+", ("m2","m2"):"+", ("m2","rr"):"+"}
        labels = dict((edge, label) for (edge, label) in net.items() if label!='0') # TODO: obsolete iff addzeros==False in graph_enumerator
        # then set up the morphogene edges:
        if add_morphogene:
            for edge in morphogene_interactions:
                labels[edge] = morphogene_interactions[edge]
        edges = labels.keys()
        IG = nx.DiGraph()
        IG.add_edges_from(edges)
        if IG.in_degree('rr') > 3:
            continue
        graphcount +=1
        print "this is graph no.", graphcount
        ##############################################################################
        # </HACK>
        ##############################################################################

        mc = dict_to_model(networks[nwkey], add_morphogene)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."

        tend = datetime.now()
        print "total execution time:", tend-tstart
    
    print "done."
    