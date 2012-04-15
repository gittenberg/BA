from datetime import datetime
tstart = datetime.now()

import cPickle
from shove import Shove
from regnet_generator import dict_to_model

if __name__=='__main__':
    #models_dict_name = "models_dictionary.db"
    #models_dict = Shove("file://"+models_dict_name, compress=True)
    #print "found", len(models_dict), "models."
    #print models_dict.keys()
    #print models_dict['1'] # error...
    
    # wenn das mit shove nicht funktioniert, dann muss man die models eben on-the-fly machen:
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    for network in networks:
        mc = dict_to_model(networks[network], add_morphogene=True)
        print network, ":", len(mc._psc), "parameter sets."
        if not network%10:
            tend = datetime.now()
            print "total execution time:", tend-tstart
    
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
    