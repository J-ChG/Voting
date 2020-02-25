# complely ad hoc code to extract specific statisticsa from results files.

# in this case we are looking at similitudes.


# case - 0
# Borda - 1
# ;Borda;
# L - 2-6
#L0; Lp2; Lr2; Lp3; Lr3;
# I - 7-11
# I0; Ip2; Ir2; Ip3; Ir3;
# H - 12-17
# H2p1; H2p2; H2r2; H3p1; H3p3; H3r3;
# 18     19    20      21     22    23       24     25
# allW; Ccet; NCcet; NCinAW; BDt; NotBDted; BDted;  untruncated condorcet")

# - all winners 18
# Condorcet 19
# Not borda dominated - 23

import csv
import sys
import functools, operator

# open file
assert len(sys.argv)==3, "Missing arguments: pgm name, # of candidates, file name"

Thrshld = int(sys.argv[1])
fReader = csv.reader(open(sys.argv[2], newline=''), delimiter=';', quotechar='|')

# skip first line
fReader.__next__()


Bcard = [0 for i in range(Thrshld)]
Icard = [0 for i in range(Thrshld)]
Lcard = [0 for i in range(Thrshld)]
Hcard = [0 for i in range(Thrshld)]

Idiverge = [0 for i in range(Thrshld+1)]
Ldiverge = [0 for i in range(Thrshld+1)]
Hdiverge = [0 for i in range(Thrshld+1)]

ties = [0 for i in range(17)]

wDist = [0 for i in range(Thrshld)]
dominatedSize = [0 for i in range(Thrshld+1)] # suppose they could all be dominated? Even if not realistic.
dominatedWin = 0

Bcount = 0
TCcount = 0
FCcount = 0
TCBmatch = 0
FCBmatch =0
tiesCount = 0
extraWinner = 0
condorcetChanges = 0
ConcavesCmatch = 0
ConvexesCmatch = 0

for row in fReader:
    Bgroup = set()
    Lgroup = set()
    Igroup = set()
    Hgroup = set()
    concaves = set() # Concave: L/2, L/3, I/3, and H/3
    convexes = set() # L2, L3, I1, I2, I3, H1, H2, H3, H/2

    tieSkip = False

    for i in range(17):
        c = row[i+1].count(',')
        if c>0:
            rs = set([int(i) for i in row[1].split(',')])
            ties[i] += 1
            tieSkip = True

    if not tieSkip:
        # process Borda
        Bgroup = set([int(i) for i in row[1].split(',')])
        Bcard[len(Bgroup)-1]+=1

        for i in range(2,7):
            Lgroup |= set([int(j) for j in row[i].split(',')])
        Lcard[len(Lgroup)-1]+=1
        Ldiverge[len(Bgroup^Lgroup)] += 1

        for i in range(7,12):
            Igroup |= set([int(j) for j in row[i].split(',')])
        Icard[len(Igroup)-1]+=1
        Idiverge[len(Bgroup^Igroup)] += 1

        for i in range(12,18):
            Hgroup |= set([int(j) for j in row[i].split(',')])
        Hcard[len(Hgroup)-1]+=1
        Hdiverge[len(Bgroup^Hgroup)] += 1

        winners =  set([ i for i in list( row[18] ) if i.isdigit() ])
        wDist [len(winners)-1] +=1

        dominants = set([ i for i in list( row[23] ) if i.isdigit() ])
        if not winners.issubset(dominants):
            extraWinner += 1

        # L0; Lp2; Lr2; Lp3; Lr3; I0; Ip2; Ir2; Ip3; Ir3; H2p1; H2p2; H2r2; H3p1; H3p3; H3r3;
        # Concave: L/2, L/3, I/3, and H/3
        for i in [4, 6]:
            concaves |= set([int(j) for j in row[i].split(',')])

        # # L2, L3, I1, I2, I3, H1, H2, H3, H/2
        for i in [8, 10, 13, 15 ]:
            convexes |= set([int(j) for j in row[i].split(',')])

        cW = int(row[19])
        if cW != -1:
            TCcount+=1
            if cW in Bgroup:
                TCBmatch += 1

        dominated = [ i for i in list( row[22] ) if i.isdigit() ]
        if len(dominated) != 0:
            Bcount += 1

        fCW = int(row[25])
        if fCW != -1:
            FCcount += 1
            if fCW in Bgroup:
                FCBmatch += 1

        if fCW in concaves:
            ConcavesCmatch += 1
        if fCW in convexes:
            ConvexesCmatch += 1

        if cW != fCW:
            condorcetChanges += 1

        dominated = [ i for i in list( row[24] ) if i.isdigit() ]
        # print(dominated, len(dominated))
        dominatedSize[len(dominated)] += 1

        win = [ i in winners for i in dominated]
        test = functools.reduce( operator.add, win, False)
        if test: dominatedWin+=1
    else:
        tiesCount += 1

    if (len(Lgroup)-1)==Thrshld or (len(Igroup)-1)==Thrshld or (len(Hgroup)-1)==Thrshld:
        print(row)

print(sys.argv[2],";;;", tiesCount, ";", Bcount, ";", FCcount,  ";", TCcount,";", FCBmatch, ';', TCBmatch, ';', ConvexesCmatch, ";", ConcavesCmatch, ";", ','.join([str(i) for i in wDist]), ';', Ldiverge[0], ';',Idiverge[0], ';', Hdiverge[0], ';', extraWinner, ';', condorcetChanges )
if False:
    print("occurrences of ties:", ','.join([str(i) for i in ties] ))
    print(Ccount, "occurrences of Condorcet winner, matching Borda ", CBmatch, "times.")
    print("distribution of number of winners from 1 to n:", ', '.join([str(i) for i in wDist]))
    print("distribution of number of BD candidates from 0 to n", ', '.join([str(i) for i in dominatedSize]), "(total", sum(dominatedSize), ")" )
    print("# of ≠ winners in L group", Lcard, "divergences from Borda (0 to n)", Ldiverge)
    print("# of ≠ winners in I group", Icard, "divergences from Borda", Idiverge)
    print("# of ≠ winners in H group", Hcard, "divergences from Borda", Hdiverge)
