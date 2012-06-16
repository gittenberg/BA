
d1 = [1, 0, 1, 1]
d2 = [1, 0, 1, 0]
d3 = [1, 0, 0, 1]

print d1
print d2

print 0 and 1
print 1 and 1
print (d1 and d2) and d3 # unexpected!!
print [d1[i] and d2[i] and d3[i] for i in range(4)] # is what we want!
