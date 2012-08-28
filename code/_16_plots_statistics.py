import math
import pylab as pl
import shelve

combined_results_shelvenames = ["combined_results_AL.db", "combined_results_from_unconstrained_without_overregulated.db"]
for crsname in combined_results_shelvenames:
    print "========================================="
    print "using results from:", crsname
    crs = shelve.open(crsname)
    print len(crs)
    
    pl.figure()
    lastpos = len(crs.values()[0]) - 1
    x = [val[lastpos] for val in crs.values()]
    n, histbins, patches = pl.hist(x, bins=100, normed=0, histtype='stepfilled')
    pl.setp(patches, 'facecolor', 'g', 'alpha', 0.75)
    pl.xlabel("Fraction of accepted networks")
    pl.ylabel("Number of networks (total = 9612)")
    pl.xlim(xmin=0)
    pl.grid(True)
    pl.savefig(crsname+'.png')
    pl.show()