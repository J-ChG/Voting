# Revision March 30th. a new start

# created voteTable to avoid multiple computations thereof
# got rid of -i for input
# finished unification of spatial code

import sys
import math
import numpy as np
import random
import itertools
import json
import support

# arguments
# -V - verbose
# -T + par - process ties, with a threshold
# -p + par - pattern - used to set percentages for truncations.
# -v + par - number of voters
# -c + par - number of candidates
# -r + par - numnber of repetitions
# -a + par - number of  permutations (alternaticves)
# -t + par - Truncation level

# needs  -c #candidates -v #voters -r #repetitions + input file.

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        lA = argv[0]
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts, lA

myargs, lastArg = getopts(sys.argv)
inFile = lastArg

if False:
    if not '-i' in myargs:  # Example usage.
        print ("Missing -i option for input")
        sys.exit()
    else:
        inFile = myargs['-i']

if "-a" in myargs: # alternatives for permutations.
    nPermutations = int(myargs['-a'])
else:
    nPermutations = 1

if "-c" in myargs:
    nCandidates = int(myargs['-c'])
else:
    nCandidates = 0

if "-m" in myargs:
    modelType = myargs['-m']
    assert modelType == "r" or modelType == "s", "Unknown model type "+ modelType + "."
else:
    print("Need a model type: -m r (random) or s (spatial)")
    sys.exit(0)

if "-p" in myargs:
    patterns = [ int(i) for i in myargs["-p"].split()]
else:
    patterns = []

if "-r" in myargs:
    nCases = int(myargs['-r'])
else:
    nCases = 1

if "-s" in myargs:
    selection = myargs['-s']
else:
    selection = ''

if "-t" in myargs:
    truncLevel = int(myargs['-t'])
else:
    truncLevel = nCandidates

if "-T" in myargs:
    processTies = True
    threshold = int(myargs['-T']) # processTies is False unless a threshold value is given.
    print("cannot process ties in this version")
    processTies = False
else:
    processTies = False

if "-v" in myargs:
    nVoters = int(myargs['-v'])
else:
    nVoters = 0

if "-V" in myargs:
    verbose = True
else:
    verbose = False

if "-x" in myargs:
    xtractList = support.getSelections( myargs["-x"])
    xtractMode = True
else:
    xtractMode = False

assert nCases*nCandidates*nVoters != 0, "need minimally all of -c #candidates -v #voters -r #repetitions to be present"

# offset for candidates. In case we use a data file where candidates are 1..n
# here we'll consider 0..n-1
firstIdx = 0

# read cases to process from external file, in json format.

Labels1 = support.Labels1
Labels2 = support.Labels2
Labels3 = support.Labels3
LabelsStr = support.LabelsStr
MaxGroups = support.MaxGroups

# index practically start at 1 - we cannot skip index, even if we ask.
if selection == '':
    selectionSet = [i+1 for i in range(MaxGroups)]
else:
    selectionSet = support.getSelections(selection)
    selectionSet = [ i for i in selectionSet if i <= MaxGroups ] # truncate useless.

# vVector = []
# eType = 'IC' # can be 'IC' or 'IAC'
with open(inFile, 'r') as f:
     (c , v, m, eType, vVector) = json.load(f)
     assert c == nCandidates and v == nVoters, "mismatch between parameters and input file"
     assert eType == 'IC' or eType == 'IAC', "unknown type of vote (neither IC nor IAC)"
     assert modelType == m, "incompatible model - " + m
f.close()

# establish all possible orders.
# note that the "spatial model " also advertises itself as IC, so this distinctions
# should not be necessary.
if modelType == 'r': # randome.
    maxOrders = math.factorial(nCandidates)
    orders = list(itertools.permutations([i for i in range(nCandidates)]))
    assert maxOrders == len(orders), 'mismatch in random model.'
    ballotTypes = nVoters if eType == 'IC' else maxOrders # for IAC
else: # spatial
    orders, _ = support.buildSpatialTable(nCandidates)
    maxOrders = len(orders)
    ballotTypes = nVoters

#==============  Permutations and patterns

# patterns holds the data to process the random variations of elections
# 0: percentage of representation for truncation level
# 1: scaling factor to match percentage to number of voters. It is assumed that
# the number of voters is a multiple of 100. This could/should actually be derived from
# nVoters.
# 2: repetitions ???
# 3: nCandidates???

if patterns == []:
    patterns = [0 for i in range(nCandidates)]
    patterns[-1] = 100

assert len(patterns) == nCandidates, "mismatch between candidates and number of patterns"
assert sum(patterns) == 100, "sum of truncation patterns different from 100%"

# There is a relation with patterns and permutations. If the pattern is random, then
# we need permutations in its application.
if 100 in patterns:
    nPermutations = 1 # already set before, but does not hurt.

pattern = [patterns, nVoters / 100, nPermutations, nCandidates]

# exploit truncation profile.
# profile is list of percentages of cuts, adding up to 100
# this include possibility that it is fixed.
# maxdepth is depth to exploit.
# total is number of voters.
# scale is the translation from % to number of voters.
def buildProfile(profile, total, maxdepth):
   if 100 in profile:
      return [ profile.index(100)+1 for i in range (total) ]
   t = 0
   list = []
   scale = total/100
   for i in profile:
     t+=1
     list += [t for j in range(0,int(i*scale)) ]

   list += [maxdepth for j in range( total - len(list) )]
   return list

# data structures to keep track of results. These are standards
# used by algorithms.
# ballots will be filled from randomly generated data


# ballots collects the ballot order for all voters, complete with information
# on ties (indices 1 and 2)
ballots = np.zeros( (ballotTypes, nCandidates, 3), dtype=np.int32)
# numbers of each type of ballots.
ballotDistribution = np.zeros( ballotTypes, dtype=np.int32)
# based on profile, but by default there is no truncation.
# also not sure if it should be nCandidates or nCandidates -1
ballotTruncation = np.full( ballotTypes, truncLevel)
# Used to identify the Condorcet candidate

# this is a record of the votes.
# The original intent was to be compact, but this does not help with truncation patterns.
# So another built on top of this to process each class of votes.
def addtorecord( matrix, vector, index ):
    j = 0
    for i in vector:
        matrix[index, j, 0] = i
        matrix[index, j, 1] = matrix[index, j, 2] = 1
        j+=1

#=========================== Condorcet code

# the computation of Condorcet requires a precedence table (PT).
# that is, a NxN matrix (N is the number of candidates) where
# PT(i,j) is the number of times i is prefered over j

# execution of the precedence relations
# Full controls whether the level of truncation applies of not
# skipOver controls what we do with candidates not on the ballot (or truncated)
#   True means that they are not counted.
def buildPrecedenceTable( full=False, skipOver=True ):
    precedences = np.zeros( (nCandidates, nCandidates), dtype=np.int32)

    ii = 0
    for i in range(ballotTypes): # for all groups
        if full: # has to be here in case truncation is not uniform.
            theLimit = nCandidates
        else:
            theLimit = ballotTruncation[i]
        # external loop over all ballot types
        for _ in range(ballotDistribution[i]): # for all instances in group. The specific index is not relevant.
            candidatesDone = [False for k in range(nCandidates)]
            j = 0
            # middle loop over candidates
            while j< theLimit:
                cg = [] # list of candidates in tie group
                cgl = ballots[i,j,2] # identification of tie group. Valid only if a tie is flagged (value 2)
                # loop over peers in tie group.
                while (j < theLimit and ballots[i,j,1]==2 and ballots[i,j,2]==cgl):
                    cg += [ ballots[i,j,0] ]
                    j+=1
                # make sure we build the list of candidates to consider
                if cg == []:
                    cg = [ ballots[i,j,0] ]
                    j+=1
                # in all cases j points to the first location beyond the tie group.
                # then establish precedence of the members of the group over the rest of the ballot
                for c in cg:
                    for k in range(j, theLimit):
                        precedences[c- firstIdx ,  ballots[i,k,0]- firstIdx] += 1
                    candidatesDone[c- firstIdx ] = True
            ii += 1  # increment global counter.
            # finally precedence of candidates of ballot over
            # candidates not in ballot.
            # but it is conditional to a flag.
            if not skipOver:
                # print("not executed")
                cdT = [c for c in range(nCandidates) if candidatesDone[c]]
                cdF = [c for c in range(nCandidates) if not candidatesDone[c]]
    #            print(candidatesDone, cdT, cdF)
                for k in cdT:
                    for l in cdF:
                        precedences[k,l] += 1
        # and we are done!!!
    assert ii == nVoters, "missing cases in precedence construction " + ii
    return precedences

    # compute Condorcet
def computeCondorcet(PT): # PT == precedence table, built from buildPrecedenceTable
    TC = 0 # tentative Condorcet
    for i in range(nCandidates):
        TC = i
        for j in range(nCandidates):
            if (PT[i,j] <= PT[j,i]) and (j!=i):
                TC = nCandidates
        if TC != nCandidates:
            break
    if TC  == nCandidates: TC = -1
    return TC

def computeNotCondorcet(PT):
    NC = 0
    for i in range(nCandidates):
        NC = i
        for j in range(nCandidates):
            if (PT[i,j] > PT[j,i]):
                NC = nCandidates
                break
        if NC != nCandidates:
            break
    if NC  == nCandidates: NC = -1
    return NC

# The Copeland score exploits the PT but records results
# in a differential mode only.
# For each candidate, it indicates how often it is preferred to
# another.
def computeCopeland(PT):
    results = [0 for i in range(nCandidates)]
    for i in range(nCandidates):
        for j in range(nCandidates):
            if (j!=i):
                results[i] += 1 if PT[i,j] > PT[j,i] else -1 if  PT[i,j] < PT[j,i] else 0
    return results
# variation without precedence table.

# this one is hiding two alternatives, depending on whether or not we need to process ties.
def precedes(a,b):
    return simplePrecedes(a,b)

def simplePrecedes(a,b): # used when we are doing comparisons on full or truncated ballots
    aAhead = 0
    bAhead = 0
    for i in range(ballotTypes):
        for j in range( ballotTruncation[i] ):
            if ballots[i,j,0] == a:
                aAhead += ballotDistribution[i]
                break
            elif ballots[i,j,0] == b:
                bAhead += ballotDistribution[i]
                break
#    assert aAhead + bAhead == nVoters, "mismatch in precedence count"
    return aAhead > bAhead

def fullPrecedes(a,b):
    # ties and truncation complicate case analysis.
    # in the simplest case, both candidates  a and b are on the ballot, and not tied.
    # but either or both could not be on the ballot, and could be tied or not. 4 cases, and one with ties.
    # and whether or not we can proceed in the presence of ties requires scanning the whole ballot
    aAhead = 0
    bAhead = 0
    for i in range(ballotTypes):
        aFound = False
        bFound = False
        aGroup = 0
        bGroup = 0
        firstFound = -1
        for j in range( ballotTruncation[i] ):
            if ballots[i,j,0] == a:
                if ballots[i,j,1]==2:
                    aGroup = ballots[i,j,2]
                if firstFound == -1:
                    firstFound = a
                    aFound = True
                    if aGroup == 0:
                        aAhead += ballotDistribution[i]
                        break
                else:
                    break
            elif ballots[i,j,0] == b:
                if ballots[i,j,1]==2:
                    bGroup = ballots[i,j,2]
                if firstFound == -1:
                    firstFound = b
                    bFound = True
                    if bGroup == 0:
                        bAhead += ballotDistribution[i]
                        break
                else:
                    break
            else: # move to next line in current column
                continue
            if aGroup != 0 and aGroup == bGroup: # both found, and in tie group
                firstFound = -1
                break
            if aFound and bFound: # should not be there
                print('should have breaked before')
                break
        if firstFound == -1:
            print("missing a and/or b on ballot, or tie?)")
    return aAhead > bAhead

def checkCondorcet():
    # precedes handles truncation.
    cList = [i for i in range(nCandidates)]
    eSet = set() # elimination
    cSet = set(cList)
    while  cSet != set():
         # test for empty set
        c = cSet.pop()
        pSet = set() # precedes c
        for i in cSet:
            if precedes(i,c):
                pSet.add(i)
        if pSet != set():
            cSet &= pSet
            eSet.add(c)
        else:
            break # nothing found that precedes c.
    truism = True
    # now start again to check. for all that were not found to be preceded.
    # perform the inverse test.
    tSet = set(cList) - eSet - {c}
    for i in tSet:
        truism =  precedes(c,i)
        if not truism:
            break
    if not truism:
        return -1
    else:
        return c



#=============  Borda dominance.

def computeDominants():
    # build tables
    # use global definition of voteTally
    # compare
    scores = [0 for i in range(nCandidates) ]
    for i in range(nCandidates):
        for j in range(nCandidates):
            if j != i:
                greater = True
                for k in range(truncLevel):
                    if voteTally[i,k] < voteTally[j,k]:
                        greater = False
                        break
                if greater :
                    scores[i]+=1
    scores.sort(reverse=True)
    return scores

# compute number of candidates dominated by at least another candidate
def computeDominated():
    scores = 0
    for i in range(nCandidates):
        for j in range(nCandidates):
            if j != i:
                greater = False
                for k in range(truncLevel):
                    if voteTally[i,k] > voteTally[j,k]:
                        greater = True
                        break
                if not greater :
                    scores+=1
                    break
#    if scores == nCandidates:
#        print(voteTally)
    return scores

def isDominated(c):
    for i in range(nCandidates):
        if c != i:
            greater = True # assume i dominates c
            allEqual = True
            for k in range(truncLevel):
                if voteTally[i,k] < voteTally[c,k]:
                    greater = False # clearly not dominated
                    allEqual= False # not really necessary
                    break
                elif  voteTally[i,k] > voteTally[c,k]:
                    allEqual = False
            if greater and not allEqual:
                return True # one cas is all we need.
    return False

def dominates(a, b):
    allEqual = True
    for k in range(truncLevel):
        if voteTally[a,k] < voteTally[b,k]:
            return False # clearly dominated
        elif voteTally[a,k] > voteTally[b,k]:
            allEqual = False  #
    return  not allEqual # must make sure we exclude case of all equality.

# list of candidates who dominate c
def whoDominates( c ):
    result = []
    for i in range(nCandidates):
        if c != i:
            greater = True # assume i dominates c
            allEqual = True
            for k in range(truncLevel):
                if voteTally[i,k] < voteTally[c,k]:
                    greater = False # clearly not dominated
                    allEqual= False # not really necessary
                    break
                elif  voteTally[i,k] > voteTally[c,k]:
                    allEqual = False
            if greater and not allEqual:
                result.append(i)
    return result

def whoIsDominatedBy(c): # reverse of preceding.
    result = []
    for i in range(nCandidates):
        if c != i:
            greater = True # assume c dominates i
            allEqual = True
            for k in range(truncLevel):
                if voteTally[i,k] > voteTally[c,k]:
                    greater = False # clearly not dominated
                    allEqual= False # not really necessary
                    break
                elif  voteTally[i,k] < voteTally[c,k]:
                    allEqual = False
            if greater and not allEqual:
                result.append(i)
    return result


# Compute votes / candidates matrix
# returns a triplet of lists: borda dominants, non borda dominated, borda dominated
# construction of voteTall
def computeDominance():
    # incremental computation of voteTally while keeping track of "winners" and their evolution
    global voteTally
    voteTally = np.zeros( (nCandidates, nCandidates), dtype='int16' )
    # 1 is candidates, 2 is rounds - remember!!!
    maxVal = 0
    winSet = []
    for j in range(nCandidates):
        tmp = voteTally[j,0] = voteTable[j,0]
        if tmp > maxVal:
            winSet = [j]
            maxVal = tmp
        elif tmp == maxVal:
            winSet.append(j)

    classes = [ [] for i in range(nCandidates-1)]
    classes[0] = winSet
    winners = winSet.copy()
    potentialDominant = classes[0]
    for k in range(1,nCandidates-1): # rounds
        maxVal = 0
        winSet = []
        for j in range(nCandidates):
            voteTally[j,k] = voteTable[j,k] + voteTally[j,k-1]
        # find the highest value for candidates who were previous winners
        for j in winners:
            if voteTally[j,k] > maxVal:
                maxVal = voteTally[j,k]
        # now check if we have a new winner.
        for j in range(nCandidates):
            if j not in winners and voteTally[j,k] > maxVal:
                winSet.append(j)
        newSet = []
        # will have a Borda dominant winner if it is consistently
        # winning. This must be extablished.
        # first check if we had a candidate - has to be from round 0
        # winSet has to be null.
        if potentialDominant != [] and winSet == []:
            for j in potentialDominant:
                if voteTally[j,k] == maxVal:
                    newSet.append(j)
            potentialDominant = newSet
        else: # has be reset to 0 or new winner: no luck
            potentialDominant = []
        classes[k] = winSet
        winners += winSet

    # Last round, final values.
    for j in range(nCandidates):
        voteTally[j, nCandidates-1] = nVoters

    if  potentialDominant != []:
        exclusionSet = potentialDominant
    else:
        exclusionSet = winners

    bdFoundSet = []
    currentSmallest = exclusionSet[0]

    if True: # change of code XXX must be fixed at some point.
        for j in range(nCandidates):
            if  voteTally[ currentSmallest,0 ] > voteTally[j,0]:
                currentSmallest = j
        others = [ i for i in range(nCandidates) if i != currentSmallest]
        cSmallests = [currentSmallest]
        smallests = []
        for j in others:
            if voteTally[ currentSmallest,0 ] == voteTally[j,0]:
                cSmallests.append(j)

        for j in cSmallests:
            others = [ i for i in range(nCandidates) if i != j]
            smallest = True
            for l in range(1, nCandidates-1):
                for i in others:
                    if voteTally[ j,l ] > voteTally[i,l]:
                        smallest = False
                        break
                if not smallest:
                    break
            if smallest:
                bdFoundSet.append(j)
    else:
        for j in range(nCandidates):
            if j not in exclusionSet:
                smaller = True
                for k in range(nCandidates): # could be just winners
                    if k != j:
                        for l in range(nCandidates-1): # do not check last line#                                print(j, k, processingMTX[l,j ], processingMTX[l,k], processingMTX[l,j ] > processingMTX[l,k])
                            if  voteTally[ j,l ] > voteTally[k,l]:
                                smaller = False
                                break
                        if smaller:
                            bdFoundSet.append(j)
                            break # found one case.
                        else:
                            smaller = True # reset

    return potentialDominant, winners, bdFoundSet



#==================== Score functions.

# various support functions for alternative voting models.
def tailAverage (values, usedLength):
  m = len(values)
  if usedLength == m:
     return 0
  sum = 0
  for i in range(usedLength, m):
      sum+= values[i]
  return sum/(m-usedLength)

def rangeAverage (values, offset, triplet):
    j = 0
    top, bottom, list = triplet
    for i in range(top, bottom+1):
        j+=values[i+offset]
    return j/(bottom-top+1)

def ties1(score, offset, triplet):
    top, _, _ = triplet
    return score[offset+top]

def ties2(score, offset, triplet):
    _, bottom, _ = triplet
    return score[offset+bottom]

def tiesAVG(score, offset, triplet):
    return rangeAverage (score, offset, triplet)

def bsFromList (refList):
    return [ refList[i] if i in range(len(refList)) else 0 for i in range(nCandidates)]

# as well as data structures
ballotScores1 = [nCandidates -i  for i in range(nCandidates)]
ballotScores2 = [nCandidates -i -1  for i in range(nCandidates)]
ballotScores3 = [1/i  for i in range(1,nCandidates+1)]
ballotScoresGP1 = [25, 18, 15, 12, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1] # probably not correct.
ballotScoresGP0 = [9, 6, 4, 3, 2, 1]
#
def lBSform (k):
    return [((nCandidates -i -1)/(nCandidates -1))**k  for i in range(nCandidates) ]

bsL0 = [(nCandidates -i -1)/(nCandidates -1)  for i in range(nCandidates)]
bsLp2 = lBSform (2)
bsLr2 = lBSform (1.0/2)
bsLp3 = lBSform (3)
bsLr3 = lBSform (1.0/3)
#
bsC = lBSform (1.42554)

#
genBSform = lambda i, h, k, n: ((n**h - i**h) /  ( i**h *( n**h - 1) )) ** k
def myBShunc(i, h, k):
  return genBSform(i,h,k, nCandidates)
#
bsInv0 = [ myBShunc(i+1, 1, 1) for i in range(nCandidates)]
bsInvp2 = [ myBShunc(i+1, 1, 2) for i in range(nCandidates)]
bsInvr2 = [ myBShunc(i+1, 1, 1/float(2) ) for i in range(nCandidates)]
bsInvp3 = [ myBShunc(i+1, 1, 3) for i in range(nCandidates)]
bsInvr3 = [ myBShunc(i+1, 1, 1/float(3) ) for i in range(nCandidates)]
#
bsH2p1 = [ myBShunc(i+1, 2, 1) for i in range(nCandidates)]
bsH2p2 = [ myBShunc(i+1, 2, 2) for i in range(nCandidates)]
bsH2r2 = [ myBShunc(i+1, 2, 1/float(2)) for i in range(nCandidates)]
bsH3p1 = [ myBShunc(i+1, 3, 1) for i in range(nCandidates)]
bsH3p3 = [ myBShunc(i+1, 3, 3) for i in range(nCandidates)]
bsH3r3 = [ myBShunc(i+1, 3, 1/float(3)) for i in range(nCandidates)]

# bsFromABS1 = [0 for i in range(nCandidates)]
bsFromGP0 = bsFromList(ballotScoresGP0)
bsFromGP1 = bsFromList(ballotScoresGP1)
ballotScoresAP = [1  for i in range(nCandidates)]

tailScores0 = lambda x, y : 0
tailScoresNext = lambda x, y : x[y] if y < len(x) else 0
tailScoresAVG = lambda x, y : tailAverage(x, y)
tailScoresMDN = lambda x, y : tailMedian(x, y)
# tailScores2 = def(x,y,z):  ...

# ht = processing of head votes
# tt = processing of tail votes (not on ballot)
# tv = processing of tie vote
# tb = top/bottom - binary variable to indicate if we are dealing with the bottom or top of the range
def vote (ht, tt, tv, tb):
    global verbose
    results = [0 for i in range(nCandidates)]
    # external loop
    ii = 0
    for i in range(ballotTypes): # for each group.
        multiplicity = ballotDistribution[i]
        ties = [] # we keep track of the offsets of the tie groups.
        wasTie = False
        lastGen = 1 # indicators of occurrence of some tie group.
        currentTop = currentBottom = 0
        truncation = ballotTruncation[i]

        offset = tb * (nCandidates-truncation)
        present = [0 for i in range(nCandidates)]
        for j in range( truncation ):
            c = ballots[i,j,0]
            present[c - firstIdx ] = 1
            if ballots[i,j,1] == 2:
                if not wasTie:
                    wasTie = True
                    currentTop = currentBottom = j
                    tieList = []
                elif ballots[i,j,2] != lastGen : #  a new tie group.
                    lastGen += 1
                    ties += [ (currentTop, currentBottom, tieList) ]
                    tieList = []
                    currentTop = j
                currentBottom = j
                tieList+=[c]
            else :
                results[ c - firstIdx ] += ht[j+offset] * multiplicity
                if wasTie:
                    ties += [ (currentTop, currentBottom, tieList) ]
                    wasTie = False
                    lastGen = 1
                    tieList = []
            if wasTie: # case where we have reached the end and it was a tied group.            print("closing after tie")
                ties += [ (currentTop, currentBottom, tieList) ]
                # none of the following should be necessary.
                WasTie = False
                tieList = []
                lastGen = 1
            # add processing for ties. No need to check if it is empty or not.
            for t,b,l in ties:
                score = tv(ht, offset, (t,b,l))
                for c in l:
                    results[c - firstIdx] += score * multiplicity
            nullScore = tt(ht, truncation )
            for j in range(nCandidates):
                if present[j] == 0:
                    results[j] += nullScore * multiplicity
            if False:
                print ("intermediate results:", ballotDistribution[i], ballotTruncation[ii], results)

        ii += multiplicity
    #    print (ballots[i], results, ballotDistribution[i], ballotTruncation[i], offset, nullScore)
    assert ii == nVoters, "vote not done for right number of candidates " + str(ii)

    return results

# specific to spatial model
def builtTies(distance, order, threshold):
  k = 0
  l = nCandidates - 1
  ties = []
  while k < nCandidates:
      l = k+1
      lTie = [order[k]]
      while l < nCandidates and abs(distance[order[k]]-distance[order[l]]) < threshold:
          lTie += [order[l]]
          l+=1
      lTie.sort()
      ties.append(lTie)
      k=l
  return ties

def updateDepth(inputList, table, idx):
    i = 0
    toggle = 1
    for j in inputList:
        if len(j) > 1:
            depth = 2
        else:
            depth = 1
        for k in j:
#            if k != table[idx,i,0]:
#                print('mismatch?', k, table[idx,i,0])
            table[idx,i,1] = depth
            table[idx,i,2] = toggle
            i+=1
        toggle+=1

# ----
# allWinners = set() -- check note that it needs to be reset, so ...
# offSet is index offset
# aW set of all winners. it is modified by the function to be used over
# l is list of values.
# approach chosen because it is used in a list comprehension.
def maxes( l, aW, offset ):
    max = 0
    res = []
    for i, v in enumerate(l):
      if v > max:
        max =  v
        res = [i+offset]
      elif v == max:
        res.append(i+offset)
    aW |= set(res)
    return  ','.join([ str(i) for i in res])


# we are generating a number of random cases based on the value of "repeats"

if not xtractMode:
    print(' ; '.join(LabelsStr))
# print(";Borda; L0; Lp2; Lr2; Lp3; Lr3; I0; Ip2; Ir2; Ip3; Ir3; H2p1; H2p2; H2r2; H3p1; H3p3; H3r3; allW; Ccet; NCcet; NCinAW; BDt; NotBDted; BDted")
# print( ",nTO1/tail0/tiesAvg/Top,,nTO1/tail0/tiesAvg/Bottom,,1OVERn/tail0/tiesAvg/Top,,1OVERn/tail0/tiesAvg/Bottom,,AP/tail0/tiesAvg/Top,,GP(old)/tail0/tiesAVG/Top,,Condorcet")

idx = 0
totalVotes = nVoters

for v in vVector :
    # enumeration for all cases.
    idx +=1
    if eType == 'IC' or modelType == 's': # again, this should not be necessary.
        ballotDistribution = np.ones( ballotTypes, dtype=np.int32)
        for i in range (ballotTypes):
            addtorecord( ballots, orders[v[i]], i )
    elif eType == 'IAC':
        ballotDistribution = np.fromiter( v, np.int32)
        for i in range (ballotTypes):
            addtorecord( ballots, orders[i], i )

#    nResults = 6 # (number of cases processed.)
#    resultTable = np.zeros( (pattern[2], nResults), dtype=np.int32)
#    resultTally = np.zeros( ( nResults, nCandidates+1 ), dtype=np.int32)

    if  verbose:
        bd = [ballotDistribution[i] for i in range(ballotTypes)]
        print("ballot types", bd, sum(bd))
        print(ballots[ [i for i in range(ballotTypes)],:,:])

    voteTable = np.zeros( (nCandidates, nCandidates), dtype='int16' ) # 1 is candidates, 2 is rounds
    for i in range (nCandidates): # i is round
        for j in range (ballotTypes): # j is ballot
            voteTable[ ballots[j,i,0], i] += ballotDistribution[j]
    if verbose:
        print(voteTable)

    voteTally = np.zeros( (nCandidates, nCandidates), dtype='int16' ) # 1 is candidates, 2 is rounds - remember!!!
    for i in range(nCandidates):
        voteTally[i,0] = voteTable[i,0]
    for i in range(1, nCandidates):
            for j in range (nCandidates):
                voteTally[j,i] = voteTable[j,i] + voteTally[j,i-1]

    if 1 in selectionSet:
        SelectL = True
        SelectI = True
        SelectH = False
        results = [ vote(ballotScores1, tailScores0, tiesAVG, 0) ]
        results += [vote(bsL0, tailScores0, tiesAVG, 0) ] if SelectL else [[ -1 ]]
        results += [vote(bsLp2, tailScores0, tiesAVG, 0) ] if SelectL else [[ -1 ]]
        results += [vote(bsLr2, tailScores0, tiesAVG, 0) ] if SelectL else [[ -1 ]]
        results += [vote(bsLp3, tailScores0, tiesAVG, 0) ] if SelectL else [[ -1 ]]
        results += [vote(bsLr3, tailScores0, tiesAVG, 0) ] if SelectL else [[ -1 ]]
        results += [vote(bsInv0, tailScores0, tiesAVG, 0) ] if SelectI else [[ -1 ]]
        results += [vote(bsInvp2, tailScores0, tiesAVG, 0) ] if SelectI else [[ -1 ]]
        results += [vote(bsInvr2, tailScores0, tiesAVG, 0) ] if SelectI else [[ -1 ]]
        results += [vote(bsInvp3, tailScores0, tiesAVG, 0) ] if SelectI else [[ -1 ]]
        results += [vote(bsInvr3, tailScores0, tiesAVG, 0) ] if SelectI else [[ -1 ]]
#
        results += [vote(bsC, tailScores0, tiesAVG, 0) ]
#        results += [vote(bsH2p1, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        results += [vote(bsH2p2, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        results += [vote(bsH2r2, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        results += [vote(bsH3p1, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        results += [vote(bsH3p3, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        results += [vote(bsH3r3, tailScores0, tiesAVG, 0) ] if SelectH else [[ -1 ]]
        #    winners = [ i.index(max(i))+firstIdx for i in results]
        allWinners = set() # important reset - note that it is modified by maxes!
        winners = [ maxes(i, allWinners, firstIdx) if i != [] else -1 for i in results ]
        winners.append(allWinners)
    else:
        winners = ['-' for i in range(len(Labels1))]
    assert len(winners) == len(Labels1), 'Failed'+str(results)+'\n'+str(winners)

    if 2 in selectionSet: # ["Ccet", 'NCcet', 'FC', 'TCi', 'TCe']
        if truncLevel == nCandidates:
            PT = buildPrecedenceTable( True, False) # full condorcet
#        PTft = buildPrecedenceTable( False, True)
        else:
            PT = buildPrecedenceTable( False, False) # truncated condorcet
        # TCa = checkCondorcet()
        # winners.append(TCa+firstIdx)
        CC = computeCondorcet ( PT )
        CV = computeCopeland(PT)
        # print( PT, CC, CV)
        if xtractMode and (idx-1) in xtractList:
            print(idx-1, CC, PT)
        # assert TCa == TCb, "condorcet mismatch" + str(TCa) + '-' + str(TCb)
        if truncLevel == nCandidates:
            winners.append(CC+firstIdx)
            winners.append('-')
        else:
            winners.append('-')
            winners.append(CC+firstIdx)

        if False:
            winners.append( checkCondorcet() )
        else:
            winners.append(CV)
        # winners.append('-') # no longer computing condorcet under CheckCondorcet
        # winners.append(FC+firstIdx)
        DtedSet = whoDominates( CC ) if CC != -1 else []
        winners.append(DtedSet)
        DsSet = whoIsDominatedBy( CC ) if CC != -1 else []
        winners.append(DsSet)

#        if DtedSet != []:
#                print (PT, voteTable, voteTally)
    else:
        winners += ['-' for i in range(len(Labels2))]
    assert len(winners) == len(Labels1) + len(Labels2)

    if 3 in selectionSet:
        bd,nbd,bdted = computeDominance()
        winners.append(bd) #22
        winners.append(nbd) #23
        winners.append(bdted) #24
        winners.append(computeDominants() if True else '-') # 25
        winners.append(computeDominated() if True else '-') #26
        winners.append(False) #27 # isDominated(TC) if TC != -1 else False
        winners.append(dominates(1,2) if True else '-') # 28
    else:
        winners += ['-' for i in range(len(Labels3))]
    assert len(winners) == len(Labels1) + len(Labels2)  + len(Labels3)

    outLine = "# "+str(idx)+';' + '; '.join([ str(i) for i in winners])

    if not xtractMode:
        print(outLine)

    votesLength = np.zeros(nCandidates, dtype=np.int32)
    ballots = np.zeros( (ballotTypes, nCandidates, 3), dtype=np.int32)    # next a count of the number of votes for that ballot type
    ballotDistribution = np.zeros( ballotTypes, dtype=np.int32)
#    ballotTruncation = np.full( ballotTypes, truncLevel)



    # print (', ' + ', '.join([ "%.2f"%(i) for i in r0]) + ", votes (winner/maximum) ", max(r0), "/", nCandidates * totalVotes, ", for candidate:", r0.index(max(r0))+firstIdx )
#    r1 = vote(ballotScores1, tailScores0, tiesAVG, 1) # nTO1/tail0/tiesAvg/Bottom
    # print (', ' + ', '.join([ "%.2f"%(i) for i in r0]) + ", votes (winner/maximum) ", max(r0), "/", nCandidates * totalVotes, ", for candidate:", r0.index(max(r0))+firstIdx )
#    r2 = vote(ballotScores3, tailScores0, tiesAVG, 0) # 1OVERn/tail0/tiesAvg/Top
    # print (', ' + ', '.join([ "%.2f"%(i) for i in r0]) + ", votes (winner/maximum) ",  "%.2f"%(max(r0)), "/",  totalVotes, ", for candidate:", r0.index(max(r0))+firstIdx )
#    r3 = vote(ballotScores3, tailScores0, tiesAVG, 1) # 1OVERn/tail0/tiesAvg/Bottom
    # print (', ' + ', '.join([ "%.2f"%(i) for i in r0]) + ", votes (winner/maximum) ", "%.2f"%(max(r0)), "/", totalVotes, ", for candidate:", r0.index(max(r0))+firstIdx )
#    r3 = vote(ballotScoresAP, tailScores0, tiesAVG, 0) # AP/tail0/tiesAvg/Top
#    r4 = vote(ballotScoresAP, tailScores0, ties1, 0) # AP/tail0/tiesAvg/Top
    # print (', ' + ', '.join([ "%.2f"%(i) for i in r0]) + ", votes (winner/maximum) ", max(r0), "/", totalVotes, ", for candidate:", r0.index(max(r0))+firstIdx )
#    r5 = vote(bsFromGP0, tailScores0, tiesAVG, 0) # AP/tail0/tiesAvg/Top
