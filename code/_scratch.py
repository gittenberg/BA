import shelve

'''
small_gps_pass_shelvename = "small_gps_pass_test.db"
d = shelve.open(small_gps_pass_shelvename)    

for key in d.keys()[200:220]:
    print key, d[key]
'''

pssname = "combined_results.db"
d = shelve.open(pssname)

print d.keys()    
print d.values()    
