from datetime import datetime
tstart = datetime.now()

import itertools
import networkx as nx
import cPickle
from os import rename, remove
from os.path import exists

nodes = ["bb", "gg", "rr"]
labels = ["-", "0", "+"]


def backup(filename):
    print "backing up", filename, "...",
    if exists(filename+".bak"): remove(filename+".bak")
    if exists(filename): rename(filename, filename+".bak")
    print "done."
    

def generate_all_networks():
    ''' generate all 3^9 = 19683 combinations of networks '''
    print "generating all networks...",
    edges = [(node1, node2) for node1 in nodes for node2 in nodes]
    labelcombinations = itertools.product(labels, repeat=len(edges)) # all combinations of len(edges) labels
    networks = dict(enumerate(dict(zip(edges, labelcombination)) for labelcombination in labelcombinations))

    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained
    picklename = "all_networks.db"
    backup(picklename)
    print "pickling", len(networks), "networks to", picklename, "."
    cPickle.dump(networks, file(picklename, "w" ))

    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."


def convert_dict_to_graphs(networks, addzeros=False):
    ''' given a dictionary, create digraph with labels
    assumption: networks is dict(netID:dict(edge:label)) '''
    print "converting dictionaries to graphs...",
    G = dict() # dictionary of digraphs
    for netID in networks:
        G[netID] = nx.DiGraph()
        net = networks[netID]
        for edge in net:
            if addzeros or net[edge]!='0':
                G[netID].add_edge(edge[0], edge[1], label=net[edge])
                #print edge[0], edge[1], G[netID][edge[0]][edge[1]]
    print "done."
    return G
    

def label_match(label1, label2):
    return label1==label2
    
    
def check_isomorphism(networks, mode, tag_input_gene): # mode is just for filenames here... TODO: remove eventually
    ''' check for isomorphism: loop through all pairs of networks and check for isomorphy '''
    ''' new, faster version'''
    print "checking networks for isomorphism..."
    G = convert_dict_to_graphs(networks, addzeros=False)
    if tag_input_gene:
        # treat gene with label tag_input_gene gene differently than others (input gene)
        print "labelling input genes in graphs...",
        for graph in G.values():
            graph.node[tag_input_gene] = 'input'
        match_fct = label_match
        print 'done.'
    else:
        match_fct = None
    
    isomorphy_classes = {}
    for netID in networks.keys():
        for isomorphy_class in isomorphy_classes.values():
            if nx.is_isomorphic(G[netID], G[isomorphy_class[0]], node_match=match_fct, edge_match=label_match): # we found an isomorphism
                isomorphy_classes[isomorphy_class[0]].append(netID) # compare with first member of isomorphy class
                break # quit looping over isomorphy classes, continue with networks
        else: # if break was not hit, we found no isomorphy class
            isomorphy_classes[netID] = [netID] # create new isomorphy class
            print "creating new isomorphy class for netID:", netID, "."
    tend = datetime.now()
    print "total execution time:", tend-tstart

    unique_networks = dict()
    for netID in networks.keys():
        if isomorphy_classes.has_key(netID):
            unique_networks[netID] = networks[netID]

    picklename1 = "unique_networks_" + mode + ".db"
    picklename2 = "isomorphy_classes_" + mode + ".db"
    backup(picklename1)
    backup(picklename2)
    print "pickling", len(unique_networks), "unique networks to", picklename1, "."
    print "pickling", len(isomorphy_classes), "isomorphy classes to", picklename2, "."
    cPickle.dump(unique_networks, file(picklename1, "w"))
    cPickle.dump(isomorphy_classes, file(picklename2, "w"))
    
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


def filter_disconnected(unique_networks, mode):
    ''' remove networks with fewer than 3 nodes and unconnected'''
    print "filtering disconnected networks..."
    G = convert_dict_to_graphs(unique_networks, addzeros=False)
    for netID in G:
        if len(G[netID].nodes())==0 or not nx.is_connected(G[netID].to_undirected()):
            print netID, "not connected: removing."
            del unique_networks[netID]

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    backup(picklename)
    print "pickling", len(unique_networks), "connected unique networks to", picklename, "."
    cPickle.dump(unique_networks, file(picklename, "w"))
    print "done."


def keep_only_three_genes(unique_networks, mode):
    ''' remove networks with fewer than 3 nodes and unconnected'''
    print "filtering disconnected networks..."
    G = convert_dict_to_graphs(unique_networks, addzeros=False)
    for netID in G:
        if not len(G[netID].nodes())==3:
            print netID, "contains only", len(G[netID].nodes()), "node(s): removing."
            del unique_networks[netID]
            continue

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    backup(picklename)
    print "pickling", len(unique_networks), "connected unique networks to", picklename, "."
    cPickle.dump(unique_networks, file(picklename, "w"))
    print "done."


if __name__ == '__main__':
    generate_all_networks()
    networks = cPickle.load(file("all_networks.db"))
    #networks = dict((k, networks[k]) for k in range(500)) # enable for quick check
    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained

    #mode, tag_input_gene = "without_morphogene", None # >3000 # to compare with the paper
    #mode, tag_input_gene = "with_morphogene", "rr"     # 9612 # Hannes's favourite
    mode, tag_input_gene = "without_morphogene", "rr" # 9612   # Heike's favourite

    check_isomorphism(networks, mode, tag_input_gene) # takes 2 hrs
    unique_networks = cPickle.load(file("unique_networks_"+mode+".db"))
    print "found", len(unique_networks), "unique networks." 
    keep_only_three_genes(unique_networks, mode)
    filter_disconnected(unique_networks, mode)
    
    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
