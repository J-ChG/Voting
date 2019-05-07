import sys
import numpy as np
import re

# march 16th:
# removed the display of candidates eliminated while the winner was already known
# modified the display to produce "exhausted ballots"

# print(sys.argv)  # Note the first argument is always the script filename.

def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

myargs = getopts(sys.argv)


if not '-i' in myargs:  # Example usage.
    print ("Missing -i option for input")
    sys.exit()

fh = open (myargs['-i'], "r")
lin = fh.readline()
candidates = int(lin)
for i in range(candidates):
  fh.readline()
lin = fh.readline()
llin = lin.split(",")
# print (llin[0], llin[1], llin[2])

tV = int(llin[0])
ballotTypes = int(llin[2])
#
# check the length of ballots for distribution of truncation
votesLength = np.zeros(candidates, dtype=np.int32)
# 2 tables to hold the data. First ballot types
# this is 3 dimensional.
# 0 is candidate
# 1 is embedding level - 1 or 2 - for ties.
# 2 is a number to count the number of ties - to distinguish a sequence of two ties.
details = np.zeros( (ballotTypes, candidates, 3), dtype=np.int32)
# next a count of the number of votes for that ballot
detailc = np.zeros( ballotTypes, dtype=np.int32)
# truncation per ballot type
votesTop = np.zeros( ballotTypes, dtype=np.int32)
# to count the votes per rounds.
rounds = np.zeros( (candidates, candidates), dtype=np.int32)
# check the length of ballots for distribution of truncation
totalVotes = 0

tiesCount = (0,0)
tailTiesCount = (0,0)

# outer loop - for each different type of ballot. First element of line
# is the number of instances
for i in range( ballotTypes ) :

  lin = fh.readline()
  lins = lin.split(",")
  lineItem = 0
  depth = 1
  generation = 0
  isTie = False

  for j in lins[1:]:

    if j.find("{") != -1:
        isTie = True
        el = j.split('{')
        depth +=1
        details[i, lineItem,1] = depth
        generation +=1
        nV = int(el[1])
    elif j.find("}") != -1:
        el = j.split('}')
        nV = int(el[0])
        details[i, lineItem,1] = depth
        depth -=1
    else:
        details[i, lineItem,1] = depth
        nV = int(j)

    details[i, lineItem,0] = nV
    details[i, lineItem,2] = generation
    lineItem+=1

  if isTie:
      tiesCount = (1+tiesCount[0], int(lins[0])+tiesCount[1])
  if details[i, lineItem-1,1] > 1:
      tailTiesCount = (1 + tailTiesCount[0], int(lins[0])+tailTiesCount[1])

  totalVotes+=int(lins[0])
  detailc[i] = int(lins[0])
  votesTop[i] = lineItem # note it is one beyond, so votesTop can be used in range
  votesLength[ lineItem -1 ] += int(lins[0])

fh.close()

avgLength = 0
for i in range(candidates):
    avgLength += (i+1)*votesLength[i]
#    print( myargs['-i'], "//", candidates, "//", totalVotes, "(", tV, ")//", ballotTypes, "//", votesLength, "(avg -", int(100*avgLength/sum(votesLength))/100, ")")

print( myargs['-i'], "//", candidates, "//", totalVotes, "//", ballotTypes, "//", votesLength, "(avg -", int(100*avgLength/sum(votesLength))/100, ")")

if tiesCount != (0,0):
    print (tiesCount[1], "ballot with ties over", tiesCount[0], "ballot types;", tailTiesCount[1], "are trailing."  )

# may have to return next neighbour if not valid. or check externally?
# i is ballotType, j is round.
def neighbours(i,j):
    if details[i][j][1] == 1:
        return 0
    else:
        t = 0
        g = details[i][j][2]
        k = j-1
        while (k>0) and (details[i][k][1] == 2) and (g == details[i][k][2]):
            if active[ details[i][k][0] -1 ] :
                t += 1
            k -= 1
        k = j+1
        while (k < votesTop[i]) and (details[i][k][1] == 2) and (g == details[i][k][2]):
            if active[ details[i][k][0] -1 ] :
                t += 1
            k += 1

        return t

def stillLive(i,j):
    level = details[i][j][1]
    if level == 1:
        return active[ details[i][j][0] -1 ]
    else:
        group = details[i][j][2]
        k = j
        live = False
        while (k < votesTop[i]) and (details[i][k][1] == level) and (details[i][k][2] == group):
            live = live or active[ details[i][k][0] -1 ]
            k += 1


print ("\nElection:")
totalVoters = totalVotes
results = np.zeros( candidates, dtype=np.float)
# we must also keep trace of who is in the race. Better to keep them separate.
active = np.ones( candidates, dtype=np.bool)
# and where each voter is in her vote
votesIndex = np.zeros( ballotTypes, dtype='int16' )
# Top is the last useable index. Adjusted by different factors.
# end of initialization, now we proceed.
rounds = 1
for v in range(ballotTypes):
  # do not forget to convert from candidate to index
  c = details[v][0][0] -1
  n = neighbours(v,0)
  results[ c ]  += float(detailc[v]) / (1+n)

eliminated = 0
loosers = []
# we loop until there is a winner, or we run out of rounds.
while (np.amax(results) < (totalVoters//2+1)) and (rounds < candidates) :
    #  print(totalVoters,"voters in this round")
    # we must eliminate the candidate with the worst results.
    min = results.argmax() # cannot use argmin since some values are blanked out
    for c in range(candidates):
        if (active[c] and (results[c] < results[min])):
            min = c
#    results[min] = 0
# different measures - do sum(results)-eliminated or
# do tV - totalVoters.
    print ( [ str(results[x]) if active[x] == True else "--" for x in range(candidates)], tV-totalVoters, "exhausted ballots; eliminating candidate", min+1 ) # tV was sum(results)
#    assert ( sum(results)-eliminated == totalVoters )
    active[min] = False
    loosers.append(min)
    eliminated += results[min]

    for v in range(ballotTypes):
        c = details[v][votesIndex[v]][0] - 1
        if c == min and votesIndex[v] < votesTop[v] and not stillLive(v,votesIndex[v]):
            while (not active[c]) and votesIndex[v] < votesTop[v]:
                votesIndex[v] += 1
                c = details[v][votesIndex[v]][0] -1
            if active[c] and votesIndex[v] < votesTop[v]:
#                print ("new candidate:", c, ", changing index for voter", v)
                n = neighbours(v, votesIndex[v])
                results[c] += float(detailc[v]) / (1+n)
            else:
                totalVoters -= detailc[v]
    rounds += 1

# at this stage we have a winner.
print ( [ str(results[x]) if active[x] == True else "--" for x in range(candidates)], tV-totalVoters, "exhausted ballots." )
while (rounds <= candidates):
    min = results.argmax() # cannot use argmin since some values are blanked out
    for c in range(candidates):
        if (active[c] and (results[c] < results[min])):
            min = c
    if (rounds == candidates):
        print ("Candidate", min+1, "wins with", results[min] , "votes.")
#    else:
#        print ( [ str(results[x]) if active[x] == True else "XXXX" for x in range(candidates)], sum(results)-eliminated, "ballots, eliminating candidate", min+1 )
    eliminated += results[min]
    active[min] = False
    loosers.append(min)
    rounds += 1

results = [x+1 for x in loosers[::-1]]
print ("\nResults in decreasing ranking:",results)
# print ("Results in decreasing rank:", [x+1 for x in results.reverse()])

# if candidate one is on top, what is the distribution of candidate two for the other locations?
# we will return a list where position 0 holds the number of times two did not appear, and
# the others will be in their respective position.
def isPresent(one, two):
    # three possibilities: two is in the bottom, in the top, or absent.

    position  = np.zeros(candidates, dtype=np.int32)
    ranking = np.zeros(candidates, dtype=np.int32)
    first = 0

    for v in range(ballotTypes):
        vT = votesTop[v]
        Absent = True
        if details[v][0][0] == one:
            first += detailc[v]
            rank = 0
            gen = 0
            for i in range(1, vT):
                if (details[v][i][1]==1):
                    rank = i
                else:
                    if details[v][i][2] != gen:
                        rank = i
                        gen  += 1
                if details[v][i][0] == two:
                    position[i]   += detailc[v]
                    ranking[rank] += detailc[v]
                    Absent = False
                    break
            if Absent:
                position[0] += detailc[v]

    return (first, list(position), list(ranking))

tied = 0; tiedbt = 0; tied1st = 0; tied1stbt = 0; maxtie = 0
position  = np.zeros(candidates, dtype=np.int32)

if False:
    for v in range(ballotTypes):
        if details[v][0][1] == 2:
            tiedbt += 1
            tied += detailc[v]
            i = 0
            while  (details[v][i][1] == 2) and (details[v][i][2] == 1): # tie, 1st generation.
                if (i>maxtie):
                    maxtie = i
                if details[v][i][0] == results[0]: # apply to winner?
                        tied1stbt += 1
                        tied1st += detailc[v]
                        position[i] += detailc[v]
                i += 1
    print ("\nNumber of ties for first ballot:",tiedbt, "cases,", tied, "instances with", tied1st, "where winner (candidate",  results[0], ") is tied (", list(position[0:maxtie+1]),  ")." )

print("\nStudy of results of order of candidates in ballots.")
for i in ([ [0,1], [1,0], [0,2], [2,0], [0,3], [3,0] ]):
    fst = results[i[0]]
    snd = results[i[1]]
    (nbr, res, rks) = isPresent(fst, snd)
    assert (nbr == sum(res) )

    assert (nbr == sum(rks)+res[0] )

    print ("Cases where",fst, "is first (", nbr, "out of", tV, ")", snd, "is absent", res[0], "times, otherwise distributed as")
    print ("Per strict order:", res[1:])
    print ("Per rank (with ties):", rks[1:])
