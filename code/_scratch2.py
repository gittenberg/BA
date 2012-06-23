
import cPickle

iso_classes_name = "isomorphy_classes_without_morphogene.db"
isoclasses = cPickle.load(file(iso_classes_name))

def lookup_iso_rep(number):
    for isoclass in isoclasses:
        if number in isoclasses[isoclass]:
            return isoclass
    # only executed if never found:
    print "isomorphism representative not found!"
    return -1

numbers = [7747, 7423, 18343, 12007, 14284]
for number in numbers:
    print number, lookup_iso_rep(number)
