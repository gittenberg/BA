
import shelve
import cPickle
from _02_regnet_generator import dict_to_model
from _12_AL_model_checker import filter_byAL

def remove_zero_edges(networks):
    print "found", len(networks), "networks.\nremoving null edges...",
    for nw in networks:
        networks[nw] = dict((k, v) for (k, v) in networks[nw].items() if v!='0')
    print "done."
    return networks
    
def lookup_graph_number(ig): # because dicts are non-hashable, we cannot just revert allnetworks
    #print "looking up graph:", ig
    for nw in allnetworks:
        #print "checking:", allnetworks[nw]
        if allnetworks[nw]==ig:
            return nw
    # only executed if never found:
    print "interaction graph not found!"
    return -1

def lookup_iso_rep(number):
    for isoclass in isoclasses:
        if number in isoclasses[isoclass]:
            return isoclass
    # only executed if never found:
    print "isomorphism representative not found!"
    return -1

if __name__=='__main__':
    networks = dict()
    for letter in 'ABDEF': # in C, unfortunately green is the input gene
        networks[letter] = dict()
    
    networks['A']['name'] = '(A) Incoherent type 1 feed-forward'
    networks['A']['interactions'] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","gg"):"+"}
    
    networks['B']['name'] = '(B) Mutual inhibition'
    networks['B']['interactions'] = {("rr","gg"):"+", ("rr","bb"):"+", ("bb","gg"):"-", ("gg","bb"):"-"}
    
    networks['D']['name'] = '(D) Overlapping domains'
    networks['D']['interactions'] = {("rr","gg"):"-", ("rr","bb"):"+", ("bb","gg"):"+", ("gg","rr"):"-"}
    
    networks['E']['name'] = '(E) Bistable'
    networks['E']['interactions'] = {("rr","gg"):"-", ("gg","bb"):"-", ("bb","gg"):"+", ("bb","bb"):"+"}
    
    networks['F']['name'] = '(F) Classical'
    networks['F']['interactions'] = {("rr","gg"):"-", ("rr","bb"):"-", ("bb","gg"):"-", ("gg","gg"):"+", ("bb","bb"):"+"}
    
    allnetworks = cPickle.load(file("all_networks.db"))
    allnetworks = remove_zero_edges(allnetworks)
    
    combined_results_shelvenames = ["combined_results_AL.db", "combined_results.db"]

    iso_classes_name = "isomorphy_classes_without_morphogene.db"
    isoclasses = cPickle.load(file(iso_classes_name))
    #print isoclasses
    
    for crsname in combined_results_shelvenames:
        print "========================================="
        print "using results from:", crsname
        crs = shelve.open(crsname)
        for net in networks:
            print net #, networks[net]['interactions']
            graph_number = lookup_graph_number(networks[net]['interactions'])
            iso_graph_number = lookup_iso_rep(graph_number) 
            print iso_graph_number 
            print crs[str(iso_graph_number)]
            #print dict_to_model(networks[net]['interactions'], add_morphogene=True)

    print "========================================="
    print "AL model checking"
    crs = shelve.open(combined_results_shelvenames[0])
    numbers = [7747, 7423, 7969, 9349, 14284] # TODO: this should be generated in the above loop (simple)
    # I see where the problem is: gg=1 can be in everywhere, despite the suggestive name...
    ALformula = "(?(left: left.frozen(gg)&left.max(gg)=0)) & (?(middle: middle.frozen(gg)&middle.min(gg)=1)) & (?(right: right.frozen(gg)&right.max(gg)=0))"
    #ALformula = "(?(left, right: left.frozen(gg)&left.max(gg)=0&right.frozen(gg)&right.max(gg)=0)) & (?(middle: middle.frozen(gg)&middle.min(gg)=1))"
    for number in numbers:
        mc = dict_to_model(allnetworks[number], add_morphogene=True)
        gpss = mc._psc.get_parameterSets()
        count_accepted = 0
        for gps in gpss:
            #print gps
            accepted = filter_byAL(mc, gps, ALformula)
            print accepted
        
