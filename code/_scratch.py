import shelve
import sys

for i, arg in enumerate(sys.argv): 
    print i, arg
    

#pssname = "passing_sets.db"
#pssname = "combined_results.db"
pssname = "small_gps_pass_test_AL.db"
d = shelve.open(pssname)

for key in d:
    #print key, d[key]
    pass
print len(d)
'''
#print d.keys()    
#print d.values()    
'''