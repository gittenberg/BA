
import cPickle

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))
print "found", len(networks), "networks."

print networks[0]
print networks[1]