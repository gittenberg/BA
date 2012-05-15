
parset = {'gg': {('gg', 'rr'): 1, ('bb', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg',): 1, ('rr',): 1, (): 1, ('bb', 'gg'): 1, ('bb',): 1}, 
          'm1': {(): 0, ('m1',): 1}, 
          'rr': {('bb', 'gg', 'm1', 'm2'): 1, ('bb', 'm2', 'rr'): 1, ('bb', 'gg', 'm1'): 1, ('bb', 'm1'): 1, ('bb', 'gg', 'm2'): 1, ('rr',): 1, ('gg', 'm1', 'rr'): 1, ('gg', 'm1', 'm2'): 1, ('bb', 'rr'): 1, ('m2',): 1, ('gg', 'm1', 'm2', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg', 'm2'): 1, ('gg',): 1, ('bb', 'gg', 'm1', 'm2', 'rr'): 1, ('bb',): 1, ('gg', 'm2', 'rr'): 1, ('bb', 'gg', 'm1', 'rr'): 1, ('bb', 'gg'): 1, ('m1', 'm2', 'rr'): 1, ('bb', 'm1', 'm2', 'rr'): 1, ('bb', 'gg', 'm2', 'rr'): 1, ('gg', 'm1'): 1, ('bb', 'm1', 'm2'): 1, ('m2', 'rr'): 1, ('m1',): 1, ('gg', 'rr'): 1, ('m1', 'm2'): 1, ('bb', 'm1', 'rr'): 1, (): 1, ('bb', 'm2'): 1, ('m1', 'rr'): 1}, 
          'bb': {('gg', 'rr'): 1, ('bb', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg',): 1, ('rr',): 1, (): 1, ('bb', 'gg'): 1, ('bb',): 1}, 
          'm2': {('m2',): 1, (): 0}}

testlist = [[j for j in i.keys()  if 'm1' not in j and 'm2' not in j] for i in parset.values()]

for elem in testlist:
    print elem

#newparset = {key:value for value in newvalues for key in parset if key not in ['m1', 'm2'] and parset[key]}

#print newparset