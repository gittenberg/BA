
bla = {'a':1, 'b':0}

print bla

blo = {key:bla[key] for key in bla.keys() if bla[key]!=0}

print blo