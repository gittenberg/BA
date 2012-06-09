import shelve

shelvefilename = "small_gps_pass_test.db"
d = shelve.open(shelvefilename)    

print len(d)

#print "\n".join(d.keys()[:10])

for i, x in enumerate(d):
    if i < 100 or i > 399900:
        print i, x, d[x]