import shelve

shelvefilename = "small_gps_pass_test.01.db"
d = shelve.open(shelvefilename)    

print len(d)

print "\n".join(d.keys()[:10])

#for x in d:
#    print x, d[x]