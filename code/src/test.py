import imp
import os
import networkx as nx #@UnresolvedImport

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if __name__=='__main__':
    # this is graph A in figure 2 of Cotterel/Sharpe
    # including "mm" doubles the number of original parameter sets and the number of filtered parameter sets
    #interactions = {("mm","rr"):"obs+", ("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    #interactions = {("rr","gg"):"obs+", ("rr","bb"):"obs+", ("bb","gg"):"obs-", ("gg","gg"):"obs+"}
    interactions = {("mm","rr"):"+", ("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    thresholds = {("mm","rr"):1, ("rr","gg"):2, ("rr","bb"):1, ("bb","gg"):1, ("gg","gg"):1}
    edges = interactions.keys()
    mc = MC.ModelContainer()
    IG = nx.DiGraph()
    IG.add_edges_from(edges)
    mc.set_IG(IG)
    for edge in edges:
        mc.set_thresholds(dict((edge, thresholds[edge]) for edge in edges))
    mc.set_edgeLabels(interactions)
    mc.compute_constraint_parameterSets()
    mc.set_initialStates()
    mc.initializePSC()
    mc._NuSMVpath = r"C:\Progra~2\NuSMV\2.5.2\bin\NuSMV.exe"
    
    lpss = mc._psc._localParameterSets
    print "PSC:",len(mc._psc)
    
    for gene in lpss:
        print "======="
        print gene
        print "======="
        for lps in lpss[gene]:
            print lps

    #print lpss

    print "Filtering..."

    CTLformula, CTLsearch = "(rr=2&bb=0&gg=0->EF(AG(gg=0)))&(rr=1&bb=0&gg=0->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
                                                                      #   ??/14 bei thresholds = 1, +-
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=0))", "exists" # 190/202 bei thresholds = 1, obs* # Modell fuer linke Region
                                                                  #   18/14 bei thresholds = 1, +-
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&AF(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
                                                                  #    0/14 bei thresholds = 1, +-
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EG(gg=0))", "exists" #   0/202 bei thresholds = 1, obs* # Modell fuer linke Region
                                                                  #    0/14 bei thresholds = 1, +-
    #CTLformula, CTLsearch = "!(rr>0&bb>0&gg>0&EF(gg=0))", "forAll" #  12/202 bei thresholds = 1, obs* # Negation von Modell fuer linke Region 
    #CTLformula, CTLsearch = "(rr>0&bb>0&gg>0&EF(gg=1))", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer mittlere Region
    #CTLformula, CTLsearch = "EF(rr=0&bb=0&gg=1)", "exists" # 202/202 bei thresholds = 1, obs* # Modell fuer rechte Region
    
    #mc.filter_extremeAttractors('max', 'attrs', True, True)
    
    ALformula = "?(rand,mitte: rand.frozen(gg)&rand.max(gg)=0&mitte.frozen(gg)&mitte.max(gg)=1)"
    #mc.filter_byCTL(CTLformula, search=CTLsearch)
    mc.filter_byAL(ALformula)
    print "Done."
