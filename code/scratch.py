
import cPickle
from graphenumerator2 import convert_dict_to_graphs


def tag_node_match(node1, node2):
    return node1==node2


if __name__ == '__main__':
    #generate_all_networks()
    networks = cPickle.load(file("all_networks.db"))
    networks = dict((k, networks[k]) for k in range(20)) # enable for quick check
    
    for k in networks:
        print networks[k]

    G = convert_dict_to_graphs(networks, addzeros=False)
    
    print len(G)
    
    for graph in G.values():
        graph.node['rr'] = 'input gene'

    print G[1].nodes()
    
    print G[1].node # == dict('rr':{}, ...)
    print G[1].node['rr']
    