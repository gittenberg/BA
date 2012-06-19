from datetime import datetime
tstart = datetime.now()

import os
import imp
import subprocess as SP
import cPickle
import shelve
from _03_database_functions import decode_gps_full

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))
LFG = imp.load_source("LFG", os.path.join("LanguageFileGenerator.py"))

if os.name != 'nt':
    print "running on linux."
    path="/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
elif os.name == 'nt':
    print "running on windows."
    path="C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
    #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop


def filter_single_parameterSet_byCTL(container, parameterSet, CTLspec, search="exists"):
    '''Adds indices to _filteredParametersIndexList for parameterSets that do not satisfy the CTL formula for all states (search="forAll") or for at least one state (search="exists").'''
    SMVpath = os.path.join(os.getcwd(), "temp.smv")
    if search == "exists":
        validation = "is false"
        formula = "!("+CTLspec+")"
    elif search == "forAll":
        validation = "is true"
        formula = "("+CTLspec+")"
    else:
        raise Exception("search should be exist or forAll!")

    accepted = False
    fileString = LFG.generate_smv(mc, parameterSet, formula)
        
    tempFile = open("temp.smv", "w")
    tempFile.write(fileString)
    tempFile.close()
    
    cmd = nusmvpath + " " + SMVpath
    output = SP.Popen(cmd, shell=True, stdin=SP.PIPE, stdout=SP.PIPE, stderr=SP.STDOUT)
    outputread = output.stdout.read()
    if "ERROR" in outputread or not "This is NuSMV" in outputread:
        raise Exception(outputread)
    if validation in outputread:
        accepted = True
    return accepted


if __name__=="__main__":
    CTLformulas = ["EF(AG(gg=0))", "AF(AG(gg=0))", "EF(AG(gg=1))", "AF(AG(gg=1))"]

    allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))
    lenallsets = len(allsetslist) 
    print lenallsets #910890
    
    shelvefilename = "small_gps_pass_test.test.db"
    d = shelve.open(shelvefilename)    

    #CTLspec = CTLformulas[0]
    
    start = 700000
    setstocheck = lenallsets - start
    
    for i, code in enumerate(allsetslist[start:start+setstocheck]):
        if not i%100 and i!=0:
            print i, "sets done"
            tend = datetime.now()
            print "total execution time:", tend - tstart
            print "expected finishing time:", tstart + (tend - tstart) * setstocheck / i
        tmp = []
        for CTLspec in CTLformulas:
            parameterset, IG = decode_gps_full(code)
            mc = MC.ModelContainer()
            mc.set_IG(IG)
            mc.set_thresholds(dict((edge, 1) for edge in mc._IG.edges()))
            mc.set_dynamics("asynchronous")
            mc.set_initialStates()
            
            accepted = filter_single_parameterSet_byCTL(mc, parameterset, CTLspec, search="exists")
            #if accepted: print "accepted:", code
            tmp.append(accepted*1)
        if tmp[0]!=tmp[1] or tmp[2]!=tmp[3]:
            print tmp
        d[code] = tmp
        
    d.close()
    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
    