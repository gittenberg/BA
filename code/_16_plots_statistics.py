
import matplotlib
import shelve

combined_results_shelvenames = ["combined_results_AL.db", "combined_results.db"]
for crsname in combined_results_shelvenames:
    print "========================================="
    print "using results from:", crsname
    crs = shelve.open(crsname)
    print len(crs)