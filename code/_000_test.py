
import cPickle

def is_overregulated(network):
    if network[('bb', 'rr')]!='0' and network[('gg', 'rr')]!='0' and network[('rr', 'rr')]!='0': 
        return True
    else:
        return False

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))

if __name__=='__main__':
    print "found", len(networks), "networks."
    
    print "===================================================================================="
    counter = 0
    for nwkey in networks:
        if is_overregulated(networks[nwkey]):
            #print "network", nwkey, "is overregulated, skipping."
            continue
        else:
            counter += 1
    print "found", counter, "reasonably regulated networks"