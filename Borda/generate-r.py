import random
import math
import json
import sys
import support
# import os.path
from os import path

# this programme generates elections according to an IC or IAC model
# the output is a json file containing a tuple with
# nCandidates, nVoters, type, results
# In the IC case, the outcome is a vector of size nVoters,
# in the IAC case, the outcome is a vector of size nCandidates!
# There are nCandidates! possible elections.


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
  print ("options are: -v # -c # -r # -t IC|IAC -p prefix ]")
  exit(0)

if "-v" in myargs:
    nVoters = int(myargs['-v'])
else:
    nVoters = 0
if "-c" in myargs:
    nCandidates = int(myargs['-c'])
else:
    nCandidates = 0

if "-t" in myargs:
  type = myargs['-t']
else:
  print("missing type")

if "-r" in myargs:
  repeats = int(myargs['-r'])
else:
  repeats = 1000

assert type == 'IC' or type == 'IAC', "wrong type"+type
assert nCandidates * nVoters != 0, "Wrong values for #candidates or #voters"

variants = 0
while True:
    countStr = (str(variants)).zfill(3)
    outFile  = str(nCandidates) + "-" + str(nVoters) + "-" + type + "-" + str(repeats) + "-r-" + countStr + '.json'
    if not path.exists(outFile):
        break
    else:
        variants += 1

results = []
size = math.factorial( nCandidates )
sizeSet = [i for i in range(size) ]

if type == 'IC':
  # in this case, we just randomply pick sime instance from the size choices nVoters time
  for _ in range(repeats):
    allVotes = random.choices( sizeSet, k=nVoters)
    results.append( allVotes)
elif type == 'IAC':
  # this is more tricky. We need to generate a size-long sequence of numbers such
  # that their sum = nVoters
  # the techniused here requires that we have more voters than
  # possible choices. So we make that a (reasonable) constraints
  population = [i for i in range(0, nVoters+1)]
  assert nVoters>=size, "# of voters ("+str(nVoters)+") should be greater than # of different ballots ("+str(size)+")"
  for _ in range(repeats):
    votes = random.choices( population,  k=size -1 )
    allVotes = [0] + votes + [nVoters]
    allVotes.sort()
    results.append( [ allVotes[i+1] - allVotes[i] for i in range(0, size) ])
else:
  print("won't happen")

with open(outFile, 'w') as f:
     json.dump(( nCandidates, nVoters, 'r', type, support.COrders(nCandidates), results), f)
