import cPickle
import shelve

split_gps_store = cPickle.load(file("split_gps_store.pkl"))

test1 = [1, 2, 3]
test2 = [3, 4]

shelvefilename = "unique_small_gps_codes.db"
d = shelve.open(shelvefilename)    
print d["0"]
print d["1"]