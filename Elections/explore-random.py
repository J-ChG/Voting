# explore elections based on random selection of order of candidates on ballot.
# this code looks at specific cases.

import numpy as np
import sys
# import argparse
import random
import json

# parameters - revised between executions are required.
voters = 601
candidates = 6
repeats = 100
repetitions = 5000
detail = False # just collect high level statistics.
outData = [] # interesting cases, saved in a file for future reference or revisiting.

overall = {}
consolidate = {}
condorsetSet = {}
Cposition = [0 for x in range(candidates)]

def condInc( dic, lab) :
  if lab in dic:
    dic[lab] = dic[lab] + 1
  else:
    dic[lab] = 1

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

# truncation cases analyzed. specific val;ues are given in terms of percentage
# for first, second, ... candidate)
percentages = []
selections = []
inputData = open('values.txt')
for line in inputData:
    fields = line.strip().split()
    percentages.append([int(fields[0]), int(fields[1])])
inputData.close()
# Transform the percentages into numbers.
for i in percentages:
    new = []
    for j in i:
        new.append(int(j*voters/100))
    selections.append(new)

### support function for printing.
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

# For the second part, we need random allocations of the numbers in selections
# We do this by creating a number of random permutations of the voters, which
# will be used as indexes into the real voters data.
alternatives = []
for i in range(0,repeats):
    alternatives.append( random.sample(range(0, voters), voters))

voteTally = np.zeros( (candidates, voters), dtype='int16' )
changed = 0

def condorcet(idx = None):
    present = [1 for x in range(candidates)]
    if idx is None:
        idx = 0
    while idx != -1 :
        values = [0 for x in range(candidates)]
        for i in range(voters):
            for j in range(candidates):
                c = voteTally[j,i]
                if c == idx:
                    break
                else:
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
    # generate election data, random case - we assign votes to voters
    for v in range(voters):
        r = random.sample(range(0, candidates), candidates)
        for p in range(candidates):
            voteTally[p,v] = r[p]

    winners = []
    allWinners = 0
    codeWinner = ''
    # levels of truncation.
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
          c = voteTally[0, v]
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
                c = voteTally[ votesIndex[v],v]
                if (c == min and votesIndex[v] < (votesTop[v])):
                    while (not active[c] and votesIndex[v] < (votesTop[v])):
                        votesIndex[v] += 1
                        c = voteTally[ votesIndex[v],v ]
                    if (active[c]) and votesIndex[v]<(votesTop[v]):
                        results[c] += 1
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
    condInc(overall, codeWinner)
#    print (winners, codeWinner)
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
    print ( ',', codeWinner, ', ', otherWinner, outW, 'C, ', c, ", ", Cstr  )

    if detail:
        print('MC case at iteration', status, loopCount, winners)
# proceed with randomc voting itself.
        fh = open("case_"+str(loopCount)+".txt", 'w')
        outData.append(voteTally.tolist())
        randoms = []
        for s in selections:
            mark = np.zeros( candidates, dtype=np.int16)
            for a in alternatives:
                # initialize
                results = np.zeros( candidates, dtype=np.int16)
                # we must also keep trace of who is in the race. Better to keep them separate.
                active = np.ones( candidates, dtype=np.bool)
                # and where each voter is in her vote
                votesIndex = np.zeros( (voters), dtype='int16' )
                # Top is the last useable index. Adjusted by different factors.
                idx = 0
                votesTop = np.zeros( (voters), dtype='int16' )
                for i in range (0, s[0]):
                    votesTop[a[idx]] = 1
                    idx += 1
                for i in range (0, s[1]):
                    votesTop[a[idx]] = 2
                    idx += 1
                for i in range (s[0]+s[1], voters):
                    votesTop[a[idx]] = 3
                    idx += 1
                # Process.
                rounds = 1
                for v in range(voters):
                  c = voteTally[0, v]
                  results[ c]  += 1
                # everyone must have voted
                assert (results.sum() == voters)
                # not sure we need to keep track of it. But why not.
                # note that it is used in the loop below.
                totalVoters = voters
                for v in votesTop:
                    assert( votesTop[v] != 0) # really?

                while (np.amax(results) < (totalVoters//2+1)) and (rounds < candidates) :
        #            print(totalVoters,"voters in this round")
                    min = results.argmax() # cannot use argmin since some values are blanked out
                    for c in range(candidates):
                        if (active[c] and (results[c] < results[min])):
                            min = c
                    active[min] = False
                    results[min] = 0
                    for v in range(voters):
                        c = voteTally[ votesIndex[v],v]
                        if (c == min and votesIndex[v] < (votesTop[v])):
                            while (not active[c] and votesIndex[v] < (votesTop[v])):
                                votesIndex[v] += 1
                                c = voteTally[ votesIndex[v],v ]
                            if (active[c]) and votesIndex[v]<(votesTop[v]):
                #                print ("new candidate:", c, ", changing index for voter", v)
                                results[c] += 1
                            else:
                                totalVoters -= 1
                    rounds += 1
                mark[results.argmax()] += 1
            randoms.append(mark)
        fh.write(subreveal(randoms))
        fh.close()

if detail:
    with open('selected.json', 'w') as f:
         json.dump(outData, f)
         f.close()

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
