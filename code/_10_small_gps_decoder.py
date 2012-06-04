from datetime import datetime
tstart = datetime.now()

import cPickle
from _03_database_functions import decode_gps_full

allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))

for code in allsetslist[:10]:
    print decode_gps_full(code)


tend = datetime.now()
print "total execution time:", tend-tstart
