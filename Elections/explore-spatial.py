import numpy as np
import sys
# import argparse
import random
import json

# parameters - revised between executions are required.
voters = 601
candidates = 6
repetitions = 5000
detail = False # just high level statistics.
outData = [] # interesting cases, saved in a file for future reference or revisiting.

overall = {}
consolidate = {}
condorsetSet = {}
Cposition = [0 for x in range(candidates)]

# variety of support functions

# Conditionally increase a count
def condInc( dic, lab) :
  if lab in dic:
    dic[lab] = dic[lab] + 1
  else:
    dic[lab] = 1

# different functions to produce a string where the index of a candidate is replaced
# with a C, to mark the Condorcet candidate.
# of course they could be combined into one, but their main purpose it to clean
# up the code.
def translate1( choix ):
    explode = list(choix)
    implode = [ 'C' if x == '1' else x for x in explode]
    return ''.join(implode)

def translate2( choix, candidate ):
    explode = list(choix)
    implode = [ 'C' if x == str(candidate) else str(int(x)+1) if int(x) < candidate  else x for x in explode]
    return ''.join(implode)

def translate3( choix ):
    explode = list(choix)
    implode = [ str(int(x)+1) for x in explode]
    return ''.join(implode)

# F is first, O is other, N is none and - is null.
def addCondorset( field, kind ):
    if field not in condorsetSet:
        condorsetSet[field] = {'-':0, 'F':0, 'O':0, 'N':0}
    condorsetSet[field][kind] += 1

def populate(depth, maximum, current):
  if depth == candidates-1:
    overall[current] = 0
    return
  else:
    for i in range(1,maximum+2):
      populate(depth+1, max(i, maximum), current + str(i))
populate(1, 1, '1')

### help function for printing.
def subreveal(marks):
    st = ""
    for j in range(0, len(percentages)):
        for i in percentages[j]:
            st += str(i)
            st += " "
#        st += str(percentages[j])
        st += " +++ "
        for i in marks[j]:
            st += str(i)
            st += " "
        st +="\n"
    return(st)

# table to hold elections.
voteTally = np.zeros( (candidates, voters), dtype='int16, int16' )

# computes the Condorcet candidate. It is always present in the spatial model
def condorcet(idx = None):
    present = [1 for x in range(candidates)]
    if idx is None:
        idx = 0
    while idx != -1 :
        values = [0 for x in range(candidates)]
        for i in range(voters):
            for j in range(candidates):
                c, _ = voteTally[j,i]
                if c == idx:
                    break
                else:
                    if present[c]:
                        values[c]+=1
        tentative = [1 if values[x] > (voters/2) else 0 for x in range(candidates) ]
        if tentative.count(1) == 0:
            return idx
        else:
            for i in range(candidates):
                if tentative[i] and not present[i]:
                    return -1
            present = [ present[x] and tentative[x] for x in range(candidates)]
            idx = present.index(1)
#            print(idx, values, tentative, present)

# main loop. It is controlled by the number of repetitions requested.
for loopCount in range(repetitions):
    candidate_list = sorted(random.sample(range(0, voters), candidates))
#    candidate_list = [85, 215, 294, 323]
    allCandidates = np.array(candidate_list)

    for v in range(voters):
      for p in range(candidates):
        # compute distance
        if ( v < allCandidates[p]):
          d = allCandidates[p] -v -1
        else:
          d = v - allCandidates[p] +1
        # find place of insertion
        l = 0
        (_,x) = voteTally[l, v]
        while (d >= x) and (p>l) :  # votesIndex[v]>
          l += 1
          (_,x) = voteTally [l, v]
        t = p # candidate so far -1 -- reflects how deep is table is filled up.
        while (t > l):
          voteTally[t,v] = voteTally[t-1,v]
          t = t-1
        voteTally[l,v] = (p, d)

# 3 variables used to keep track of who has won to categorize profiles.
    winners = []
    allWinners = 0
    codeWinner = ''
    # we repeat an election with the same data but different levels of truncation.
    # trunc is the control variable in this case.
    for trunc in range(candidates-1,0,-1):
        # Next we create a table large enough for all the rounds of voting.
        # we need to tally for all candidates
        results = np.zeros( candidates, dtype=np.int16)
        # we must also keep trace of who is in the race. Better to keep them separate.
        active = np.ones( candidates, dtype=np.bool)
        # and where each voter is in her vote
        votesIndex = np.zeros( (voters), dtype='int16' )
        # votesTop is the last useable index. Adjusted by different factors.
        # votesTop = np.zeros( (voters), dtype='int16' )
        # votesTop.fill(trunc) # maximal value to consider.
        votesTop = np.full( (voters), trunc, dtype=np.int16)

        # first round of vote
        rounds = 1
        for v in range(voters):
          c, _ = voteTally[0, v]
          results[c]  += 1
        # everyone must have voted
        assert (results.sum() == voters)

        while (np.amax(results) < (voters//2+1)) and (rounds < candidates) :
            # we could do better here - initialize min with the first value and
            # use the computations for resetting it at the end of the loop.
            # mind you, there are not so many candidates, so this is not really an issue.
            min = results.argmax() # cannot use argmin since some values are blanked out
            for c in range(candidates):
                if (active[c] and (results[c] < results[min])):
                    min = c
            # eliminate the weakest link.
            active[min] = False
            results[min] = 0
            for v in range(voters):
                c,_ = voteTally[ votesIndex[v],v]
                if (c == min and votesIndex[v] < (votesTop[v])):
                    while (not active[c] and votesIndex[v] < (votesTop[v])):
                        votesIndex[v] += 1
                        c, _ = voteTally[ votesIndex[v],v ]
                    if (active[c]) and votesIndex[v]<(votesTop[v]):
        #                print ("new candidate:", c, ", changing index for voter", v)
                        results[c] += 1
        #                print ( "eliminated voter", v )
            rounds += 1
        # we have a winner and we have processed.
        newWinner = results.argmax()
        if (newWinner in winners):
            idx = winners.index(newWinner) + 1
            codeWinner += str(idx)
        else:
            allWinners +=1
            codeWinner += str(allWinners)
            winners.append(newWinner)
#        if (lastWinner!=newWinner):
#            if status == '12W' and newWinner in winners:
#                status = '121W'
#            else: # 0W-> 1W  12W ->123W
#                status = altChoices.get(status, 'error')
#        else:
#            status = straightChoices.get(status, 'error')
#        lastWinner = newWinner
#        winners.append(newWinner)
#    overall[status] = 1 + overall[status]
    condInc(overall, codeWinner)
    outW = ", "
    for i in range(candidates-1):
        if i < len(winners):
            outW += str(winners[i]) + ", "
    c =  condorcet(winners[0])
    if c == -1:
        Cstr = '-'
        otherWinner = codeWinner
    elif c == winners[0]:
        Cposition[0] += 1
        Cstr = 'F'
        otherWinner = translate1(codeWinner)
    elif winners.count(c) != 0:
        Cstr = 'O'
        otherWinner = translate2(codeWinner, winners.index(c)+1) # 2nd parameter is position of Condorcet.
        for i in range(1, len(winners)):
            if c == winners[i]:
                Cposition[i] += 1
    else:
        Cstr = 'N'
        otherWinner = translate3(codeWinner)
        Cposition[candidates-1] += 1
    condInc(consolidate, otherWinner)
    addCondorset(codeWinner, Cstr)
    print (allCandidates, ',', codeWinner, ', ', otherWinner, outW, 'C, ', c, ", ", Cstr  )

print(overall)
print(consolidate)

for i in consolidate:
    print (i, ',', consolidate[i], ',', end='')
print ('')
print (Cposition)


for i in [] : # condorsetSet
    print (i, end='')
    for j in condorsetSet[i]:
        k = condorsetSet[i][j]
        print (', ', j, ',', k, end='')
    print("")
