
from shove import Shove

data = Shove("file://testfile_shove.db", compress=True)

data["1"] = "example"
data["3"] = "bla"

print data

data.sync()

newdata = Shove("file://testfile_shove.db", compress=True)

print newdata
