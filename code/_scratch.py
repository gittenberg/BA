import shelve
from operator import itemgetter

resultsdict = "combined_results_AL.db"
resultslist = []

d = shelve.open(resultsdict)

for key in d:
    thiskeylist = [int(key)] + d[key]
    resultslist.append(thiskeylist)

#sortkey = lambda elem: elem[3]

resultslist = sorted(resultslist, key=itemgetter(3, 1), reverse=True)

start = 6000
range = 1000

for i, elem in enumerate(resultslist):
    if i<=start or i>=start+range: continue
    print i, elem

