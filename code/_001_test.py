import cPickle, shelve

####################################################

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))

print len(networks) # 9612

####################################################

shelvefilename = "_13_combined_results_AL_from_unconstrained_without_overregulated.db"
combiresults = shelve.open(shelvefilename)    

print len(combiresults) # 4812???

####################################################

shelvefilename = "combined_results_AL.db"
combiresults = shelve.open(shelvefilename)    

print len(combiresults) # 9612???

####################################################

shelvefilename = "_12_small_gps_pass_test_AL_from_unconstrained_without_overregulated.db"
d = shelve.open(shelvefilename)    

print len(d) # 318796

for key in d.keys()[:5]:
    print key
    pass

####################################################

shelvefilename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"

d = shelve.open(shelvefilename)    
#print d.keys()
print d["4"]

print len(d.keys()) # 6642

####################################################

shelvefilename = "small_gps_pass_test_from_unconstrained_without_overregulated.db"
d = shelve.open(shelvefilename)    

print len(d.keys()) # 318796

#print d.keys()
#print d["4"]

for key in d.keys()[:5]:
    print key
    #pass

