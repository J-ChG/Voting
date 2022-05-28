# processing of elections for comparison with a Buclin model
# we can handle different forms of elections for the sake of comparison.

import sys
import math
import numpy as np
import random
import json
import support
import regions

# Managing options:

myargs, lastArg = support.getopts(sys.argv)
inFile = lastArg

if "-o" in myargs: # offset for first element
    offset = int(myargs['-o'])
else:
    offset = 0

if "-c" in myargs: # number of elements to process
    count = int(myargs['-c'])
else:
    count = 0

# break down of elections to test to have a progress report.
if "-p" in myargs: # number of progress items. To follow progress for a long run.
    loopTrack = = int(myargs['-p'])
else:
    loopTrack = 100000 # large enough to make a difference.

# parameter for specific region to analyze.
if '-r' in myargs: # specific region, to pass as parameter to generation.
    args = myargs['-r']
else:
    args = ''
    print("no r")
    print(sys.argv)

# this allows to explore a region in different ways:
# 'Base', 'Pyramid', 'Cubic', 'Points'
if "-t" in myargs:
    type = myargs['-t']
    assert type in regions.Variations, "unknown type "+type
else:
    type = 'Pyramid'
    print("Exploration type defaulted to " + type)

# truncation - self explanatory.
if "-T" in myargs:
    truncLevel = int(myargs['-T'])
else:
    truncLevel = None

# Not used much, but ready in case.
verbose = True if "-V" in myargs else  False
displayProfiles = True if "-w" in myargs else False

#  reflects different ways to generate the source points
# 1 is functions
# 2 is small rectangular patches
# 3 is large triangular zone
# 4 is specific scorers.

# open a model file.
with open(inFile, 'r') as f:
    (c , v, m, eType, orders, vVector) = json.load(f)
    nCandidates = c
    nVoters = v
    nCases = len(vVector)
    count = nCases if count == 0 else min(count, nCases-offset)
    modelType = m
    truncLevel = nCandidates-1 if truncLevel == None else truncLevel
    assert nCases*nCandidates*nVoters != 0, "need minimally all of -c #candidates -v #voters -r #repetitions to be present"
    assert eType == 'IC' or eType == 'IAC', "unknown type of vote (neither IC nor IAC)"
    assert modelType == 'r' or modelType == 's' , "unknown type of vote (neither r nor s)" # random or spatial.
f.close()


# Creation of data structures for models. They all share common structure because the are derived from the same
# kind of model.

# ballotTypes = constant
# ballotDistribution = table( ballotTypes )  = number of votes of a specific ballot type = 1 unless we are doing IAC
# For IAC, ballots are implicit, since they match order.
# ballots: ballotypes x ncandidates  - copy of ballots.
# ballotTruncation - table( ballotTypes )


# establish all possible orders.
# note that the "spatial model " also advertises itself as IC, so this distinctions
# should not be necessary.
# introduce mType to get rid of the eType+model distinction. Only 3 possibilities: IAC, IC or s (spatial)

if modelType == 'r': # random.
    mType = eType
    maxOrders = math.factorial(nCandidates)
    assert maxOrders == len(orders), 'mismatch in random model.'
    ballotTypes = nVoters if eType == 'IC' else maxOrders # for IAC
    ballotDistribution = np.ones( ballotTypes, dtype=np.int32) if eType == 'IC' else np.zeros(maxOrders, dtype=np.int32)
    # treat IAC differently because it will be initialized for every IAC election
else: # spatial
    mType = 's'
    maxOrders = len(orders)
    ballotTypes = nVoters
    ballotDistribution = np.ones( ballotTypes, dtype=np.int32)

# ballots collects the ballot order for all voters
ballots = np.zeros( (ballotTypes, nCandidates), dtype=np.int32)
#
# XXX
# note that ballotTruncation is not used uniformly. Sometimes we use it, sometimes we use truncLevel.
# is there because of the use of legacy code in precedence.
# at the same time, if randomness needs to be added, there is a possibility.
ballotTruncation = np.full( ballotTypes, truncLevel)
print("truncation initialization at", truncLevel)


# we generate alternatives for weights (weighted bucklin)
# types of region are: 'Base', 'Pyramid', 'Cubic', 'Points'
# this is in module regions.
# nAlternatives is the count
# voteweights is the weights array
# functions if the printing function for the different weights.
# note that, if we are computing "points", it implies that we have computed best cases,
# and thus we are also looking at the best score vectors for Borda model
# possibly using the region defined in argument.
nAlternatives, voteWeights, functions = regions.generate(nCandidates, mType, type, True if type=="Points" else False, args)

# computation of indexes. This must be done after generation to set extraV correctly.
# we have two regions: 0 to nAlternatives is explored in (weighted) Bucklin way
# whereas nAlternatives to nAlternative + ExtraV are explore in the (weighted) Borda way.
# some regions are hardcoded into comparison in the Borda models. We bring them out clearly.
iBidx = regions.iBLidx + nAlternatives # implicit normalized Borda
cNidx = regions.cVidx + nAlternatives  # Cervone
eBidx = regions.eBLidx + nAlternatives # explicit normalized Borda
freeNidx = regions.freeNidx + nAlternatives
extraV = regions.extraV
lastIdx = nAlternatives + extraV - 1 # or just  -1 if used as index rather than count.

print("Computing", count, 'elections over', nAlternatives+extraV, "points in form", type, "@truncation", truncLevel )

if displayProfiles:
    print("Weight profiles")
    for i in range(nAlternatives+extraV):
        print( functions[i][0], voteWeights[i])

nRounds = nCandidates # to avoid confusion in code, create a distinct variable.

# structures used to hold the best and worst results.
maxTopVals = 10
topVals = [(0.0, []) for i in range(maxTopVals)]

def resettopVals():
    global topVals
    topVals = [(0.0, []) for i in range(maxTopVals)]

def topN(ix, val):
    global topVals
    for i in range(maxTopVals):
        if val > topVals[i][0]:
            for j in range(maxTopVals-1, i, -1):
                topVals[j] = topVals[j-1]
            topVals[i] = (val, [ix])
            break
        elif val == topVals[i][0]:
            topVals[i][1].append(ix)
            break

botVals = [(100.0,[]) for i in range(maxTopVals)]
def botN(ix, val):
    global botVals
    for i in range(maxTopVals):
        if val < botVals[i][0]:
            for j in range(maxTopVals-1, i, -1):
                botVals[j] = botVals[j-1]
            botVals[i] = (val, [ix])
            break
        elif val == botVals[i][0]:
            botVals[i][1].append(ix)
            break

#    ====
# the computation of Condorcet requires a precedence table (PT).
# that is, a NxN matrix (N is the number of candidates) where
# PT(i,j) is the number of times i is prefered over j

# execution of the precedence relations
# Full controls whether the level of truncation applies of not
# skipOver controls what we do with candidates not on the ballot (or truncated)
#   True means that they are not counted.

#-- For Condorcet
# a precedence table is the basic tool to compute Condorcet winner and loser
# we isolate its construction
# we have 2 parameters to control
# 1) if ballot trunction is taken into account. False means we use ballot truncation.
# 2) how we process candidates not on ballots. False means we do.
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
                c = ballots[i,j]
                j+=1
                # in all cases j points to the first location beyond the tie group.
                # then establish precedence of the members of the group over the rest of the ballot
                for k in range(j, theLimit):
                    precedences[c,  ballots[i,k]] += 1
                candidatesDone[c] = True
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

# compute Condorcet winner
def computeCondorcetWinner(PT): # PT == precedence table, built from buildPrecedenceTable
    TC = 0 # tentative Condorcet
    for i in range(nCandidates):
        TC = i
        for j in range(nCandidates):
            if (PT[i,j] <= PT[j,i]) and (j!=i):
                TC = nCandidates
        if TC != nCandidates:
            break
    return TC if TC != nCandidates else -1

# compute Condorcet winner
def computeCondorcetLoser(PT):
    NC = 0
    for i in range(nCandidates):
        NC = i
        for j in range(nCandidates):
            if j != i and PT[i,j] > PT[j,i]: # j dominated by i
                NC = nCandidates # fail
                break
        if NC != nCandidates: # succeeded
            break
    return NC if NC != nCandidates else -1

#    ===

def precedes(a,b): # used when we are doing comparisons on full or truncated ballots
    aAhead = 0
    bAhead = 0
    for i in range(ballotTypes):
        for j in range( ballotTruncation[i] ):
            if ballots[i,j] == a:
                aAhead += ballotDistribution[i]
                break
            elif ballots[i,j] == b:
                bAhead += ballotDistribution[i]
                break
#    assert aAhead + bAhead == nVoters, "mismatch in precedence count"
    return aAhead > bAhead


# The Copeland score exploits the PT but records results
# in a differential mode only.
# For each candidate, it indicates how often it is preferred to
# another
def computeCopeland(PT):
    results = [0 for i in range(nCandidates)]
    for i in range(nCandidates):
        for j in range(nCandidates):
            if (j!=i):
                results[i] += 1 if PT[i,j] > PT[j,i] else -1 if  PT[i,j] < PT[j,i] else 0
    return results

####

# procedure election for rounds and weights. - Bucklin
# - wT is the threshold.
# voteweights is a global reference, unchanged.
def thresholdWinner(i, voteTable, voteTally, wT):
    winners = [] # all winners
    sWinners = [] # vs. unique winner
    round = -1 # # of rounds to declare winner
    maxV = 0.0 # max # of votes
    mCnt = 0 # for ties

    for j in range(nCandidates):
        voteTally[i,0,j] = float(voteTable[0,j]) * voteWeights[i,0]
        if voteTally[i,0,j] > wT:
            winners.append(j)
            round = 0
            if voteTally[i,0,j] > maxV:
                maxV = voteTally[i,0,j]
                mCnt = 1
                sWinners = [ j ]
            elif voteTally[i,0,j] == maxV:
                mCnt += 1
                sWinners.append(j)
    if round == -1 : # no winner yet
        for j in range(1, min(nRounds, truncLevel)):  # rounds ... but truncation?
            for k in range (nCandidates): # candidates
                voteTally[i,j, k] = float(voteTable[j,k])*voteWeights[i,j] + voteTally[i,j-1, k]
                if voteTally[i,j, k] > wT:
                    winners.append(k)
                    round = j
                    if voteTally[i,j, k] > maxV:
                        maxV = voteTally[i,j, k]
                        mCnt = 1
                        sWinners = [ k ]
                    elif voteTally[i,j, k] == maxV:
                        mCnt += 1
                        sWinners.append(k)
            if round != -1: break
    return (round!=-1, sWinners, winners )

# election procedure for plurality model - the highest scores win after all rounds. - Borda
# # voteweights is a global reference, unchanged.
def pluralityWinners(i, voteTable, voteTally):
    sWinners = [] # top winners
    maxV = 0.0 # max # of votes
    mCnt = 0 # for ties
    lRounds = min(nRounds, truncLevel) # limits to handle truncation

    for j in range(nCandidates):
        voteTally[i,0,j] = float(voteTable[0,j]) * voteWeights[i,0]
    for j in range(1, lRounds):  # rounds
        for k in range (nCandidates): # candidates
            voteTally[i,j, k] = float(voteTable[j,k])*voteWeights[i,j] + voteTally[i,j-1, k]
    for k in range(nCandidates):
        if voteTally[i, lRounds-1, k] > maxV:
            maxV = voteTally[i, lRounds-1, k]
            mCnt = 1
            sWinners = [ k ]
        elif voteTally[i, lRounds-1, k] == maxV:
            mCnt += 1
            sWinners.append(k)
    return (sWinners)

# variables to hold results. the names are meant to be self explanatory.
#
# vRound = np.zeros( (nAlternatives, nRounds+1), dtype='int16' ) #
#nWinners = np.zeros( (nAlternatives, nCandidates+1), dtype='int16' ) #
#
# Needs a cleanup to see what is really (purposefully) used.
#
tiesMatch = np.zeros( (nAlternatives+extraV, nCandidates+1), dtype='int32' ) #
CWmatches = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
CWmismatches = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
CLmatches = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
CLmismatches = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
simultaneousCWCL = 0
# sWinTies = np.zeros( (nAlternatives), dtype='int16' ) #
CWandNoBW = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
CLandNoBW = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
neitherW = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
BWandNoCW = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
BWandNoCL = np.zeros( (nAlternatives+extraV), dtype='int32' ) #
#
matches = np.zeros( (nAlternatives+extraV, 5), dtype='int32' ) #
CopelandScoresCW = np.zeros( (nAlternatives+extraV, nCandidates), dtype='int32' )
CopelandScoresNoCW = np.zeros( (nAlternatives+extraV, nCandidates), dtype='int32' )
CopelandDefCW = np.zeros( (nAlternatives+extraV, nCandidates), dtype='int32' )
CopelandDefNoCW = np.zeros( (nAlternatives+extraV, nCandidates), dtype='int32' )
noWinners = np.zeros( (nAlternatives+extraV), dtype='int32' )

# XXX debugging
#
BordasMismatch = 0
SubsetMismatch = 0
CWexistMismatch = 0
IntersectMismatch = 0
IntersectMatch = 0
noWinnerE = 0
noWinnerI = 0
overlaps = 0
Imatch = 0
Ematch = 0
IEmatch = 0

#
idx = 0
# totalVotes = nVoters
noCW = 0
noCL = 0
isCW = 0
isCL = 0

# set an odd size minimally equal to nCandidates
trx = nCandidates + 1 if nCandidates % 2 == 0 else nCandidates

# conversion table used for the Copeland deficit value.
ctoiTable = [0 for i in range(trx)]
for i in range(-nCandidates+1,nCandidates,2):
    ctoiTable[i] = -(i-nCandidates-1)//2 -1

# equivalent of preceeding, but as function.
def ctoi(v): # v - PT[i]
    return -(v-nCandidates-1)//2 -1

# dual operation of preceeding
def itoc(i):
    return nC+1 - (1+i)*2  # return 2*(i-1)

# main loop. over all elections, or subset chosen.
for xx in range( offset,offset+count ) :
    v = vVector[xx]
    #reset
    ballots = np.zeros( (ballotTypes, nCandidates), dtype=np.int32)    # next a count of the number of votes for that ballot type

# we do things in two different ways, which need distinct initialization.
# in one case, we point to the type of ballot, for each vote
# in the other case we have number of instances, for each type of ballot.
# ballots is initialize accordingly, and from there on the process is uniform.

    if eType == 'IC' or eType == 's': # structure of models defer between IC/s and IAC
        for i in range (ballotTypes):
            for j in range(nCandidates):
                ballots[i][j] = orders[v[i]][j]
    elif eType == 'IAC':
        # used later, so at least initialize it.
        ballotDistribution = np.fromiter( v, np.int32) #  when we need to initialize from a list of # of votes per type of ballot.
        for i in range (ballotTypes):
            for j in range(nCandidates):
                ballots[i][j] = orders[i][j]

    PT = buildPrecedenceTable(True, False) # for full condorcet
    if verbose:
        print("\nPrecedence table: \n", PT)

    CW = computeCondorcetWinner(PT)

    if CW == -1: # keep track of number of winners.
        noCW += 1
    else:
        isCW +=1
    CL = computeCondorcetLoser(PT)
    if CL == -1: # and losers.
        noCL += 1
    else:
        isCL += 1
    if CW != -1 and CL!= -1:
        simultaneousCWCL+=1

    Copeland = computeCopeland(PT)

    voteTable = np.zeros( (nRounds, nCandidates), dtype='int32' ) # 1 is rounds, 2 is candidates

    for i in range (nRounds):
        for j in range (ballotTypes): # j is ballot
            voteTable[ i, ballots[j,i]] += ballotDistribution[j]

        if verbose:
            print("\nVote table: \n", voteTable)

        # hold results.
        voteTally = np.zeros( (nAlternatives+extraV, nRounds, nCandidates), dtype='float' )
        #1 alternatives in weights
        #2 ranks
        #3 candidate

    # vote threshold. Note the underlying assumption that weights are normalized:
        wT = nVoters//2
    #       now do processing for all alternative+extra weights.
    #
        allWinners = []
        for i in range(nAlternatives):
            # was there a winner, who is the top winner, were there several winners.
            (foundIt, topW, allW) = thresholdWinner(i, voteTable, voteTally, wT)
            allWinners.append(topW)
            if foundIt :
                if CW != -1 :
                    tiesMatch[i, len(topW) ] += 1
                    if CW in topW:
                        CWmatches[i] += 1
                    else:
                        CWmismatches[i] +=1
                else: # BEW winner but no CW winner
                    BWandNoCW[i] += 1
                if CL != -1 :
                    if CL in topW:
                        CLmatches[i] += 1
                    else:
                        CLmismatches[i] +=1
                else: # BEW winner but no CW winner
                    BWandNoCL[i] += 1

    #            if CW not in sWinners and sWinners != []:
    #                print("CW no match -", CW, sWinners)

                if CW == -1:
                    # max(Copeland)
                    CopelandDefNoCW[i, (nCandidates-1 - Copeland[ allWinners[i][0] ])//2 ]+=1
                else:
                    CopelandDefCW[i, (nCandidates-1 - Copeland[ allWinners[i][0] ])//2 ]+=1
    #
    #            CSCW[i, (max(Copeland) - Copeland[ allWinners[i][0] ])//2 ]+=1
            else: # no winners
                noWinners[i] += 1
                if CW != -1 :
                    CWandNoBW[i] += 1
                else:
                    neitherW[i] += 1

        for i in range(nAlternatives, nAlternatives+extraV):
            topW = pluralityWinners(i, voteTable, voteTally)
            # note that there is always a winner
            allWinners.append(topW)

            if CW != -1:
                tiesMatch[i, len(topW) ] += 1
                CopelandDefCW[i, (nCandidates-1 - Copeland[ allWinners[i][0] ])//2 ]+=1
                if CW in topW:
                    CWmatches[i] += 1
                else:
                    CWmismatches[i] +=1
            else:
                CopelandDefNoCW[i, (nCandidates-1 - Copeland[ allWinners[i][0] ])//2 ]+=1


    # order for elements of "matches" - completely ad hoc.
    #0 - no CW
    #1 - CW matches B winner and Cervone
    #2 - CW matches B winner but not cervone
    #3 - CW matches Cervone only
    #4 - CW matches neither
        for i in range(nAlternatives+extraV):
            if CW == -1:
                matches[i,0] += 1
                if allWinners[i]:
                    CopelandScoresNoCW[i, ctoiTable[( Copeland[ allWinners[i][0] ] )]  ]+=1
            elif allWinners[i]:  # matching with several forms of winners.
                try:
                    CopelandScoresCW[i, ctoiTable[( Copeland[ allWinners[i][0] ])]  ]+=1
                except IndexError:
                    print ("index problem", i, len(allWinners), allWinners[0], Copeland, CopelandScoresCW.shape, extraV, nAlternatives)
                if CW in allWinners[i] and CW in allWinners[cNidx]:
                    matches[i,1] += 1
                elif CW in allWinners[i]:
                    matches[i,2] += 1
                elif CW in allWinners[cNidx]:
                    matches[i,3] += 1
                else:
                    matches[i,4] += 1

        if allWinners[iBidx] != allWinners[eBidx] and CW != -1 :  # XXX troubleshooting code - comparing Bordas
            if len( allWinners[iBidx]  ) == 1 and allWinners[iBidx][0] in allWinners[eBidx]:
                SubsetMismatch+=1
            elif len( allWinners[iBidx]  ) == 1 and len( allWinners[iBidx]  ) == 1 and allWinners[iBidx][0] != allWinners[eBidx][0]:
                BordasMismatch+=1
            else: CWexistMismatch += 1
            if not (set(allWinners[iBidx] ) & set( allWinners[eBidx] )): #intersection is empty, in general.
                IntersectMismatch+=1
        if CW != -1:
            if (set(allWinners[iBidx] ) & set( allWinners[eBidx] )):
                IntersectMatch += 1
            if allWinners[eBidx] == []:
                noWinnerE += 1
            if allWinners[iBidx] == []:
                noWinnerI += 1
    idx +=1
    if idx % loopTrack == 0:
        print ( (idx%loopTrack)+1, "pass done, counted", idx, ",", isCW, "CW")

# ad hoc way to taylor the output to cut it down while keeping options open. To clean up in the future
# but in the meantime it shows possibilities.

Sparse = True

if not Sparse:
    print("CW present/absent", isCW, noCW)
    print("CL present/absent", isCL, noCL)

# find the best results
for xi in range(nAlternatives):
    # print(xi,  CWmatches[xi], isCW)
    topN(xi, CWmatches[xi]/isCW)
maxIter = min(5, maxTopVals)

if not Sparse:
    print(f'\nCondorcet efficiency, top {min(maxIter,nAlternatives):2d} only:\n      Case  , isCW, CW matches Bucklin')

iter = 0
for xj in range(maxTopVals):
    for xi in topVals[xj][1]:
        if iter == maxIter:
            break
        else: iter+=1
#            print(  functions[xi][0], ',',   CCexists[xi], ',  ', CCmatches[xi], ',   ', CCmismatches[xi], ',       ', CWandNoBW[xi], ',      ', BWandNoCW[xi], ',      ', neitherW[xi], ','f'{(100*CCmatches[xi]/CCexists[xi]):.5f}%, {(100*(CCmatches[xi]+neitherW[xi])/count):.5f}%' )
        if not Sparse:
            print(CWmatches[xi]/isCW, ';', functions[xi],
            '- CW exists/matches: ', isCW, '/', CWmatches[xi],
            '- CL exists/matches: ', isCL, '/', CLmatches[xi],
            ", simultaneous occurrences:", simultaneousCWCL )
if Sparse:
    CE = CWmatches[ topVals[0][1][0] ]/isCW
    Wts = functions[topVals[0][1][0]]

if not Sparse:
    print("\nCopeland analysis (top", maxIter,"cases.)")
    print("function, Coincidence cases, Copeland scores general, Copeland scores with CW", )

cM = matches.tolist()
iter = 0
for xk in range(min(maxTopVals,nAlternatives)):
    for xj in topVals[xk][1]:
        if iter > maxIter:
            break
        else:
            iter+=1
            CS1 = CopelandDefNoCW[xj].tolist()
            CS2 = CopelandDefCW[xj].tolist()
            ttl = sum(CS1)+sum(CS2)
            if not Sparse:
                print( functions[xj], ';', (CopelandDefNoCW[xj][1] + CopelandDefCW[xj][0])/ttl , '--', cM[xj])
                print('---- Deficit, no CW', CS1, '-WC-', CS2, '-- (', ttl, ")"  )
#                print('old', CopelandScores[xj].tolist(), CopelandScoresCW[xj].tolist(), CSCW[xj].tolist())
#                print('new - no CW', CopelandScoresNoCW[xj].tolist(), CopelandDefNoCW[xj].tolist(), '-WC-', CopelandScoresCW[xj].tolist(), CopelandDefCW[xj].tolist() )

topString = ""
outV = ""

# computation of performance results for Copeland Score.
# these follow from definition.
xj = topVals[0][1][0]
CS1 = CopelandDefNoCW[xj].tolist()
CS2 = CopelandDefCW[xj].tolist()
ttl = sum(CS1)+sum(CS2)
Pmax = (CopelandDefNoCW[xj][1] + CopelandDefCW[xj][0])/ttl if ttl!=0 else float("nan")
ED = 0
for i in range(nCandidates):
    ED += CopelandDefCW[xj][i]*2*i
for i in range(1,nCandidates-1):
    ED += CopelandDefNoCW[xj][i]* 2*(i-1)
ED = ED/ttl if ttl != 0 else float("nan")
tiesC = sum(tiesMatch[xj][2:])

# preparing a structured string for output, following a CSV format for easier later integration
# in a spreadsheet.
topString = ";Weights; CE; PMax; E[D]; Ties"
outV = ';{};{};{};{};{}'.format(Wts, CE, Pmax, ED, tiesC)

resettopVals()

# Look again for top values, but this time for specific points in weighted scores
# The question is the range we explore.
# there is an assumption.
# rewrite this cleanly ... XXX
for xi in range(freeNidx, extraV):
    topN(xi, CWmatches[xi]/isCW)

# we only compute full results when we are doing "points", that is, comparing
# the two forms of elections and adding cervone and borda for comparisons.
if type == "Points":
    iter = 0
    wi, wll = topVals[0]
    if wll != []:
        xj = topVals[0][1][0]
        CS1 = CopelandDefNoCW[xj].tolist()
        CS2 = CopelandDefCW[xj].tolist()
        ttl = sum(CS1)+sum(CS2)
        Pmax = (CopelandDefNoCW[xj][1] + CopelandDefCW[xj][0])/ttl
        CE = CWmatches[ xj ]/isCW
        ED = 0
        for i in range(nCandidates):
            ED += CopelandDefCW[xj][i]*2*i
        for i in range(1,nCandidates-1):
            ED += CopelandDefNoCW[xj][i]* 2*(i-1)
        ED = ED/ttl
        tiesC = sum(tiesMatch[xj][2:])
        outV += ';;{};{};{};{};{}'.format(Wts, CE, Pmax, ED, tiesC)
        topString+= ";;Score; CE; PMax; E[D]; Ties"

    CS1 = CopelandDefNoCW[iBidx].tolist()
    CS2 = CopelandDefCW[iBidx].tolist()
    ttl = sum(CS1)+sum(CS2)
    Pmax = (CopelandDefNoCW[iBidx][1] + CopelandDefCW[iBidx][0])/ttl
    CE = CWmatches[ iBidx ]/isCW
    tiesC = sum(tiesMatch[iBidx][2:])
#    print( "Borda (L); CE; PMax; E[D]; Ties")
#    print (  ";", CE, ";", Pmax, ";", ED, tiesC )
    outV += ';;;{};{};{};{}'.format(CE, Pmax, ED, tiesC)
    topString+= ";;Borda; CE; PMax; E[D]; Ties"

    CS1 = CopelandDefNoCW[cNidx].tolist()
    CS2 = CopelandDefCW[cNidx].tolist()
    ttl = sum(CS1)+sum(CS2)
    Pmax = (CopelandDefNoCW[cNidx][1] + CopelandDefCW[cNidx][0])/ttl
    CE = CWmatches[ cNidx ]/isCW
    tiesC = sum(tiesMatch[cNidx][2:])
#    print( "Cervone; CE; PMax; E[D]; Ties")
#    print (  ";", CE, ";", Pmax, ";", ED, tiesC )
    outV += ';;;{};{};{};{}'.format(CE, Pmax, ED, tiesC)
    topString+= ";;Cervone; CE; PMax; E[D]; Ties"

    if not regions.within(voteWeights[iBidx], voteWeights[freeNidx], voteWeights[-1]):
            print('Borda out of bounds', voteWeights[iBidx] )
    else:
            print("Borda within bounds")

print(topString)
print(outV)
