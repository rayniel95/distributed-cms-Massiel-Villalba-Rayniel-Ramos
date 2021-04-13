from tools import utils
import hashlib
import copy
import encodings.ascii

def interval_compare_test():
    interval_compare = utils.IntervalCompare(utils.Interval(6, 6, lexclude=True, rexclude=True), 3)

    print(interval_compare.compare({'chordId': 5}))
    print(interval_compare.compare({'chordId': 4}))

    # print(interval_compare.compare({'chordId': 2}))
    # print(interval_compare.compare({'chordId': 7}))

def sha1_test(string):
    print(hashlib.sha1(bytes(string, 'utf-8')).hexdigest())

if __name__ == '__main__':
    cadena = 'p1'
    sha1_test(cadena)