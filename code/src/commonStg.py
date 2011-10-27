# -*- coding: utf-8 -*-
import networkx as nx
import random as RND
import time

def compute_commonStg1(tsgen, parent=None):
    '''Zählt für die STGs in tslist die Häufigkeit jeder auftretenden Kante.''' 
    commonStg = nx.DiGraph()        ## Gemeinsamer Graph
    graphdict = dict()              ## Dictionary für die Knotenattribute "graphics"
    edgedict = dict()               ## Dictionary mit allen Kanten und Häufigkeit

    # Falls von ModelContainer aufgerufen..
    if parent:
        parent.startProgressBar()
        start = time.time()
        for counter, ts in enumerate(tsgen):
            stg = ts.stg()
            parent.stepProgressBar(counter)
            for edge in stg.edges():
                if edgedict.has_key(edge):
                    edgedict[edge]+=1
                else:
                    edgedict[edge]=1
        end = time.time()
        parent.message("CommonSTG1: Finished in %s."%parent.hmsTime(end-start), "result")

    # ..falls nicht.
    else:
        start = time.time()
        for counter, ts in enumerate(tsgen):
            stg = ts.stg()
            for edge in stg.edges():
                if edgedict.has_key(edge):
                    edgedict[edge]+=1
                else:
                    edgedict[edge]=1
        end = time.time()
        print "CommonSTG1: Finished in",end-start,"s."

    edges = edgedict.keys()
    commonStg.add_edges_from(edges)  ## Füge alle Kanten in Graphen

    ## Graphische Anordnung
    ## - vorerst zufällig, damit beim Testen überhaupt was zu sehen ist.
    for node in commonStg.nodes():
        x = RND.randint(0,500)
        y = RND.randint(0,500)
        graphdict[node]= {"x": x,
                          "y": y}
    
    #print countdict
    nx.set_edge_attributes(commonStg, "count", edgedict) ## Attribute anfuegen
    nx.set_node_attributes(commonStg, "graphics", graphdict)
    return commonStg

def compute_commonStg2(tsgen, parent=None):
    ## mit SCCs und completegraph
    ## + attraktorcount
    commonStg = nx.Graph()
    edgedict = dict() ## counts
    graphdict = dict()      ## Dictionary für die Knotenattribute "graphics"


    # Falls von ModelContainer aufgerufen..
    if parent:
        parent.startProgressBar()
        start = time.time()
        for counter, ts in enumerate(tsgen):                ## In jedem TS
            parent.stepProgressBar(counter)
            sccs = ts.sccs()                                ## jede SCC bestimmen
            for c in sccs:
                if len(c) > 1:
                    sorC = sorted(c)                        ## und falls nicht trivial
                    for n1 in sorC:                         ## Kante adden!
                        for n2 in sorC[n1:]:
                            edge=tuple(sorted(n1,n2))
                            if not(edgedict.has_key(edge)):
                                edgedict[edge]=1
                            else:
                                edgedict[edge]+=1
        edges = edgedict.keys()
        commonStg.add_edges_from(edges)
        end = time.time()
        parent.message("CommonSTG1: Finished in %s."%parent.hmsTime(end-start), "result")
    # ..falls nicht.
    else:
        start = time.time()
        for counter, ts in enumerate(tsgen):                ## In jedem TS
            sccs = ts.sccs()                                ## jede SCC bestimmen
            for c in sccs:
                if len(c) > 1:
                    sorC = sorted(c)                        ## und falls nicht trivial
                    for i, n1 in enumerate(sorC):           ## Kante adden!
                        for n2 in sorC[i:]:
                            edge=tuple(sorted([n1,n2]))
                            if not(edgedict.has_key(edge)):
                                edgedict[edge]=1
                            else:
                                edgedict[edge]+=1
        end = time.time()
        edges = edgedict.keys()
        commonStg.add_edges_from(edges)
        print "CommonSTG2: Finished in",end-start,"s."
                                                
    for node in commonStg.nodes():
        x = RND.randint(0,500)
        y = RND.randint(0,500)
        graphdict[node]= {"x": x,
                          "y": y}
    nx.set_node_attributes(commonStg, "graphics", graphdict)
    nx.set_edge_attributes(commonStg, "count", edgedict)
    return commonStg

if __name__=="__main__":
    print "Testskript -> nach Testsskripte/test_commonStg.py verschoben."
