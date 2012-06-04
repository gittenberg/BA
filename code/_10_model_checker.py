from datetime import datetime
tstart = datetime.now()

import os
import imp
import subprocess as SP
import cPickle
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

CTLformulas = ["True", "False", "EFAG(gg=0)", "AFAG(gg=0)", "EFAG(gg=1)", "AFAG(gg=1)"]



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
    fileString = LFG.generate_smv(parameterSet, formula)
    print "so far, so good."
    
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
    allsetslist = cPickle.load(file("all_small_gps_encodings.pkl"))
    print len(allsetslist) #910890
    
    CTLspec = CTLformulas[0]
    
    for code in allsetslist[:10]:
        parameterset, IG = decode_gps_full(code)
        mc = MC.ModelContainer()
        mc.set_IG(IG)
        # is this required?
        mc.set_thresholds(dict((edge, 1) for edge in IG.edges()))
        # is this required?
        mc.initializePSC()

        filter_single_parameterSet_byCTL(mc, parameterset, CTLspec, search="exists")

    tend = datetime.now()
    print "total execution time:", tend-tstart
    print "done."
    