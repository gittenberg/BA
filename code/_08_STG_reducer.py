from datetime import datetime
tstart = datetime.now()

import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps


def subparset(parset, is_m1_in, is_m2_in):
    tmp = {key:{tuple(y for y in context if y!="m1" and y!="m2"):parset[key][context] \
                for context in parset[key].keys() \
                if key!="rr" or ("m1" in context)==is_m1_in and ("m2" in context)==is_m2_in} \
           for key in parset.keys() if key!="m1" and key!="m2"}
    return tmp
    

if __name__=='__main__':
    mode = "with_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."
    pstotal = 0
    graphcount = 0
    
    combis = [(False, False), (True, False), (False, True)] # low, medium, high
    
    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."
    split_gps_store = dict() # will be {nwkey:[encoding_of_split_gps1, ..., encoding_of_split_gps3]}
    
    allsubgpss = set()
    for nwkey in networks:
        if nwkey >= 2: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        #print networks[nwkey]

        mc = dict_to_model(networks[nwkey], add_morphogene)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            for combi in combis:
                #print subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1])
                subgps = encode_gps(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))
                allsubgpss.add(subgps)
            #print gps
            #print encode_gps(gps)
        print len(allsubgpss)
        split_gps_store[nwkey] = [npsc, pstotal, len(allsubgpss)]

        tend = datetime.now()
        print "total execution time:", tend-tstart
    
    print "pickling results to: split_gps_store.pkl"
    cPickle.dump(split_gps_store, file("split_gps_store.pkl", "w"))
    print "done."
    