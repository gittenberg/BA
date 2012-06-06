import shelve

shelvefilename = "small_gps_pass_test.db"
d = shelve.open(shelvefilename)    

for x in d:
    print x, d[x]