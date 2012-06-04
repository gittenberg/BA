from datetime import datetime
tstart = datetime.now()

import cPickle

allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))

print "hi."

tend = datetime.now()
print "total execution time:", tend-tstart
