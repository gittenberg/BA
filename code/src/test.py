import imp
import os
from os.path import join
import networkx as nx #@UnresolvedImport
import sqlite3

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if __name__=='__main__':
    # create database
    path = "C:\Users\MJS\gitprojects_2\BA\code\src"
    con = sqlite3.connect(join(path, 'filter_results.db'))
    
    # setup tables
    con.execute('''DROP TABLE IF EXISTS iagraphs''')
    con.execute('''DROP TABLE IF EXISTS edges''')

    # setup objects
    networks = ['Incoherent type 1 feed-forward']

    # strict, without morphogene
    interactions = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds = {("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}
    edges = interactions.keys()
    IG = nx.DiGraph()
    IG.add_edges_from(edges)

    # this is graph A in figure 2 of Cotterel/Sharpe
    # including "mm" doubles the number of original parameter sets and the number of filtered parameter sets
    
    # non-strict, with morphogene
    #interactions = {("mm","rr"):"obs+", ("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}

    # non-strict, without morphogene
    #interactions = {("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    
    # strict, with morphogene
    #interactions = {("mm","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    #thresholds = {("mm","rr"):1, ("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}

    '''
    mc = MC.ModelContainer()
    mc._NuSMVpath = r"C:\Progra~2\NuSMV\2.5.2\bin\NuSMV.exe"
    mc.set_IG(IG)
    for edge in edges:
        mc.set_thresholds(dict((edge, thresholds[edge]) for edge in edges))
    mc.set_edgeLabels(interactions)
    mc.set_initialStates()
    mc.initializePSC()
    # TODO: replacing this by MC.parameterSetup() would allow more flexibility like local constraints etc.
    
    lpss = mc._psc._localParameterSets
    print "PSC:",len(mc._psc)
    
    for gene in lpss:
        print "======="
        print gene
        print "======="
        for lps in lpss[gene]:
            print lps

    print "============"
    print "Filtering..."

    CTLformula, CTLsearch = "(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll" # (left&middle&right), the gg=1 in left and middle is from the drawing on page 5

    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=0))", "exists" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&AF(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EG(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
    #CTLformula, CTLsearch = "!(rr>0&bb>0&gg>0&EF(gg=0))", "forAll" #  12/202 bei thresholds = 1, obs* # Negation von Modell fuer linke Region 
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=1))", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer mittlere Region
    #CTLformula, CTLsearch = "EF(rr=0&bb=0&gg=1)", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer rechte Region
    
    #mc.filter_extremeAttractors('max', 'attrs', True, True)
    
    mc.filter_byCTL(CTLformula, search=CTLsearch)

    #ALformula = "?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.max(gg)=1)"
    #mc.filter_byAL(ALformula)

    for parameterSet in mc._psc.get_parameterSets():
        print parameterSet 

    print "============"
    print "Exporting..."
    mc.export_commonSTG(Type="transitions", filename="A_commonSTG_transitions_strict.gml", initialRules=None)

    print "Done."
    '''