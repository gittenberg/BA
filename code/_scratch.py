import shelve
import cPickle

shelvefilename = "unique_small_gps_codes.remote_generated.db"
d = shelve.open(shelvefilename)    

x = d['0']

print len(x)
print len(d)
print list(x)[:20]

split_gps_store = cPickle.load(file("split_gps_store.pkl"))

print len(split_gps_store.keys())

print split_gps_store[0]
