from datetime import datetime
tstart = datetime.now()

import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps_full
from _08_STG_reducer import subparset

if __name__=='__main__':
    mode = "with_morphogene"
    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."
    
    combis = [(False, False), (True, False), (False, True)] # low, medium, high

    networks = cPickle.load(file(picklename))
    tocheck = len(networks)
    print "found", tocheck, "networks."
    
    pstotal = 0
    current = 0
    for nwkey in networks:
        current += 1
        if nwkey >= 2: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        mc = dict_to_model(networks[nwkey], add_morphogene)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."
        
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            # decompose gps code into 3 small gps codes
            # schau die einzelteile nach und merke dir, zu welchem aus lo, mid, high sie gehören
            # kombiniere die 0, 1 werte zu einem
            for combi in combis:
                subgps = encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))
                print subgps
                
        tend = datetime.now()
        print "total execution time:", tend - tstart
        print "expected finishing time:", tstart + (tend - tstart) * tocheck / current
        