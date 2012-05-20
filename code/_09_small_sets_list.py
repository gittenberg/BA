import shelve
import cPickle

shelvefilename = "unique_small_gps_codes.remote_generated.db"
d = shelve.open(shelvefilename)    

allsets = set()

for key in d.keys():
    print key
    thisset = d[key]
    allsets = allsets.union(thisset)
    print "length of allsets:", len(allsets)
    
allsetslist = list(allsets)
allsetslist.sort() # in-place sorting

cPickle.dump(allsetslist, file("all_small_gps_encodings.pkl", "w"))
