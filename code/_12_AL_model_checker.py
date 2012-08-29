from datetime import datetime
tstart = datetime.now()

import os
import imp
import cPickle
import shelve
from _03_database_functions import decode_gps_full

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
TS = imp.load_source("TS", os.path.join("TransitionSystem.py"))
AL = imp.load_source("AL", os.path.join("attractor_logic.py"))

def filter_single_parameterSet_byCTL(container, parameterSet, CTLspec, search="exists"):
    pass

def filter_byAL(container, parameterSet, ALformula):
    '''.'''
    accepted = 0
    ts = TS.TransitionSystem(container, parameterSet)
    if AL.evaluate(ALformula, ts, preprocessing=True):
        accepted = 1
    return accepted

if __name__=="__main__":
    ALformulas = ["?(outside: outside.frozen(gg)&outside.max(gg)=0)", "?(inside: inside.frozen(gg)&inside.min(gg)=1)",
                  "?(instable: !instable.frozen(gg))"]
    allsetslist = cPickle.load(file("all_small_gps_encodings_from_unconstrained_without_overregulated.pkl"))
    lenallsets = len(allsetslist) 
    print lenallsets #910890 (old)/318796 (new)
    
    shelvefilename = "_12_small_gps_pass_test_AL_from_unconstrained_without_overregulated.db"
    d = shelve.open(shelvefilename)    

    start = 0
    setstocheck = lenallsets

    for i, code in enumerate(allsetslist[start:start+setstocheck]):
        if not i%100 and i!=0:
            print i, "sets done"
            tend = datetime.now()
            print "total execution time:", tend - tstart
            print "expected finishing time:", tstart + (tend - tstart) * setstocheck / i
        tmp = []
        parameterSet, IG = decode_gps_full(code)
        mc = MC.ModelContainer()
        mc.set_IG(IG)
        mc.set_thresholds(dict((edge, 1) for edge in mc._IG.edges()))
        mc.set_dynamics("asynchronous")
        mc.set_initialStates()
        for ALformula in ALformulas:
            accepted = filter_byAL(mc, parameterSet, ALformula)
            tmp.append(accepted)
        d[code] = tmp

    d.close()
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
