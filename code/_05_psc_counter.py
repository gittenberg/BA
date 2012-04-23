from datetime import datetime
tstart = datetime.now()

import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import *

if os.name != 'nt':
    print "running on linux."
    path="/home/bude/mjseeger/git/BA/code"
    nusmvpath = r"~/NuSMV-2.5.4-i386-redhat-linux-gnu/bin/NuSMV"    # Linux computer
elif os.name == 'nt':
    print "running on windows."
    path="C:\Users\MJS\git\BA\code"
    nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
    #nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop


if __name__=='__main__':
    mode = "with_morphogene"
    if mode=="with_morphogene":
        add_morphogene=True
    elif mode=="without_morphogene":
        add_morphogene=False
    else:
        print "warning: morphogene mode not set."
    pstotal = 0

    picklename = "connected_unique_networks_three_nodes_"+mode+".db"
    networks = cPickle.load(file(picklename))
    print "found", len(networks), "networks."

    for nwkey in networks:
        #if nwkey >= 100: continue # enable for quick check
        print "===================================================================================="
        print "considering nwkey:", nwkey
        
        mc = dict_to_model(networks[nwkey], add_morphogene)
        npsc = len(mc._psc)
        print nwkey, ":", npsc, "parameter sets."
        pstotal += npsc
        print nwkey, ":", pstotal, "parameter sets in total."

        tend = datetime.now()
        print "total execution time:", tend-tstart
    
    print "done."
    