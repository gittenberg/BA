import cPickle, shelve

####################################################

picklename = "small_gps_pass_test_AL_from_unconstrained_without_overregulated.db.pkl"
small_gps_codes = cPickle.load(file(picklename))

print len(small_gps_codes)
print small_gps_codes[4] # 

shelvefilename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"

d = shelve.open(shelvefilename)    
#print d.keys()
print d["4"]

for key in d.keys():
    #print key
    pass

print len(d.keys())

####################################################

shelvefilename = "small_gps_pass_test_from_unconstrained_without_overregulated.db"
d = shelve.open(shelvefilename)    

print len(d.keys())

#print d.keys()
#print d["4"]

for key in d.keys()[:5]:
    print key
    #pass

####################################################

picklename = "combined_results_AL_from_unconstrained_without_overregulated.db"
combiresults = cPickle.load(file(picklename))

print len(combiresults)

