# Misc support code, shared between different programmes, placed here
# to facilitate interop.

# ---- options management

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

# --- Used to create hash tables with lists as index

# list from string
def lFRs(s): return [int(i) for i in s.split('-')]
#string from list
def sFRl(l): return '-'.join([str(i) for i in l])

class ListTable:
    def __init__(self, list):
        self.table = {}
        self.index = {}
        cnt = 0
        for i in list:
            self.table[sFRl(i)] = 0
            self.index[sFRl(i)] = cnt
            cnt += 1

    def inc(self, l):
        self.table[sFRl(l)] += 1

    def count(self, l):
        return self.table[sFRl(l)]

    def indexOf(self, l):
        return self.index[sFRl(l)]


#==========
# code originally from paths .py, but trimmed.
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

# management of block structure.

Labels1 = ["Borda",
    "L0", "Lp2", "Lr2", "Lp3", "Lr3",
    "I0", "Ip2", "Ir2", "Ip3", "Ir3",
    "H2p1", "H2p2", "H2r2", "H3p1", "H3p3", "H3r3",
    "allW"]
Labels2 = ["Ccet", 'NCcet', 'FC', 'TCi', 'TCe']
Labels3 = [ "BDt", "NotBDted", "BDted", "dominants", "dominated", "isTCdominated", "1 dominates 2" ]
Labelse = ["FB"]
LabelsStr = ["index"] + Labels1 + Labels2 + Labels3 + Labelse
LabelsSet = [ ["index"], Labels1,  Labels2,  Labels3, Labelse ]

MaxGroups = 3

def LabelsList( labels, empty = False ):
    if empty:
        build = ' ; '.join([ '-' for i in range(len(labels))])
    else:
        build = ' ; '.join(labels)
    return build
