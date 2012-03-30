from datetime import datetime

tstart = datetime.now()

import itertools
import networkx as nx
import cPickle
#import shelve

nodes = ["bb", "gg", "rr"]
labels = ["-", "0", "+"]


def generate_all_networks():
    ''' generate all 3^9 = 19683 combinations of networks '''
    print "generating all networks...",
    edges = [(node1, node2) for node1 in nodes for node2 in nodes]
    labelcombinations = itertools.product(labels, repeat=len(edges)) # all combinations of len(edges) labels
    networks = dict(enumerate(dict(zip(edges, labelcombination)) for labelcombination in labelcombinations))
    cPickle.dump(networks, file("all_networks.db", "w" ))
    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained

    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."


def convert_dict_to_graphs(networks, addzeros=True):
    ''' given a dictionary, create digraph with labels
    assumption: networks is dict(netID:dict(edge:label)) '''
    print "converting dictionaries to graphs...",
    G = dict() # dictionary of digraphs
    for netID in networks:
        G[netID] = nx.DiGraph()
        net = networks[netID]
        for edge in net:
            if net[edge]!='0' or addzeros:
                G[netID].add_edge(edge[0], edge[1], label=net[edge])
                #print edge[0], edge[1], G[netID][edge[0]][edge[1]]
    print "done."
    return G
    

def label_match(label1, label2):
    return label1==label2
    
    
def check_isomorphism(networks, outfile_tag="_without_morphogene", tag_input_gene=False):
    ''' check for isomorphism:
    loop through all pairs of networks and check for isomorphy
    (takes about 6 hrs on the full set)'''
    print "checking networks for isomorphism..."
    G = convert_dict_to_graphs(networks, addzeros=False)
    if tag_input_gene:
        # treat label 'rr' gene differently than others (input gene)
        print "labelling input genes in graphs...",
        for graph in G.values():
            graph.node['rr'] = 'input'
        match_fct = label_match
        print 'done.'
    else:
        match_fct = None
    
    skiplist = []
    isomorphy_classes = {}
    maxiter = len(networks)
    for netID1 in networks.keys():
        if netID1 not in skiplist:
            isomorphy_classes[netID1] = [netID1]
            for netID2 in range(netID1+1, maxiter):
                if netID2 not in skiplist:
                    if nx.is_isomorphic(G[netID1], G[netID2], node_match=match_fct, edge_match=label_match):
                        try:
                            #del networks[netID2]
                            skiplist.append(netID2)
                            isomorphy_classes[netID1].append(netID2)
                        except:
                            pass
            skiplist = list(set(skiplist)) # remove double entries
            print "isomorphy_classes[", netID1, "] =", isomorphy_classes[netID1]
        tend = datetime.now()
        print "total execution time:", tend-tstart

    unique_networks = dict()
    for netID in networks.keys():
        if isomorphy_classes.has_key(netID):
            unique_networks[netID] = networks[netID]
    print "pickling", len(unique_networks), "unique networks."
    cPickle.dump(unique_networks, file("unique_networks"+outfile_tag+".db", "w"))
    print "pickling", len(isomorphy_classes), "isomorphy classes."
    cPickle.dump(isomorphy_classes, file("isomorphy_classes"+outfile_tag+".db", "w"))
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done checking networks for isomorphism."


def convert_graph_to_dict(G, addzeros=False):
    ''' given a graph, create dictionary with edge:label '''
    es = G.edges()
    ls = [G[edge[0]][edge[1]]['label'] for edge in G.edges()]
    if addzeros:
        alledges = [(node1, node2) for node1 in nodes for node2 in nodes]
        for edge in alledges:
            if edge not in es:
                es.append(edge)
                ls.append('0')
    return dict(zip(es, ls))


def filter_disconnected(unique_networks, outfile_tag="_with_morphogene"):
    ''' remove networks with > 1 connected component '''
    ''' remove networks that do not contain node rr '''
    print "filtering disconnected networks..."
    G = convert_dict_to_graphs(unique_networks, addzeros=False)
    for netID in G:
        if not G[netID] or not nx.is_connected(G[netID].to_undirected()):
            try:
                del unique_networks[netID]
            except:
                pass
        if not 'rr' in G[netID].nodes():
            try:
                print netID, "does not contain the input node: removing."
                del unique_networks[netID]
            except:
                pass
    
    print "pickling", len(unique_networks), "connected unique networks."
    cPickle.dump(unique_networks, file("connected_unique_networks"+outfile_tag+".db", "w"))
    print "done."


if __name__ == '__main__':
    generate_all_networks()
    networks = cPickle.load(file("all_networks.db"))
    #networks = dict((k, networks[k]) for k in range(500)) # enable for quick check
    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained
    #print networks[1]
    #check_isomorphism(networks, outfile_tag="_without_morphogene", tag_input_gene=False) # takes 6 hrs
    check_isomorphism(networks, outfile_tag="_with_morphogene", tag_input_gene=True) # takes 15 hrs
    #unique_networks = cPickle.load(file("unique_networks_without_morphogene.db"))
    unique_networks = cPickle.load(file("unique_networks_with_morphogene.db"))
    print "found", len(unique_networks), "unique networks." 
    filter_disconnected(unique_networks, outfile_tag="_with_morphogene")
    connected_unique_networks = cPickle.load(file("connected_unique_networks_with_morphogene.db"))
