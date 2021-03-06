'''
from matplotlib import rc
rc('font',**{'family':'sans-serif','sans-serif':['Helvetica']})
## for Palatino and other serif fonts use:
#rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=True)
'''

import imp
import networkx as nx
import numpy as np
import pylab as pl
import shelve
import cPickle
from _05_psc_functions import export_STG
import os
from os.path import join

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

#combined_results_shelvenames = ["_13_combined_results_AL_from_unconstrained_without_overregulated.db", "_11_combined_results_from_unconstrained_without_overregulated.db"]
#combined_results_shelvenames = ["_13_combined_results_AL.db", "_11_combined_results.db"]
#combined_results_shelvenames = ["_13_combined_results_AL.db"]
#combined_results_shelvenames = ["_11_combined_results.db"]
combined_results_shelvenames = ["_13_combined_results_AL.db", "_11_combined_results.db", "_13_combined_results_AL_from_unconstrained_without_overregulated.db", "_11_combined_results_from_unconstrained_without_overregulated.db"]

picklename = "connected_unique_networks_three_nodes_with_morphogene.db"
networks = cPickle.load(file(picklename))
print picklename
print len(networks) # 9612
#print 2352, networks[2352]
#print 2354, networks[2354]

def create_overall_plots():
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
        pl.xlabel("Pass ratio")
        pl.ylabel("Number of networks (total ="+str(len(crs))+")")
        pl.xlim(xmin=0)
        pl.grid(True)
        pl.savefig(crsname+'.png')
        pl.show()

def create_overall_statistics():
    for crsname in combined_results_shelvenames:
        print "========================================="
        print "using results from:", crsname
        crs = shelve.open(crsname)
        print len(crs)
        size = len(crs['1']) # 5 or 3, this is how long the list crs[result] is
        posfraction = (size+1)/2 # 3 or 2, this is where the fraction of passing sets are stored
        ngpss = dict()
        for i in range(1, 10):
            ngpss[i] = np.array([0] * size)
        for result in crs:
            if True: #crs[result][posfraction]>0.7:
                nwkey = int(result)
                networks[nwkey] = {edge:networks[nwkey][edge] for edge in networks[nwkey] if networks[nwkey][edge]!='0'}
                #if networks[nwkey].has_key(('bb', 'gg')) and networks[nwkey].has_key(('rr', 'bb')):
                #if networks[nwkey].has_key(('bb', 'gg')):
                    #print result, crs[result]
                    #print networks[nwkey]
                numedges = len(networks[nwkey])
                ngpss[numedges] += crs[result]
                '''
                IG = nx.DiGraph()
                IG.add_edges_from(networks[nwkey].keys())
                mc = MC.ModelContainer()
                mc.set_IG(IG)
                mc.set_edgeLabels(networks[nwkey])
                thresholds = dict((edge, 1) for edge in networks[nwkey].keys())
                mc.set_thresholds(thresholds)
        
                mc.set_initialStates()
                mc.set_dynamics("asynchronous")
                mc.initializePSC()
                gpss = mc._psc.get_parameterSets()
                for gps in gpss:
                    print gps
                print "encoding the last gps to test_unregulated_gg.gml"
                export_STG(mc, gps, filename="test_unregulated_gg.gml", initialRules=None)
                '''
        print "========================================="
        for i in range(1, 10):
            print i, ngpss[i]
            if ngpss[i][size/2]!=0:
                print 1.0*ngpss[i][size/2-1]/ngpss[i][size/2]
        print sum(ngpss[i] for i in range(1, 10))
    
def special_example():
    for crsname in combined_results_shelvenames:
        print "========================================="
        print "using results from:", crsname
        crs = shelve.open(crsname)
        print len(crs)
        # network 7465 example for gg self-regulating and just a few edges
        #network = {('gg', 'bb'): '-', ('gg', 'gg'): '+', ('bb', 'gg'): '-', ('gg', 'rr'): '-'}
        network = {("m1","m1"):"+", ("m1","rr"):"+", ("m2","m2"):"+", ("m2","rr"):"+", ('gg', 'bb'): '-', ('gg', 'gg'): '+', ('bb', 'gg'): '-', ('gg', 'rr'): '-'}
        #if networks[nwkey].has_key(('bb', 'gg')) and networks[nwkey].has_key(('rr', 'bb')):
        print crs['7465']
        print network
        IG = nx.DiGraph()
        IG.add_edges_from(network.keys())
        mc = MC.ModelContainer()
        mc.set_IG(IG)
        mc.set_edgeLabels(network)
        thresholds = dict((edge, 1) for edge in network.keys())
        mc.set_thresholds(thresholds)

        mc.set_initialStates()
        mc.set_dynamics("asynchronous")
        mc.initializePSC()
        gpss = mc._psc.get_parameterSets()
        for gps in gpss:
            print gps
        print "encoding the last gps to test_unregulated_gg.gml"
        export_STG(mc, gps, filename="test_unregulated_gg.gml", initialRules=None)
    
def count_nonzeros(): 
    for crsname in combined_results_shelvenames:
        print "========================================="
        print "using results from:", crsname
        crs = shelve.open(crsname)
        print len(crs)
        print "zeros:", len({key:crs[key] for key in crs if crs[key][0]==0})
        print "non-zeros:", len({key:crs[key] for key in crs if crs[key][0]!=0})

if __name__=='__main__':
    create_overall_plots()
    #create_overall_statistics()
    #special_example()
    count_nonzeros()