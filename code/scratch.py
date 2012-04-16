
from shove import Shove

models_dict_name = "models_dictionary.db"
models_dict = Shove("file://"+models_dict_name, compress=True)

print type(models_dict)

md = dict(models_dict)

print "found", len(models_dict), "models."
print md.keys()
print md["0"] # error...
