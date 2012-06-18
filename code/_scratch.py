import shelve

shname1 = "combined_results.db"
d1 = shelve.open(shname1)
shname2 = "small_gps_pass_test.db"
d2 = shelve.open(shname2)
shname3 = "passing_sets.db"
d3 = shelve.open(shname3)

print len(d1)
for key in d1.keys()[0:20]:
    print key, d1[key]
    
#print len(d2)
print len(d3)
#print d3.keys()
