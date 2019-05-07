import numpy as np
import sys
# import argparse
import random
import json

# parameters - revised between executions are required.
voters = 200
candidates = 4
repeat = 1000
outData = [] # interesting cases, saved in a file for future reference or revisiting.


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

inputData = open('pairs.txt')
# reads as index case
for line in inputData:
    fields = line.strip().split()
    offset = int(fields[0])
    case   = int(fields[1])


    overall = [ {'1': 0, '2': 0, '3': 0, '4': 0},
       {'12': 0,'13': 0, '14': 0, '21': 0, '23': 0, '24': 0, '31': 0, '32': 0,'34': 0, '41': 0, '42': 0,'43': 0},
       {'123': 0, '124': 0, '132': 0, '134': 0, '142': 0, '143': 0, '213': 0, '214': 0, '231': 0, '234': 0, '241': 0, '243': 0, '312': 0, '314': 0, '321': 0, '324': 0, '341': 0, '342': 0, '412': 0, '413': 0, '421': 0, '423': 0, '431': 0, '432': 0},
       {'1234': 0, '1243': 0, '1324': 0, '1342': 0, '1423': 0, '1432': 0, '2134': 0, '2143': 0, '2314': 0, '2341': 0, '2413': 0, '2431': 0, '3124': 0, '3142': 0, '3214': 0, '3241': 0, '3412': 0, '3421': 0, '4123': 0, '4132': 0, '4213': 0, '4231': 0, '4312': 0, '4321': 0}
       ]
    # voteTally = np.zeros( (candidates, voters), dtype='int16' )
    for idx in range(candidates):
        voteTally = np.array(rawdata[offset])
        ol = overall[idx]
        for v in range(voters):
            l = ""
            for c in range(idx+1):
                i = voteTally[c, v]
                l += str(i+1)

            print ("key:", l)
            ol[l] += 1

    print ("case", offset)
    fh = open("_tally_xtd"+str(case)+".txt", 'w')
    for idx in range(candidates):
        fh.write("\nTruncate to " + str(idx+1)+ "\n")
        for key, val in overall[idx].items():
          fh.write(key+ "/"+  str(val) + "\n")
    fh.close()


inputData.close()
