import cPickle
import shelve
from _01_graph_enumerator import convert_dict_to_graphs
from _03_database_functions import decode_gps

split_gps = cPickle.load(file("all_small_gps_encodings.pkl"))

# the main part of this script still assumes that split_gps is a dict. TODO: change

print len(split_gps)
print split_gps[0] # parsets for this nwkey, total parsets so far, subparsets for this nwkey)
print split_gps[19682] # parsets for this nwkey, total parsets so far, subparsets for this nwkey)


networks = cPickle.load(file("all_networks.db"))
print "found", len(networks), "networks." # 3^9 = 19683 if unconstrained

shelvefilename = "unique_small_gps_codes.remote_generated.db"
d = shelve.open(shelvefilename)    
for nwkey in [0, 1, 2, 3, 19681, 19682]:
    strnwkey = str(nwkey) # because shelve only accepts string keys
    print strnwkey
    print networks[nwkey]
    IG = convert_dict_to_graphs({nwkey:networks[nwkey]})[nwkey]
    #print IG.edges()
    print "example item:", list(d[strnwkey])[0]
    print "converted to gps:", decode_gps(int(list(d[strnwkey])[0]), IG)
    print "longest code:", max(len(code) for code in d[strnwkey])
    print "shortest code:", min(len(code) for code in d[strnwkey])
    print "codes for nwkey:", len(d[strnwkey])
    
print max([int(key) for key in d.keys()])