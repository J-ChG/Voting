# definition of sets of weights to apply to elections.
# different methods can be used: generator functions,
# cubes, pyramids, fixed set of point, etc.
# the appropriate function is chosen as a parameter, extra data can also be
# given as range.

# Many design and use changes were made along the way.
# formulae were no longer used, for one, but the code is kept for reference.

import numpy as np
import math
import sys

# support for difference weighting generator formulae
linearF = lambda i, h: 1 - i/(h*nCandidates)
proportionalF = lambda i, h: h * (nCandidates-1-i)
harmonicF = lambda i, h:  1/((i+1)**h)
dualHarmonicF = lambda i: 1 - 1 /(nCandidates-i) + 1/(nCandidates)
squareF = lambda i,h : 1/(2 ** (i*h))
dualSquareF = lambda i: 1 - 1 / (2**(nCandidates-i)) + 1/2**(nCandidates)
classicalB = lambda i: nCandidates - i

def constant(i): return squareF(i,0)
def linA(i): return linearF(i, 1)
def linB(i): return linearF(i, 2)
def harmA(i): return harmonicF(i, 1)
def harmB(i): return harmonicF(i, 2)
def squareFa(i): return squareF(i,1)
def pFa(i): return proportionalF(i,0.4)
def pFb(i): return proportionalF(i,0.5)

baseFunctions = [
  ("  C. Bucklin", constant),
  (" Linear Prop", linA),
  (" HalfLi Prop", linB),
  ("    Prop .4 ", pFa),
  ("    Prop .5 ", pFb),
  ("    Harmonic", harmA),
#  ("  Harmonic^2", harmB),
  ("  Dual Harm.", dualHarmonicF),
#  ("   1/2^ down", squareFa),
  ("     Dual 2^", dualSquareF),
  ("          CB", classicalB)
]

functions = []

# For comparisons - Borda, Cervone.
# their respective weights will be added after the test values.
# Note that the scores start at index 0 and the length is -1: the last value is always 0.

# little computation for Cervone
def oForm (n):
    nC = n-1
    CvFactor = 1.42554  # coding of Cervone factor.
    return [(1.0 - n/nC)**CvFactor for n in range(nC)]

# Common score vectors used for comparisons with weights.
# They are to be modified manually is some reference is added or the count is increased.
# note that we have two ways of computing normalized Borda - explicit and implicit.
# this was done to explore the arithmetic differences between the two and understand how
# some solutions were not found.
ScoreVectors = [
# 3
[([1.0, 1/2, 0.0], "   Borda(L)i"), ([1.0,0.37228, 0.0], "  Cervone"), ([1.0, .5, 0.0], "   Borda(L)e"), ([1.0, 1.0, 1.0], "  Bucklin"), ([3.0, 2.0, 1.0], " Std Borda") ],
#4 [(1.0 - n/3)**CvFactor for n in range(3)]
[([1.0, 2/3, 1/3, 0.0], "   Borda(L)i"), (oForm(4), "  Cervone"), ([1.0, .6666667, .3333333, 0.0], "   Borda(L)e"), ([1.0, 1.0, 1.0, 1.0], "  Bucklin"), ([4.0, 3.0, 2.0, 1.0], " Std Borda")],
#5  [(1.0 - n/4)**CvFactor for n in range(4)]
[([1.0, 3/4, 1/2, 1/4, 0.0], "   Borda(L)i"), (oForm(5), "  Cervone"), ([1.0, .75, .5, .25, 0.0], "   Borda(L)e"), ([1.0, 1.0, 1.0, 1.0, 1.0], "  Bucklin"), ([5.0, 4.0, 3.0, 2.0, 1.0], " Std Borda")],
#6    [(1.0 - n/5)**CvFactorfor n in range(5)]
[([1.0, 4/5, 3/5, 2/5, 1/5, 0.0], "   Borda(L)i"), (oForm(6), "  Cervone"), ([1.0, 0.8, 0.6, 0.4, 0.2, 0.0], "   Borda(L)e"), ([1.0, 1.0, 1.0, 1.0, 1.0, 1.0], "  Bucklin"), ([6.0, 5.0, 4.0, 3.0, 2.0, 1.0], " Std Borda")]
]

# derived from above and likewise hard coded
# this is exported into the application program - rather brittle.
iBLidx = 0 # index for Borda
cVidx = 1 # index for Cervone
eBLidx = 2 # index for standard Bucklin
stdBidx = 3
tbIdx = 4 # index for standard Borda - if necessary.
freeNidx = 3 # first score vector not used.
extraV = freeNidx # where can we start filling up new values from.

# How Many Decimals? Number of digits used by default in representation of points.
hmd = 4

# --- Utilities ---

# stringToTuples  takes a string representing a sequence of range tuples
# (composed of two floating point values and an one int)
# and turns it in list of tuples of points, and one numner, which is the minimal numner of decimals to use
# to represent the numbers, based on the size of the increment.
# in other words, this is completely ad-hoc, and brittle
# (f,f,i), (f,f,i) [, (f,f,i)]*
# returns this list + another list of significant decimals.


# we have two forms of this. The original one just below - will take the tuples
# and read them as bottom, increment, number of increments.

# the other form below, used by default, extends the syntax to different forms od using such
# tuples: as range from bottom, around a middle, or a single value.

def stringToTuplesOrig(s):
    # number of decimals in a string.
    def sigDigits(a):
        off = 1 if a[0]=='.' else 2
        return  len(a) - off

    go = s.find('(')
    ss = s
    range = []
    sizes = []
    while go != -1 :
        end = ss.find(')')
        extract = ss[go+1:end]
        a = extract.split(',')
        range.append(tuple( [float(a[0]), float(a[1]), int(a[2])] ))
        sizes.append( sigDigits(a[1]) )  # find the number of significant decimals from the size of increment.
        ss = ss[end+1:]
        go = ss.find('(')
    return range, sizes

# in other words, this is completely ad-hoc, and brittle
# "bot" or "around" (....), or single
# as described above
def stringToTuplesExt(s):
    # number of decimals in a string.
    def sigDigits(a):
        off = 1 if a[0]=='.' else 2
        return  len(a) - off
    # to return results.
    range = []
    sizes = []
    go = s.find('(')
    start=0
    while s[start] not in 'afs': start+=1  # first letters must be a, f or s.
    if s[start] == 'a': # around
        ss = s
        while go != -1 :
            end = ss.find(')')
            extract = ss[go:end+1] # keep the brackets!
            xtracted = eval(extract)
            range.append( (xtracted[0]-xtracted[1]*xtracted[2], xtracted[1], xtracted[2]+xtracted[3]+1 ) )
            sizes.append(4)
            ss = ss[end+1:]
            go = ss.find('(')
        print("created range and size", range, sizes)
    elif s[start] == 'f' : # from bottom - traditional
        ss = s
        while go != -1 :
            end = ss.find(')')
            extract = ss[go+1:end]
            a = extract.split(',')
            range.append(tuple( [float(a[0]), float(a[1]), int(a[2])] ))
            sizes.append( sigDigits(a[1]) )  # find the number of significant decimals from the size of increment.
            ss = ss[end+1:]
            go = ss.find('(')
    elif s[start] == 's' : # Just one point. different structure, but we recreate internal model for single value.
        ss = s
        end = ss.find(')')
        extract = ss[go+1:end]
        a = extract.split(',')
        for pts in a:
            range.append(tuple( [float(pts), 0.0, 1] ))
            sizes.append( sigDigits(6) )  # find the number of significant decimals from the size of increment.
    else:
        # fail.
        print("could not parse parameters", s)
        sys.exit(0)
    return range, sizes

# switching to a new form of input parameters to have more flexibility in the
# way we define exploration zones, for either weights or scores
# this allows us flexibility to experiment without changing the rest of the code.
# since all processing is localized in stringToTuples.
#
stringToTuples=stringToTuplesExt

# little utility to truncate upwards (ceiling) of a number with a
# chosen number of decimals.
def truncateUp(number, digits) -> float:
    stepper = 10.0 ** digits
    return math.trunc(stepper * number+1) / stepper

# --- End of utilities.

# -- defining regions.

# the alternative to passing regions through the command line is
# to have these "builtin areas"

# just hard coding this for simplicity for cubic regions, points.
# these values are ranges used for exploration
# since this has changed through times and may vary according to input
# we now have the possibility to introduce a sequence through the input line.
ranges =[ [],[],[],
# 3
    [(0.3817,0.00003,20)],
#    [(0.3810,0.0001,25)],
# 4
    [(0.591,0.0005,20),(0.285,0.001,10)],
#    [(0.55,0.005,20),(0.27,0.02,10)],
#    [(0.5,0.02,10),(0.20,0.02,10)],
# 5
    [ (0.72, 0.004,10), (0.46,0.002,10), (0.22,0.002, 10)],
#    [ (0.6, 0.02,10), (0.4,0.02,10), (0.2,0.02, 10)],
#
#    [(1.0/6, 0.3/10), (1.0/6, 0.3/10)],
#    [(1.0/6, 0.3/10), (1.0/4, 0.5/10), (1.0/6, 0.3/10)],
#    [(1.0/6, 0.3/10), (1.0/4, 0.5/10), (1.0/4, 0.5/10),(1.0/6, 0.3/10)],
# 6
#    [ (0.78,0.004,10), (0.58,0.004,10), (0.38,0.004,10), (0.18,0.004,10)]
    [ (0.76, 0.005, 14), (0.56, 0.005, 10), (0.37, 0.004, 10), (0.182,0.004,9)  ]
]

# this is for cubic areas. They were explored mostly for IAC before the
# command line flexibility was introduced.
# all values were found experimentally and added to the list.
# below specific values are chosen into an appropriate universal
# data structures, valid for spatial, IC and IAC.
C_IAC_3 = [
    [(1.00, 0.01, 40),(0.25, 0.025, 16)], # 1.035-1.085/25/.002	.425-.575/30/.005
    [(1.035, 0.002, 25),(0.425, 0.005, 30)],
    [(1.0416, 0.00001, 20), (0.54,0.0005,20)],
    []
]

C_IAC_4 = [
  [ (1.00, 0.025, 40),(0.4, 0.025, 16), (0.20, 0.025,16)],
  [ (1.00, 0.01, 50),(0.55, 0.01, 16), (0.25, 0.01,16)],
  [ (1.00, 0.005, 20),(0.565, 0.005, 17), (0.31, 0.005,10)],
  [ (1.03, 0.002, 10),(0.61, 0.002, 10), (0.33, 0.002,10)],
  [ (1.0, 0.005, 20),(0.55, 0.005, 40), (0.30, 0.01 , 20)],
  [ (1.0, 0.005, 20),(0.55, 0.005, 40), (0.31, 0.005,20)],
  [ (1.04, 0.002, 35), (0.57,0.005,12), (.32, 0.004, 15)  ], # take 2
  [ (1.044, 0.001, 12), (0.588,0.002, 25), (0.315, 0.005, 8)],
  [ (1.044, 0.0002, 12), (0.588,0.001, 50), (0.315, 0.002, 20)],
  [ (1.0445, 0.00005, 10), (0.6090, 0.0005, 25), (0.3440, 0.0005, 6)],
  []
]

C_IAC_5 = [
  [ (1.0, 0.05, 20),(0.70, 0.005, 20), (0.40, 0.010, 20), (0.20, 0.01, 10)],
  [ (1.0, 0.005, 12),(0.70, 0.005, 13), (0.42, 0.010, 10), (0.23, 0.01, 7)],
  [ (1.04, 0.002, 10), (.725, .005, 9), (.44, .005, 6), (.23, .005, 8)],
  [ (1.008, 0.002, 27), (0.705, 0.005, 11), (0.43, 0.005, 14), (0.24, 0.005, 10)],
  [ (1.0, 0.005, 11), (0.705, 0.005, 11), (0.425, 0.005, 16), (0.245, 0.005, 10) ],
  [(1.0276, 0.0002, 5),(0.7356, 0.0002, 5), (0.4826, 0.0002, 5), (0.256, 0.002, 5)]
]

C_IAC_6 = [
  [(1.0,0.005,6),(0.75,0.01,6),(0.58,0.01,5),(0.38,0.01,5),(0.19,0.01,5)]
]

# aValue bValue aInc bInc aCount, bCount
CubicRegions = { # for 3, 4, 5, 6 for each type.
's': [ [ (0.95, 0.01,  10), (0.85, 0.01, 10) ], [(0.9, 0.01, 20),(0.6,0.01, 20), (0.25, 0.01,20)], [], []  ],
'IC': [ [ (0.9, 0.005,  40),   (0.4, 0.005, 40) ], [(0.9, 0.01, 20),(0.6,0.01, 20), (0.25, 0.01,20)], [], []   ],
# 'IAC': [ [ (1.04, 0.0001, 100), (0.51,0.0001,100) ], [(0.9, 0.01, 20),(0.6,0.01, 20), (0.25, 0.01,20)] ],
#'IAC': [ [ (1.04, 0.0001, 100), (0.51,0.0001,100) ], [(0.99, 0.005, 20),(0.6,0.005, 20), (0.28, 0.005,20)] ],
# 'IAC': [ [ (1.04, 0.0001, 100), (0.51,0.0001,100) ], [(1.0445, 0.0001, 10),(0.6195, 0.0001, 10), (0.3345, 0.0001,10)] ],
'IAC': [
    C_IAC_3[1],
#1.0400-0.6200-0.3400 -  1.0800-0.6000-0.3200 - CW
    C_IAC_4[6],
#    [(1.020, 0.002, 10),(0.73, 0.002, 10), (0.475, 0.001, 10), (0.25, 0.005, 10)],
#    [(1.0356, 0.0002, 5),(0.7376, 0.0002, 5), (0.4766, 0.0002, 5), (0.246, 0.002, 5)],
    C_IAC_5[3],
    C_IAC_6[0]
 ]
}

# after cubic, we add specific point values.
# Ideally these should be read from some other file, but this was convenient enough.
#

# Holding best values for weighted Bucklin observed experimentally.
dataPoints = {
 's': [
 [ "1.00-0.50" ], #3
 [ "1.0200-0.6800-0.3400", #4
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500",
 "1.0200-0.6800-0.3400",
 "1.0500-0.7000-0.3500",
 "1.0800-0.7200-0.3600",
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500",
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500" ],
 [ "1.0000-0.7300-0.4900-0.2800", #5
"1.0000-0.7500-0.5000-0.2500",
"1.0000-0.7550-0.4700-0.2800",
"1.0000-0.7550-0.4800-0.2700",
"1.0500-0.7150-0.4700-0.2700",
"1.0500-0.7250-0.4700-0.2700",
"1.0500-0.7300-0.4600-0.2600",
"1.0500-0.7350-0.4700-0.2500",
"1.0500-0.7400-0.4600-0.2600",
"1.0500-0.7450-0.4300-0.2800",
"1.0500-0.7550-0.4600-0.2400"],
["1.000-0.792-0.614-0.410-0.200", #6 - but really global data.
 "1.000-0.796-0.606-0.395-0.210",
 "1.000-0.800-0.600-0.400-0.200",
 "1.000-0.804-0.612-0.385-0.210",
 "1.008-0.802-0.610-0.400-0.205",
 "1.010-0.804-0.598-0.390-0.200",
 "1.016-0.790-0.598-0.410-0.190",
 "1.018-0.798-0.604-0.385-0.200",
 "1.022-0.788-0.612-0.380-0.205",
 "1.022-0.790-0.600-0.400-0.185",
 "1.022-0.798-0.598-0.395-0.200",
 "1.022-0.802-0.598-0.380-0.200"]
],
 'IC': [[ "1.00-0.50" ], #3
 ["1.0200-0.6800-0.3400", #4
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500",
 "1.0200-0.6800-0.3400",
 "1.0500-0.7000-0.3500",
 "1.0800-0.7200-0.3600",
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500",
 "1.0800-0.7200-0.3600",
 "1.0500-0.7000-0.3500",
], #5
["1.0000-0.7300-0.4900-0.2800",
"1.0000-0.7500-0.5000-0.2500",
"1.0000-0.7550-0.4700-0.2800",
"1.0000-0.7550-0.4800-0.2700",
"1.0500-0.7150-0.4700-0.2700",
"1.0500-0.7250-0.4700-0.2700",
"1.0500-0.7300-0.4600-0.2600",
"1.0500-0.7350-0.4700-0.2500",
"1.0500-0.7400-0.4600-0.2600",
"1.0500-0.7450-0.4300-0.2800",
"1.0500-0.7550-0.4600-0.2400"],
["1.000-0.792-0.614-0.410-0.200", #6 - mix.
 "1.000-0.796-0.606-0.395-0.210",
 "1.000-0.800-0.600-0.400-0.200",
 "1.000-0.804-0.612-0.385-0.210",
 "1.008-0.802-0.610-0.400-0.205",
 "1.010-0.804-0.598-0.390-0.200",
 "1.016-0.790-0.598-0.410-0.190",
 "1.018-0.798-0.604-0.385-0.200",
 "1.022-0.788-0.612-0.380-0.205",
 "1.022-0.790-0.600-0.400-0.185",
 "1.022-0.798-0.598-0.395-0.200",
 "1.022-0.802-0.598-0.380-0.200"]
],
 'IAC': [
#3
["1.0530-0.5500",
"1.0530-0.5250" ,
"1.0570-0.4750" ,
"1.0650-0.5250" ,
"1.0450-0.4550" ,
"1.0530-0.5300" ,
"1.0610-0.5100" ,
"1.0430-0.4850" ,
"1.0390-0.5000" ,
"1.0430-0.5050" ,
"1.0530-0.5100"],
# best 10 IAC for 4
    [ '1.0600-0.6100-0.3350',
'1.0600-0.5900-0.3500',
"1.0650-0.5950-0.3400",
'1.0450-0.6150-0.3400',
'1.0400-0.6250-0.3400',
'1.0650-0.5950-0.3400',
'1.0350-0.5950-0.3800',
'1.0500-0.6000-0.3650',
'1.0950-0.5850-0.3200',
'1.0650-0.6000-0.3350',
'1.1000-0.5700-0.3300'],
# best 10 IAC for 5    [ '1.0362-0.7382-0.4768-0.2500', '1.0356-0.7378-0.4766-0.2500', '1.0358-0.7378-0.4766-0.2500', "1.0300-0.7400-0.4800-0.2500", "1.0250-0.7350-0.4900-0.2550", '1.0300-0.7400-0.4800-0.2600',    '1.0278-0.7358-0.4826-0.2620', '1.0280-0.7360-0.4826-0.2620'],
["1.0000-0.7300-0.4900-0.2800",
"1.0000-0.7500-0.5000-0.2500",
"1.0000-0.7550-0.4700-0.2800",
"1.0000-0.7550-0.4800-0.2700",
"1.0500-0.7150-0.4700-0.2700",
"1.0500-0.7250-0.4700-0.2700",
"1.0500-0.7300-0.4600-0.2600",
"1.0500-0.7350-0.4700-0.2500",
"1.0500-0.7400-0.4600-0.2600",
"1.0500-0.7450-0.4300-0.2800",
"1.0500-0.7550-0.4600-0.2400"],
# best 10 IAC for 6
    [ "1.0140-0.8020-0.6060-0.3850-0.1950", "1.0000-0.8000-0.6000-0.4000-0.2000", '1.0200-0.8020-0.5980-0.3800-0.2000',
      '1.0200-0.7980-0.6000-0.4000-0.1850', '1.0200-0.8000-0.5800-0.3900-0.2200', '1.0200-0.7900-0.5900-0.4100-0.1900',
      "1.000-0.792-0.614-0.410-0.200", #6
       "1.000-0.796-0.606-0.395-0.210",
       "1.000-0.800-0.600-0.400-0.200",
       "1.000-0.804-0.612-0.385-0.210",
       "1.008-0.802-0.610-0.400-0.205",
       "1.010-0.804-0.598-0.390-0.200",
       "1.016-0.790-0.598-0.410-0.190",
       "1.018-0.798-0.604-0.385-0.200",
       "1.022-0.788-0.612-0.380-0.205",
       "1.022-0.790-0.600-0.400-0.185",
       "1.022-0.798-0.598-0.395-0.200",
       "1.022-0.802-0.598-0.380-0.200"]
    ]
}

# -- processing information.

# currently used. 2 options: use the "range" data structure defined above, or the command line argument.
# note that we use two different representations.
# the builtin values have a leading 1, but ranges (or args) do not, so it is added.
def fillScoreVectors(nC, args):
    weights = []
    results = [1.0 for i in range(nC-1)]
    selection, sizemap =  (ranges[nC], [ 4 for i in ranges[nC]]) if args == '' else stringToTuples(args)

    # embedded recursive function, usable for any number of dimensions.
    # note that this implicitly adds a leading one in the sequence of weights.
    # the leading 1.0 comes from the initialisation of results.
    def ifsv(current):
        val, inc, number = selection[current]
        nlow = val
        nhigh = min(val+ inc*number, results[current])
        next = current+1
        while nlow <= nhigh:
            results[next] = nlow
            nlow+=inc
            if next+1 == nC-1:
                weights.append(results.copy())
            else:
                ifsv(next)
    ifsv(0)

#    print("fillScoreVectors", len(weights), [1]+sizemap)
    return weights, [1]+sizemap
# aa = fillScoreVectors(3)

# this is used as a global variable as it is initiated by a procedure of this module, but used in multiple
# locations.  Not the cleanest, but this code is mostly about expediency.
currentRegion = []

# an orphan utility function.
# sanity check function to make sure that the weigths respect a monotically decreasing sequence.
def wellOrdered( weights, nC ):
    for i in range(nC-2):
        if weights[i]<=weights[i+1]:
            return False
    return True


# now the generation functions for the different forms of areas - cubic, pyramid.

# # of candidates, offset, ...
# args from the command line, is presents.
# we generate an orthotope from boundary, increments and counts.
def generateCubic(nC, off, var, extraV, args):
    global currentRegion
    functions = []
    # sizemap is a number of decimals for output.  by default it is hmd, otherwise computed by stringToTuples
    pars, sizemap =  stringToTuples(args) if args != '' else (CubicRegions[var][off], [ hmd for i in CubicRegions[var][off]])
    currentRegion = pars

    print('Cubic', pars)
    print('From', [a for (a,b,c) in pars], "to", [a+b*c for (a,b,c) in pars], 'by', [b for (a,b,c) in pars])

    nAlternatives = 1
    current = [0, 0] # used for counting how many values make it through the filter.
    threshold = nC/2 # generates floating point value

    def recurseCubic(idx, vals):
        if idx > nC-2:
            # o = sum(vals)
            lastTotal = total = 0
            for x in range(nC-1): # assumption last value is 0.
                (x1,x2,_) = pars[x]
                voteWeights[ current[0] ][x] =  x1 + vals[x]*x2
                lastTotal = total
                total += voteWeights[current[0]][x]
            if total >= threshold and lastTotal < threshold and wellOrdered( voteWeights[current[0]], nC): # Bucklin condition
                functions.append( '-'.join(["{1:,.{0}f}".format( sizemap[x], voteWeights[ current[0] ][x]) for x in range(nC-1)] ) )
                current[0] += 1
            else:
                current[1] += 1
        else:
            (b, i, s) = pars[idx]
            vals[idx] = 0
            for _ in range(s):
                recurseCubic(idx+1, vals)
                vals[idx] += 1
        return

    for (_,_,a) in pars:
        nAlternatives *= a
    nAlternatives -= current[1]

    voteWeights = np.zeros( (nAlternatives+extraV, nC), dtype=float)
    recurseCubic(0, [ 0 for i in range(nC) ])
    msg = "Cubic: " + str(current[1]) + " skipped out of " + str(nAlternatives) + " cases\n"
    sys.stderr.write(msg)
#    print( "Cubic:", current[1],"skipped out of ", nAlternatives, "cases")
    nAlternatives -= current[1]
    return (nAlternatives, voteWeights, functions)

# similarly for pyramid - only used a bit at the beginning of experiments and not updated.
def generatePyramid(nC, off, var,extraV, args):
    # systematic large region. A triangle  (0,75,0,75) (1,5,0) (1,5, 1,5)

    functions = []
    points = []

    def recursePyramid(idx, prefix, val):
        while prefix[-1] >= val:
            if idx < nC-2:
                b = (nC/2 - sum(prefix)-val)/(nC-idx-2)
                recursePyramid(idx+1, prefix+[val], b)
            else:
                points.append((prefix+[val,0]).copy() )
            val += step

    base = truncateUp(nC/(2* (nC-1)), 3)
    bottom = [base for i in range(nC-1)]
    bottom.append(0)
    step = (nC/2 - base)/20
    point = bottom.copy()
    for x1 in range(20):
        recursePyramid(1, [point[0]], point[1])
        point[0] += step

    nAlternatives = len(points)

    voteWeights = np.zeros( (nAlternatives+extraV, nC), dtype=float)
    for i in range(nAlternatives):
        for j in range(nC):
            voteWeights[i, j] = points[i][j]
        functions.append('-'.join(["%.3f"%(voteWeights[i][x]) for x in range(nC-1)] ) )
    return (nAlternatives, voteWeights, functions)

#    IACset = [ "1.04-0.52" , "1.05-0.52" , "1.05-0.51" ,  "1.05-0.50" , "1.04-0.51", "1.04-0.47" ,  "1.05-0.48" ,"1.05-0.49" , "1.06-0.53" ,"1.06-0.48"]
#    ICset  =
#    Sset   =

# This simply converts from a list.
def generateDatapoints(nC, off, var, extraV, args):
    theSet = dataPoints[var][off]
    nAlternatives = len(theSet)
    voteWeights = np.zeros( (nAlternatives+extraV, nC), dtype=float)
    idx = 0
    for i in theSet:
        a = i.split('-')
        for j in range(len(a)):
            voteWeights[idx, j] = float(a[j])
        functions.append( i ) # just ignore the function.
        idx += 1
    return (nAlternatives, voteWeights, functions)

# keep in mind that we do not process anything below 3 (candidates) - so that becomes our index 0.
# we use this value as an offset
lowLimit = 3

# the choices of forms of exploration.
Variations =  {'Base': (0, lambda i,j,k:0), 'Pyramid': (1, generatePyramid), 'Cubic': (2, generateCubic), 'Points': (3,generateDatapoints) }

# Main function call.
def generate(nC, mType, sType, extras, args):  # number of candidates, IC|..., 'Base|Pyramid|..., TRue\False, n = step for extras'
#    global nCandidates, cOffset
#    nCandidates = nC
    global extraV, currentRegion
    cOffset = nC - lowLimit # compute index offset to eliminate situations where there are not enough candidates
    (_,f) = Variations[sType]

    ScoreV = ScoreVectors[cOffset][0:extraV] # initialize with minimal set of score vectors. Truncate, just in case.

    # do we need to add score vectors on top of weights?
    if extras:
        # in this case, args is used for score vectors
        currentRegion, sizemap = stringToTuples(args)
        extraVectors, sizemap = fillScoreVectors(nC, args)

        for i in extraVectors:
            ScoreV.append( (i, '-'.join([ "{1:,.{0}f}".format( sizemap[x], i[x]) for x in range(nC-1)]) ) )
#            ScoreV.append( (i, '-'.join(["%.3f"%(   i[x]) for x in range(nC-1)]) ) )
    extraV = len(ScoreV)

    # generic call. f has been initalized above.
    (nAlternatives, voteWeights, functions) = f( nC, cOffset, mType, extraV, args )

    idx = nAlternatives
    for (xi,xj) in ScoreV:
        for xk in range(len(xi)):
            voteWeights[idx, xk] = float(xi[xk])
        functions.append( xj ) # just ignore the function.
        idx += 1

# add the extra profiles.
# note that we keep increasing idx - room has been made with extraV.

    return (nAlternatives, voteWeights, functions)


# --- related support functions.
# the code below can be used to decide if the "best" solution found lies
# at the limit of the exploration zone
# within, inRegion
# or to propose a new, tighter exploration region. Can use used as required.

# create more narrow exploration zone.
# work in progress. It may not be suitable.
def tighten( weights, region = [] ):
    # assume I got an index into functions.
    cr = region if region != [] else currentRegion

    print("in tighten", cr, weights )
    # borders = []
    # for (i,j,k) in currentRegion:
    #     borders.append( (i, i+j*k) ) # low, high
    newborder = []
    point = weights[1:] if len(weights)==len(region) else weights[1:-1]
    topMet = [False for i in point]
    botMet = [False for i in point]

    for j,k in enumerate(point):
        (ri,rj,rk) = cr[j]
        topMet[j] = k == ri+rj*rk # borders[j][1]
        botMet[j] = k == ri # borders[j][0]
        if   topMet[j]:
            newborder.append( ( k-rj, rj, rk) )
        elif botMet[j]: #recenter
            newborder.append( ( round(k-rj*(rk-2),3), rj, rk) )
        else: # tighten interval
            rj = round(rj/2,3)
            newborder.append( ( round(k-rj*(rk//2),3), rj, rk) )

    return newborder, [ botMet[i] or topMet[i] for i in range(len(botMet)) ]

# a little utility to make sure that we are within the region
# note that it uses currentRegion, which can be set to different
# forms depending is we are doing a bucklin region or a score vector region.
def inRegion( test ):
    tA = test.split("-")
    tB = currentRegion
    # get rid of leading 1 of comparing points in score vectors
    valA = [float(i) for i in tA] if len(tA)==len(tB) else [float(i) for i in tA[1:] ]
    for i in range(len(valA)):
        if valA[i] < tB[i][0] or valA[i] >= tB[i][0]+tB[i][1]*tB[i][2]:
            return False
    return True

# more general form
# have any parameters of "test" reached the limits of some of low or high?
# skip first if skip is true.
def within(test, lowlimit, highlimit, skip=True):
    l = 1 if skip else 0
    for i in range(l,len(test)-1):
        if test[i]<=lowlimit[i] or test[i]>=highlimit[i]: return False
    return True
