from datetime import datetime
tstart = datetime.now()

import cPickle
import shelve
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps_full
from _08_STG_reducer import subparset


if __name__=='__main__':
    mode = "with_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."
    
    combis = [(False, False), (True, False), (False, True)] # low, medium, high
    #small_gps_pass_shelvename = "small_gps_pass_test_from_unconstrained_without_overregulated.db"
    small_gps_pass_shelvename = "_10_small_gps_pass_test.db"
    d = shelve.open(small_gps_pass_shelvename)    
    #combined_results_shelvename = "_11_combined_results_from_unconstrained_without_overregulated.db"
    combined_results_shelvename = "_11_combined_results.db"
    crs = shelve.open(combined_results_shelvename)
    #passing_sets_shelvename = "_11_passing_sets_from_unconstrained_without_overregulated.db"
    passing_sets_shelvename = "_11_passing_sets.db"
    pss = shelve.open(passing_sets_shelvename)

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    tocheck = len(networks) # tocheck = 4000 #
    print "found", tocheck, "networks."
    
    pstotal = 0
    current = 0
    for nwkey in networks:
        ## disable this to keep overregulated networks
        #if networks[nwkey][('bb', 'rr')]!='0' and networks[nwkey][('gg', 'rr')]!='0' and networks[nwkey][('rr', 'rr')]!='0': 
        #    print "network", nwkey, "is overregulated, skipping."
        #    continue # we skip if rr is overregulated (too slow)
        current += 1
        #if nwkey>=2: continue # enable for quick check
        #if nwkey<12000 or nwkey>=16000: continue
        #if nwkey<16000: continue
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        mc = dict_to_model(networks[nwkey], add_morphogene)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."
        
        gpss = mc._psc.get_parameterSets()
        count_exists = 0
        count_forall = 0
        pss_exists = []
        pss_forall = []
        for gps in gpss:
            # decompose gps code into 3 small gps codes
            subgps = dict((combi, encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))) for combi in combis)
            #d[subgps[combis[0]]]: left
            #d[subgps[combis[1]]]: middle
            #d[subgps[combis[2]]]: right
            exists = d[subgps[combis[0]]][0] and d[subgps[combis[1]]][2] and d[subgps[combis[2]]][0] # EFAG
            forall = d[subgps[combis[0]]][1] and d[subgps[combis[1]]][3] and d[subgps[combis[2]]][1] # AFAG
            #print exists, forall
            if exists==1:
                pss_exists.append(gps)
                count_exists += 1
            if forall==1:
                pss_forall.append(gps)
                count_forall += 1
            #for combi in combis:
                #subgps[combi] = encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))
                #print combi, subgps[combi], d[subgps[combi]]
        results = [count_exists, count_forall, npsc, count_exists*1.0/npsc, count_forall*1.0/npsc]
        print results
        crs[str(nwkey)] = results
        passing_sets = [pss_exists, pss_forall]
        #print passing_sets
        pss[str(nwkey)] = passing_sets
        tend = datetime.now()
        print "total execution time:", tend - tstart
        print "expected finishing time:", tstart + (tend - tstart) * tocheck / current
    
    d.close()
    crs.close()
    pss.close()
    print "done."
