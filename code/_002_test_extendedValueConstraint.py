
import cPickle
from _02_regnet_generator import dict_to_model
from _03_database_functions import export_STG

if __name__=='__main__':
    net = {('rr', 'bb'):'+', ('bb', 'rr'):'+'}

    mc = dict_to_model(net, add_morphogene=True, thresholds=None)
    print "found", len(mc._psc), "parameter sets."
    gpss = mc._psc.get_parameterSets()

    for gps in gpss:
        print gps

    print "exporting example STG..."

    export_STG(mc, gps, filename="example_network_STG.gml", initialRules=None)

    print "done."
