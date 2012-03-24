import pickle
from graphenumerator import convert_dict_to_graphs

ic = pickle.load(file("isomorphy_classes.txt"))
print len(ic)

unique_networks = pickle.load(file("unique_networks.txt"))
print len(unique_networks)

G = convert_dict_to_graphs(unique_networks)




#count[label] = len([edge for edge in network1 if network1[edge]==label])

