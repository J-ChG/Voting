# typical filter header

import sys
import support
import json

myargs, lastArg = support.getopts(sys.argv)
inFile = lastArg


with open(inFile, 'r') as f:
     (nC, nV, Model, eType, nCases, infile, labels, dataDict) = json.load(f)
f.close()

for i in labels:
    assert i in support.allLabels, "unknown label "+i

for idx in range(nCases):
    # do something to dataDict[ ] ...
