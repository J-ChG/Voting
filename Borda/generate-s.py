import random
import math
import json
import sys

# project support functions, to avoid duplication betweemn
# generation and processing.
import gencode


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

if "-p" in myargs:
    countStr =  myargs['-p']
else:
    countStr = "000"

outFileIC  = str(nCandidates) + "-" + str(nVoters) + "-IC-" + str(repeats) + "-s-" + countStr + '.json'
# outFileIAC = str(nCandidates) + "-" + str(nVoters) + "-IAC-" + str(repeats) + "-s-" + countStr + '.json'

spatialCases, allPaths = gencode.getSpatialTable (nCandidates)
nOrders = len(spatialCases)

# sanity check,
assert nOrders == 2**(nCandidates -1)
# we distinguish the number of possible sequences from the length of any sequence (they are all the same)
# This is distinct from the number of possible orders
nCases = len(allPaths)
lengthCases = len(allPaths[0])

allICresults = []
allIACresults = []

caseLengthDistribution = [0 for i in range(lengthCases)]
lengthChanged = False

for _ in range(repeats):

    # create a set of candidates
    candidatesSet  = random.sample(range(nVoters), k=nCandidates)
    candidatesSet.sort()

    ICresults = [-1 for i in range(nVoters)]
    IACresults = [0 for i in range(lengthCases)]  # all paths
    IACorder = [0 for i in range(lengthCases)] # individual path

    distance = candidatesSet.copy()
    orderChange = False

    # order is modified in-situ. It is important that oldOrder and order be different lists, even if content is the same.
    oldOrder = [i for i in range(nCandidates)]
    order = [i for i in range(nCandidates)]

    # initial situation. No  need to compute it.
    ballotType = 0
    ICresults[0] = 0
    IACorder[0] = 0
    IACresults[0] = 1
    IACindex = 0

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

                ballotType = spatialCases.index(order)
                # then process new one.
                oldOrder = order.copy()
                IACindex+=1
                if True:
                    IACorder[IACindex] = ballotType
                else:
                    add = trackExpand( IACorder, allPaths, IACindex, ballotType)
                    if add != 0:
                        IACindex += add
                        print("track expand fix", add)

        ICresults[i] = ballotType
        IACresults[IACindex] += 1

    try:
        x = ICresults.index(-1)
        # print(ICresults)
    except ValueError:
        True

    # sanity check code.
    btList = [0]
    for i in ICresults:
        if i != btList[-1]: # check is next ballottype is new.
            btList.append(i)
    try:
        caseLengthDistribution[len(btList)-1] += 1
    except IndexError:
        print("error in case length distribution")
        print(caseLengthDistribution, btList, len(btList))

    assert sum(IACresults) == nVoters, "error in IAC" + str(IACresults)
    try:
        x = allPaths.index(IACorder)
        allIACresults.append((x, IACresults))

    except ValueError:
        print("value of path not found", IACorder, candidatesSet)
        allPaths.append(IACorder)
        allIACresults.append((len(IACorder), IACresults))
        nCases+=1
        lengthChanged = True

    allICresults.append(ICresults)

with open(outFileIC, 'w') as f:
     json.dump(( nCandidates, nVoters, 'IC', allICresults), f)
f.close()

# with open(outFileIAC, 'w') as f:
#      json.dump(( nCandidates, nVoters, 'IAC', allIACresults), f)
# f.close()

print(nCases, lengthCases, caseLengthDistribution)

# statistics on range of values for the stages of the different paths.
IACstats = [ [0, [[nVoters, 0] for j in range(lengthCases)]] for i in range(nCases) ]
for (i,j) in allIACresults:
    IACstats[i][0]+=1
    for (k,l) in enumerate(j):
        IACstats[i][1][k][0] = l if l < IACstats[i][1][k][0] else IACstats[i][1][k][0]
        IACstats[i][1][k][1] = l if l > IACstats[i][1][k][1] else IACstats[i][1][k][1]

print (IACstats)
if lengthChanged:
    print("Modified paths")
    print(allPaths)
