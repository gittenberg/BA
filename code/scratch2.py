import pickle

ic = pickle.load(file("isomorphy_classes.txt"))
print ic
print len(ic)

un = pickle.load(file("unique_networks.txt"))
print un
print len(un)

networks = pickle.load(file("allnetworks.txt"))
print len(networks)

print networks[8]
print networks[20]
print networks[216]

# these are indeed isomorphic, I checked 2 examples