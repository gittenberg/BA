''' This script takes the database of all 9612 connected unique (isomorphic)
networks with three nodes (by default with morphogene) and generates:

d: a shelve object which contains nwkey:[all codes of gps of subgraphs for all
   three combinations of morphogenes]
split_gps_store: a dict which contains nwkey:[number of gps, 
   cumulative number of gps, number of sub-gps in nwkey]
'''

from datetime import datetime
tstart = datetime.now()

import cPickle
import shelve
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps, encode_gps_full


def reduced_lps(parset, is_m1_in, is_m2_in, key):
    return dict((tuple(y for y in context if y != "m1" and y != "m2"), parset[key][context]) for context in parset[key].keys() if key != "rr" or ("m1" in context) == is_m1_in and ("m2" in context) == is_m2_in)

def subparset(parset, is_m1_in, is_m2_in):
    return dict((key, reduced_lps(parset, is_m1_in, is_m2_in, key)) for key in parset.keys() if key!="m1" and key!="m2")
    

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
    shelvefilename = "unique_small_gps_codes.db"
    d = shelve.open(shelvefilename)    
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
        thesesubgpss = set()
        for gps in gpss:
            for combi in combis:
                #print subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1])
                subgps = encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))
                # TODO: add nodes and edges???
                thesesubgpss.add(subgps)
            #print gps
            #print encode_gps(gps)
        allsubgpss = allsubgpss.union(thesesubgpss)
        print "unique small gps to date:", len(allsubgpss)
        split_gps_store[nwkey] = [npsc, pstotal, len(allsubgpss)]
        d[str(nwkey)] = thesesubgpss
        tend = datetime.now()
        print "total execution time:", tend-tstart

    d.close()    
    print "pickling results to: split_gps_store.pkl"
    cPickle.dump(split_gps_store, file("split_gps_store.test.pkl", "w"))
    print "done."
    