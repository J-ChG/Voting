import random
import math
import json
import sys
# import os.path
from os import path

# project support functions, to avoid duplication betweemn
# generation and processing.

import support

# this programme generates elections according to an IC model, with an eye to
# eventually also generate an IAC one.
# the output is a json file containing a tuple with
# nCandidates, nVoters, type, results
# In the IC case, the outcome is a vector of size nVoters, with an
# index into one of the possible outcomes. (nCases)

# the model implicitly acknowledges that there is a limited number of potential ballots.
# In the random case, it is c! possibilities. In the spatial case, it is smaller.

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            if len(argv) > 1:
              opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
            else:
              opts[argv[0]] = []
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

myargs = getopts(sys.argv)

if "-h" in myargs:
  print ("options are: -v # -c # -r # [-p prefix ]")
  exit(0)

if "-v" in myargs:
    nVoters = int(myargs['-v'])
else:
    nVoters = 0
if "-c" in myargs:
    nCandidates = int(myargs['-c'])
else:
    nCandidates = 0

if "-r" in myargs:
  repeats = int(myargs['-r'])
else:
  repeats = 1000

assert nCandidates * nVoters != 0, "Wrong values for #candidates or #voters"

variants = 0
while True:
    countStr = (str(variants)).zfill(3)
    outFileIC  = str(nCandidates) + "-" + str(nVoters) + "-IC-" + str(repeats) + "-s-" + countStr + '.json'
    if not path.exists(outFileIC):
        break
    else:
        variants += 1

spatialCases = support.spatialOrders(nCandidates)
nOrders = len(spatialCases)
allICresults = []
allCases = support.ListTable(spatialCases)

# we distinguish the number of possible sequences from the length of any sequence (they are all the same)
# This is distinct from the number of possible orders

for _ in range(repeats):

    # create a set of candidates
    candidatesSet  = random.sample(range(nVoters), k=nCandidates)
    candidatesSet.sort()

    ICresults = [-1 for i in range(nVoters)]

    distance = candidatesSet.copy()
    orderChange = False

    # order is modified in-situ. It is important that oldOrder and order be different lists, even if content is the same.
    oldOrder = [i for i in range(nCandidates)]
    order = [i for i in range(nCandidates)]

    # initial situation. No  need to compute it.
    ballotType = 0
    ICresults[0] = 0

    for i in range(1,nVoters):
        lastDistance = distance.copy()

        for j in range(nCandidates):
            if i < candidatesSet[j]:
                distance[j] -= 1
            elif i > candidatesSet[j]:
                distance[j] += 1
            else:
                distance[j] = 0

        for j in range(nCandidates-1, 0, -1):
            if distance[order[j]] < distance[order[j-1]]:
    #      distance[j-1],distance[j] = distance[j],distance[j-1]
                order[j-1],order[j] = order[j],order[j-1]
                ballotType = allCases.indexOf(order)
                oldOrder = order.copy()

        ICresults[i] = ballotType

    allICresults.append(ICresults)

    # sanity check code.

with open(outFileIC, 'w') as f:
     json.dump(( nCandidates, nVoters, 's', 'IC', spatialCases, allICresults), f)
f.close()

# with open(outFileIAC, 'w') as f:
#      json.dump(( nCandidates, nVoters, 'IAC', allIACresults), f)
# f.close()

# statistics on range of values for the stages of the different paths.
