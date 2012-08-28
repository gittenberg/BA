''' This script takes the dict of sub-gps codes (which is large)
and creates a list of all 910890 (old)/318796 (new) unique sub-gps codes which occur
'''

import shelve
import cPickle

shelvefilename = "unique_small_gps_codes_from_unconstrained_excluding_overregulated.db"
d = shelve.open(shelvefilename)    

allsets = set()

for key in d.keys():
    print key
    thisset = d[key]
    allsets = allsets.union(thisset)
    print "length of allsets:", len(allsets)
    
allsetslist = list(allsets)
allsetslist.sort() # in-place sorting

cPickle.dump(allsetslist, file("all_small_gps_encodings_from_unconstrained_without_overregulated.pkl", "w"))
