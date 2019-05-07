import numpy as np
import sys
# import argparse
import random
import json

# parameters - revised between executions are required.
voters = 200
candidates = 4
repeat = 100

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
            return ("Condorcet winner", idx)
        else:
            for i in range(candidates):
                if tentative[i] and not present[i]:
                    return ("No Condorcet winner")
            present = [ present[x] and tentative[x] for x in range(candidates)]
            idx = present.index(1)
#            print(idx, values, tentative, present)


with open('selected.json', 'r') as f:
     rawdata = json.load(f)
     f.close()

percentages = []
selections = []
inputData = open('points.txt')
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

# help to display.
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
for i in range(0,repeat):
    alternatives.append( random.sample(range(0, voters), voters))

# index to information to extract from the json file (rawdata)
inputData = open('pairs.txt')
# reads as index case
for line in inputData:
    fields = line.strip().split()
    offset = int(fields[0])
    case   = int(fields[1])

    # recover voting table from rawdata
    voteTally = np.array(rawdata[offset])
    print ("case", offset)
    fh = open("___case_"+str(case)+".txt", 'w')
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
    print(case, condorcet(0))

inputData.close()
