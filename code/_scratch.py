import shelve

shname = "test.db"

d = shelve.open(shname)

d["0"] = [1, 0, 0, 1]
d["1"] = [1, 0, 1, 1]
d["2"] = [1, 0, 1, 0]

d.close()

dd = shelve.open(shname)


#print (d1 and d2) and d3 # unexpected!!
#print [d1[i] and d2[i] and d3[i] for i in range(4)] # is what we want!

def combine_truth_values(*args):
    ll = len(args[0])
    return [all([arg[i] for arg in args])*1 for i in range(ll)]

print combine_truth_values(dd["0"], dd["1"], dd["2"])

print dd["0"], dd["1"], dd["2"]

