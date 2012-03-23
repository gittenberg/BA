import pickle

ic = pickle.load(file("isomorphy_classes.txt"))
print ic

un = pickle.load(file("unique_networks.txt"))
print un
print len(un)

nets = pickle.load(file("allnetworks.txt"))
print len(nets)

print nets[8]
print nets[20]
print nets[216]

# these are indeed isomorphic, I checked 2 examples