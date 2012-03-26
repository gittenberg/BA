import shelve

s = shelve.open('unique_networks_with_morphogene.db')
try:
    s['key1'] = { 'int': 10, 'float':9.5, 'string':'Sample data' }
except:
    pass
try:
    s['key2'] = 666
finally:
    s.close()
    

s = shelve.open('unique_networks_with_morphogene.db')
try:
    existing = s['key2']
finally:
    s.close()

print existing
