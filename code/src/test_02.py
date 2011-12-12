import imp
import os
import networkx as nx #@UnresolvedImport

MC = imp.load_source("MC", os.path.join("ModelContainer.py"))

if __name__=='__main__':
    # this is a test graph
    #interactions = {("xx","yy"):"free", ("yy","xx"):"free"}
    interactions = {("xx","yy"):"+", ("yy","xx"):"-", ("yy","yy"):"+"}
    thresholds = {("xx","yy"):1, ("yy","xx"):1, ("yy","yy"):2}
    edges = interactions.keys()
    IG = nx.DiGraph()
    IG.add_edges_from(edges)

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
    
    for node in lpss:
        print "======="
        print node
        print "======="
        for lps in lpss[node]:
            print lps

    print "============"
    print "Filtering..."

    #CTLformula, CTLsearch = "(rr=2&bb=0&gg=1->EF(AG(gg=0)))&(rr=1&bb=0&gg=1->EF(AG(gg=1)))&(rr=0&bb=0&gg=0->EF(AG(gg=0)))", "forAll" # (left&middle&right), the gg=1 in left and middle is from the drawing on page 5
    
    #mc.filter_byCTL(CTLformula, search=CTLsearch)


    for parameterSet in mc._psc.get_parameterSets():
        print parameterSet 

    print "============"
    print "Exporting..."
    mc.export_commonSTG(Type="transitions", filename="mini_STG.gml", initialRules=None)

    print "Done."
