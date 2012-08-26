
import cPickle, shelve

picklename = "small_gps_codes_from_unconstrained_excluding_overregulated.pkl"
small_gps_codes = cPickle.load(file(picklename))

print len(small_gps_codes)
print small_gps_codes[4] # 

shelvefilename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"

d = shelve.open(shelvefilename)    
#print d.keys()
print d["4"]
print len(d["1"])/3
for key in d.keys():
    #print key
    pass

print len(d.keys())
