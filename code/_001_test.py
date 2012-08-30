import cPickle, shelve

####################################################

shelvename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"
bla = shelve.open(shelvename)    

print shelvename
print sorted(bla.keys())[:10]
print len(bla) # 6642

####################################################

shelvename = "unique_small_gps_codes.full.remote_generated.db"
bla = shelve.open(shelvename)    

print shelvename
print sorted(bla.keys())[:10]
print len(bla) # 9612

####################################################

picklename = "small_gps_codes_from_unconstrained_excluding_overregulated.pkl"
sets = cPickle.load(file(picklename))

print picklename
print len(sets) # 6642

####################################################

#picklename = "small_gps_codes.pkl"
#sets = cPickle.load(file(picklename))

#print picklename
#print len(sets) # 910890

####################################################

picklename = "all_small_gps_encodings.pkl"
sets = cPickle.load(file(picklename))

print picklename
print len(sets) # 910890

####################################################

picklename = "all_small_gps_encodings_from_unconstrained_without_overregulated.pkl"
sets = cPickle.load(file(picklename))

print picklename
print len(sets) # 318796

####################################################

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))

print picklename
print len(networks) # 9612

####################################################

shelvefilename = "combined_results.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # 9612
# these are all (but derived from the Hannes constraint)

for key in combiresults.keys()[:5]:
    #print key, combiresults[key]
    pass

#for net in combiresults:
#    print net

####################################################

shelvefilename = "combined_results_AL.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # 9612
# these are all (but derived from the Hannes constraint)

for key in combiresults.keys()[:5]:
    #print key, combiresults[key]
    pass

#for net in combiresults:
#    print net

####################################################

shelvefilename = "_13_combined_results_AL_from_unconstrained_without_overregulated.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # 4812??? # TODO:check by independent method!!
# of these, the overregulated are excluded

####################################################

shelvefilename = "_11_combined_results_from_unconstrained_without_overregulated.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # 6642
# of these, the overregulated are excluded

####################################################

shelvefilename = "passing_sets.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # ???

####################################################

shelvefilename = "passing_sets_from_unconstrained_without_overregulated.db"
combiresults = shelve.open(shelvefilename)    

print shelvefilename
print len(combiresults) # ???

####################################################

shelvefilename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"

print shelvefilename
d = shelve.open(shelvefilename)    
#print d.keys()
print d["4"]

print len(d.keys()) # 6642

####################################################

shelvefilename = "unique_small_gps_codes.full.remote_generated.db"

print shelvefilename
d = shelve.open(shelvefilename)    
#print d.keys()
print d["4"]

print len(d.keys()) # 9612

####################################################

shelvefilename = "_12_small_gps_pass_test_AL_from_unconstrained_without_overregulated.db"
d = shelve.open(shelvefilename)    

print shelvefilename
print len(d) # 318796

for key in d.keys()[:5]:
    #print key
    pass

####################################################

shelvefilename = "small_gps_pass_test_from_unconstrained_without_overregulated.db"
d = shelve.open(shelvefilename)    

print shelvefilename
print len(d.keys()) # 318796

#print d.keys()
#print d["4"]

for key in d.keys()[:5]:
    #print key
    pass

####################################################

shelvefilename = "_12_small_gps_pass_test_AL.db"
d = shelve.open(shelvefilename)    

print shelvefilename
print len(d) # 910890

for key in d.keys()[:5]:
    #print key
    pass

####################################################

shelvefilename = "small_gps_pass_test.db"
d = shelve.open(shelvefilename)    

print shelvefilename
print len(d) # 910890

for key in d.keys()[:5]:
    #print key
    pass

