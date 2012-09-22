
import imp
import os
import networkx as nx
from _02_regnet_generator import dict_to_model
from _03_database_functions import encode_gps, encode_gps_full, export_STG
from _03_database_functions import decode_gps_full
from _08_STG_reducer import subparset
from _12_AL_model_checker import filter_byAL

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

networks = dict()
nusmvpath = r"C:\NuSMV\2.5.4\bin\NuSMV.exe"                     # Samsung laptop
#nusmvpath = "C:\Progra~2\NuSMV\2.5.4\bin\NuSMV.exe"            # Acer laptop
    
for letter in 'A': # in C, unfortunately green is the input gene
    networks[letter] = dict()

networks['A']['name'] = '(A) Incoherent type 1 feed-forward'
networks['A']['interactions'] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
networks['A']['thresholds'] = {("rr","gg"):1, ("rr","bb"):2, ("bb","gg"):1, ("gg","gg"):1}

combis = [(False, False), (True, False), (False, True)] # low, medium, high
ALformulas = ["?(left: left.frozen(gg)&left.max(gg)=0)", "?(middle: middle.frozen(gg)&middle.min(gg)=1)",
              "?(right: right.frozen(gg)&right.max(gg)=0)"]

for letter in 'A': # in C, unfortunately green is the input gene
    print "===================================================================================="
    print "Considering network:", networks[letter]['name']
    interactions = networks[letter]['interactions']
    edges = interactions.keys()
    thresholds = networks[letter]['thresholds']
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
                
    mc = dict_to_model(interactions, thresholds=thresholds, add_morphogene=True)
    smallmc = dict_to_model(interactions, thresholds=thresholds, add_morphogene=False)

    lpss = mc._psc._localParameterSets
    print len(mc._psc), "parameter sets."

    gpss = mc._psc.get_parameterSets()
    countaccepted = 0
    countrejected = 0
    for gps in gpss:
        #print gps
        subgps = dict((combi, encode_gps_full(subparset(gps, is_m1_in=combi[0], is_m2_in=combi[1]))) for combi in combis)
        parameter_set_IG_list = [decode_gps_full(subgps[combi]) for combi in combis]
        parameter_sets = [elem[0] for elem in parameter_set_IG_list]
        accepted = all(filter_byAL(smallmc, parameter_sets[i], ALformulas[i]) for i in range(3))*1
        if accepted:
            print "accepting:", gps
            export_STG(mc, gps, filename="_nonboolean_"+letter+"_"+encode_gps(gps, base=10)+".gml", initialRules=None)
            countaccepted += 1
        else:
            print "rejecting:", gps
            countrejected += 1
    print "accepted:", countaccepted
    print "rejected:", countrejected
        