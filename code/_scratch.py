import shelve

'''
small_gps_pass_shelvename = "small_gps_pass_test.db"
d = shelve.open(small_gps_pass_shelvename)    

for key in d.keys()[200:220]:
    print key, d[key]
'''

#pssname = "passing_sets.db"
#pssname = "combined_results.db"
pssname = "small_gps_pass_test_AL.db"
d = shelve.open(pssname)

for key in d:
    print key, d[key]
#print len(d)
#print d.keys()    
#print d.values()    
