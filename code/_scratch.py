
parset = {'gg': {('gg', 'rr'): 2, ('bb', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg',): 1, ('rr',): 1, (): 1, ('bb', 'gg'): 1, ('bb',): 1}, 
          'm1': {(): 0, ('m1',): 1}, 
          'rr': {('bb', 'gg', 'm1', 'm2'): 1, ('bb', 'm2', 'rr'): 1, ('bb', 'gg', 'm1'): 1, ('bb', 'm1'): 1, ('bb', 'gg', 'm2'): 1, ('rr',): 1, ('gg', 'm1', 'rr'): 1, ('gg', 'm1', 'm2'): 1, ('bb', 'rr'): 1, ('m2',): 1, ('gg', 'm1', 'm2', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg', 'm2'): 1, ('gg',): 1, ('bb', 'gg', 'm1', 'm2', 'rr'): 1, ('bb',): 1, ('gg', 'm2', 'rr'): 1, ('bb', 'gg', 'm1', 'rr'): 1, ('bb', 'gg'): 1, ('m1', 'm2', 'rr'): 1, ('bb', 'm1', 'm2', 'rr'): 1, ('bb', 'gg', 'm2', 'rr'): 1, ('gg', 'm1'): 1, ('bb', 'm1', 'm2'): 1, ('m2', 'rr'): 1, ('m1',): 1, ('gg', 'rr'): 1, ('m1', 'm2'): 1, ('bb', 'm1', 'rr'): 1, (): 1, ('bb', 'm2'): 1, ('m1', 'rr'): 1}, 
          'bb': {('gg', 'rr'): 1, ('bb', 'rr'): 1, ('bb', 'gg', 'rr'): 0, ('gg',): 1, ('rr',): 1, (): 1, ('bb', 'gg'): 1, ('bb',): 1}, 
          'm2': {('m2',): 1, (): 0}}


def subparset(parset, is_m1_in, is_m2_in):
    return {key:{context:parset[key][context] for context in parset[key].keys() if key!='rr' or (('m1' in context)==is_m1_in and ('m2' in context)==is_m2_in)} for key in parset.keys() if key!='m1' and key!='m2'}

#subparset = {key:{context:parset[key][context] for context in parset[key].keys()} for key in parset.keys()}

tmp = subparset(parset, False, True)

print tmp==parset

for x in tmp.items():
    print x