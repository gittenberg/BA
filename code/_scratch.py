from datetime import datetime
tstart = datetime.now()

import cPickle

allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))

for i, code1 in enumerate(allsetslist[:1000]):
    first1, second1 = code1.split(".")
    for j in range(i+1, len(allsetslist[:1000])):
        code2 = allsetslist[j]
        first2, second2 = code2.split(".")
        if first1==first2:
            print "found equal codes with unequal interpretation:"
            print "i =", i, first1, second1
            print "j =", j, first2, second2

tend = datetime.now()
print "total execution time:", tend-tstart
