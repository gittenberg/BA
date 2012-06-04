from datetime import datetime
tstart = datetime.now()

import cPickle
from _01_graph_enumerator import convert_dict_to_graphs
from _03_database_functions import decode_gps

ctlformulas = ["EFAG(gg=0)", "AFAG(gg=0)", "EFAG(gg=1)", "AFAG(gg=1)"]

allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))
#print len(allsetslist) #480679

networks = cPickle.load(file("all_networks.db")) # we need this becaus we have to create the corresponding IG
for nwkey in [0, 1, 19681, 19682]:
    strnwkey = str(nwkey) # because shelve only accepts string keys
    print networks[nwkey]
    IG = convert_dict_to_graphs({nwkey:networks[nwkey]})[nwkey]
    #print IG.edges()


tend = datetime.now()
print "total execution time:", tend-tstart
print "done."
    