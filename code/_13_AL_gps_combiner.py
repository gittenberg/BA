from datetime import datetime
tstart = datetime.now()

import sys
import shelve
import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps_full
from _08_STG_reducer import subparset

if __name__=='__main__':
    print "--------------------------------------------------------------------"
    print "running _13_AL_gps_combiner.py"
    combis = [(False, False), (True, False), (False, True)] # low, medium, high
    small_gps_pass_shelvename = "_12_small_gps_pass_test_AL_from_unconstrained_without_overregulated.db"
    d = shelve.open(small_gps_pass_shelvename)    
    combined_results_shelvename = "_13_combined_results_AL_from_unconstrained_without_overregulated.db"
    crs = shelve.open(combined_results_shelvename)
    picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
    networks = cPickle.load(file(picklename))

    start_nwkey = 0
    tocheck = len(networks)
    '''
    if not sys.argv[1]:
        start_nwkey = 0
    else:
        start_nwkey = int(sys.argv[1])
    if not sys.argv[2]:
        tocheck = 1000 #tocheck = len(networks)
    else:
        tocheck = int(sys.argv[2])
    '''
    
    # main loop
    print "considering networks from", start_nwkey, "to", start_nwkey+tocheck-1, "."
    current = 0
    pstotal = 0
    for nwkey in networks:
        # disable this to keep overregulated networks
        if networks[nwkey][('bb', 'rr')]!='0' and networks[nwkey][('gg', 'rr')]!='0' and networks[nwkey][('rr', 'rr')]!='0': 
            print "network", nwkey, "is overregulated, skipping."
            continue # we skip if rr is overregulated (too slow)
        current += 1
        if nwkey<start_nwkey or nwkey>=start_nwkey+tocheck: continue
        print "===================================================================================="
        print "considering nwkey:", nwkey
        mc = dict_to_model(networks[nwkey], add_morphogene=True)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."
        
        gpss = mc._psc.get_parameterSets()
        count_accepted = 0
        for gps in gpss:
            # decompose gps code into 3 small gps codes
            subgps = dict((combi, encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))) for combi in combis)
            accepted = d[subgps[combis[0]]][0] and d[subgps[combis[1]]][1] and d[subgps[combis[2]]][0]
            #print accepted
            if accepted:
                count_accepted += 1
        results = [count_accepted, npsc, count_accepted*1.0/npsc]
        print results
        crs[str(nwkey)] = results
        tend = datetime.now()
        print "total execution time:", tend - tstart
        print "expected finishing time:", tstart + (tend - tstart) * tocheck / current
    
    d.close()
    crs.close()
    print "done."
