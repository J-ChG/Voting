# Misc support code, shared between different programmes, placed here
# to facilitate interoperability - and help with consistency.

# ---- options management
import itertools

# ---
def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        lA = argv[0]
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts, lA

# ---

# extract numbers from a string parameter to build a list.
# e.g. '1,3,5-8'
# and put it in a list
def getSelections(str):
    l = str.split(sep=',')
    o = []
    for i in l:
        m = i.split(sep='-')
        if len(m)>0:
            a = int(m[0])
        else:
            a = -1
        if len(m)>1:
            b = int(m[1])
            for j in range(a, b+1):
                o.append(j)
        else:
            o.append(a)
    return o

# different support functions to recreate list of numbers from a string representation
# as well as removing trailing 0s
# completely purpose built and not exactly robust: strongly assumes that the strings are properly formed.
def rebuild(sL):
  digits = '0123456789'
  idx = 0
  res = []
  while idx < len(sL):
    if sL[ idx ] == '-' and (idx+1) < len(sL) and sL[ idx+1 ] in digits:# accept a - only if attached to digit.
      sign = -1
      idx += 1
    else:
      sign = 1
    new_number = False
    cnt = 0
    while  idx < len(sL) and  sL[ idx ] in digits:
      cnt = 10*cnt+digits.index( sL[ idx ] )
      new_number = True
      idx += 1
    if new_number:
        res.append( sign*cnt)
    idx += 1
  return res

def stream(string):
    s = 0  # start
    e = len(string)-1  # end
    while string[s] in ' ,[]':
        s+=1
    while string[e] in ' 0,]' and e>s:
        e-=1
    if e==s:
        return '0'
    else:
        return string[s:e+1]

def trim( l):
    idx = len(l)
    while l[idx-1] == 0:
        idx -= 1
    return l[:idx]

# --- Used to create hash tables with lists as index

# list from string
def lFRs(s): return [int(i) for i in s.split('-')]
#string from list
def sFRl(l): return '-'.join([str(i) for i in l])


class ListTable:
    def __init__(self, list):
        self.table = {}
        self.index = {}
        self.cnt = 0
        self.added = False
        for i in list:
            self.table[sFRl(i)] = 0
            self.index[sFRl(i)] = self.cnt
            self.cnt += 1

    def inc(self, l):
        s = sFRl(l)
        try:
            self.table[s] += 1
        except KeyError:
            self.index[s] = self.cnt
            self.table[s] = 1
            self.added = True
            i = self.cnt
            self.cnt += 1

    def count(self, l):
        s = sFRl(l)
        try:
            i = self.table[s]
        except KeyError:
            i = -1
        return i

    def indexOf(self, l):
        s = sFRl(l)
        try:
            i = self.index[s]
        except KeyError:
            self.added = True
            self.index[s] = self.cnt
            self.table[s] = 0
            i = self.cnt
            self.cnt += 1
        return i


#==========
# used for spatial models.
# recursive function to build all paths, using reverse reachability.
def build(structure, prefix, index, result):
    if index == 0:
        result.append(prefix+[index])
    else:
        for i in structure[index]:
            build(structure, prefix+[index], i, result)
    return result


#  Manage Spatial model casesé
# it takes the number of candidates as a parameter and returns a tuple of (states, paths)
# because of path complexity, it explodes beyond 8 if paths are built.
# hence the construction of paths is set as an option.
def buildSpatialTable( nbr, buildPath = False ):
    table = [ [i for i in range(nbr)] ] # initialized with first sequence. Other values will be appended.
    preds = [[]]
    lookupTable = {sFRl(table[0]):0}
    # each prefix is itself a sequence of indexes in table.

    goOn= True
    crntIdx = 0 #
    totalLgth = 1 # length of sequence.

    while goOn:
      top = 0 # always start permutations from first element.

      # we initialize a sequence from a value in the table. Note that it may have been partially explored (first descendant)
      test = table[crntIdx].copy() # always safer: make a copy of current value to avoid making undue modifications.
      track = crntIdx # to remember where we come from.

      # skip descending prefix.

      if False:
          while top < nbr-1 and test[top] > test[top+1] :
            top+=1

          # push down lowest value in prefix.
          while top < nbr-1 and test[top] < test[top+1]:
            # swap
            test[top], test[top+1] = test[top+1], test[top]

            # check if found - this is likely as we first rediscover the first descendent.
            try:
              x = table.index(test)

              if track not in preds[x]:
                  preds[x].append(track)

              track = x
            except ValueError:
              table.append(test.copy()) # there may be more than one.
              preds.append([track])
              track = totalLgth
              totalLgth += 1
            top += 1
      else:
        while True:
            tst = table[track]
            if  (top == 0 and tst[0] < tst[1]) or (top >0 and tst[top-1] > tst[top] and tst[top] < tst[top+1]):

                test = tst.copy()

                test[top], test[top+1] = test[top+1], test[top]
#                print("generation", test, "from", tst, "(",track, ") at index", top)

                try:
#                    x = table.index(test)
                    x = lookupTable[sFRl(test)]
#                    print("found ", x, test)
#                    assert xp==x, "tables mismatch 1, "+' '+str(test)+' '+str(table)+' '+str(x)+' '+str(xp)

                    if track not in preds[x]:
                        preds[x].append(track)
#                        print("added predecessor to", x, preds[x])

#                    track = x
                except KeyError:
                    table.append(test.copy()) # there may be more than one.
                    lookupTable[ sFRl(test) ] = totalLgth
                    preds.append( [track] )
#                    print("new", totalLgth, test, "from ", track)
#                    track = totalLgth
                    totalLgth += 1
                top += 2
            else:
                top+=1
            if top >= nbr-1:
                break




      # move to next element to test.
      crntIdx += 1
      if crntIdx >= totalLgth: # all cases explored
        goOn = False
        r = []
        if buildPath:
            r = build( preds, [], len(preds)-1, r)
            for i in r:
                i.reverse()
    return table, r

# ======


def spatialOrders(nCandidates):
    orders, _ = buildSpatialTable(nCandidates)
    return orders

def COrders(nCandidates):
    return list(itertools.permutations([i for i in range(nCandidates)]))


# management of block structure.
# first block for score vectors - self explaining
Labels1 = ["Borda","L0", "Lp2", "Lr2", "Lp3", "Lr3","I0", "Ip2", "Ir2", "Ip3", "Ir3", "Cv", "allW"]
# second block for Condorcet, Copeland
# Condorcet Winner, Condorcet Loser, Condorcet Truncated Winner,???, Copeland scores, Who dominates the C.W., Who is dominated by the C.W.
# and the same for the loser
Labels2 = ["CcetW", 'CcetL', "CcetTW", 'Cop', 'Doms', "Domteds", 'DomsL', "DomtedsL" ]
# Borda computations: borda dominants, non borda dominated, borda dominated, ..., ..., ...
Labels3 = [ "BDt", "NotBDted", "BDted", "dominants", "dominated", "1d2" ]
# 'Borda,L0, Lp2, Lr2, Lp3, Lr3,I0, Ip2, Ir2, Ip3, Ir3, CcetW, CcetW, NCcet, Cop, Doms, Domteds,BDt, NotBDted, BDted, dominants, dominated'
allLabels = Labels1 + Labels2 + Labels3
# LabelsSet = [ Labels1,  Labels2,  Labels3 ]

MaxGroups = 3

# for earlier files.
conversion = { "Borda": 1, "L0":2, "Lp2": 3, "Lr2": 4, "Lp3":5, "Lr3": 6, "I0":7, "Ip2": 8, "Ir2": 9, "Ip3": 10, "Ir3": 11,
               "allW": 18, "CcetW": 19,  "CcetTW": 20, 'Cop': 21, 'Doms':22, "Domteds":23,  "BDt": 24, "NotBDted":25, "BDted": 26 }

def LabelsList( labels, empty = False ):
    if empty:
        build = ' ; '.join([ '-' for i in range(len(labels))])
    else:
        build = ' ; '.join(labels)
    return build
