
from _01_graph_enumerator import *

if __name__ == '__main__':
    generate_all_networks()
    networks = cPickle.load(file("all_networks.db"))
    print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained

    mode, tag_input_gene, tag_output_gene = "without_morphogene", None, None

    filter_disconnected(networks, mode)
    networks = cPickle.load(file("connected_networks_"+mode+".db"))

    keep_only_three_genes(networks, mode)
    three_gene_networks = cPickle.load(file("networks_three_nodes_"+mode+".db"))

    check_isomorphism(networks, mode, tag_input_gene, tag_output_gene) # takes 1:25 hrs, 3284 networks
    