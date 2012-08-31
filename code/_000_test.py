
import cPickle
import shelve

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
    not_overregulated_networks = []

    for nwkey in networks:
        if is_overregulated(networks[nwkey]):
            #print "network", nwkey, "is overregulated, skipping."
            continue
        else:
            not_overregulated_networks.append(nwkey)
            counter += 1
    #print "found", counter, "reasonably regulated networks"    
    print "found", len(not_overregulated_networks), "reasonably regulated networks"
    cPickle.dump(not_overregulated_networks, file("_000_not_overregulated_networks.pkl", "w"))

    non = cPickle.load(open("_000_not_overregulated_networks.pkl"))
    #print len(non)

    shelvefile = "__for_testing.db"
    d = shelve.open(shelvefile)    
    print len(d.keys())
    
    weird_keys = sorted([int(key) for key in d.keys()])
    #print weird_keys
    
    for key in non:
        if key not in weird_keys:
            print key, "missing from 4812!"