import cPickle
from regnet_generator import dict_to_model

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))
print "found", len(networks), "networks."

print networks.keys()

#mc = dict_to_model(networks[9611], add_morphogene=False)
