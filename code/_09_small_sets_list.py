''' This script takes the dict of sub-gps codes (which is large)
and creates a list of all 480679 unique sub-gps codes which occur
'''

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
