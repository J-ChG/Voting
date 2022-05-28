Computation of elections according to weighted Bucklin and comparison with weighted Borda.

The code first produces an exploration area for a local maximum - this is done in the "regions.py" file. Different options are possible but ultimately the "cubic" region was chosen. 

When the points option is chosen, a list of points is chosen, but another region is explored for the best weighted Borda results. As announced, this is all very ad-hoc and its use may still require modifying tables in regions.

It is best to look at the code to find out about options.

People who need to use or are interested in using this should get in touch with me.

buklinAny.py:	computation of elections and production of various results
regions.py:	generation of different weights to compute 
support.py:	generic support for elections.

3-61-....json: 	Election ballots in IC, IAC and Spatial models for 3 candidates and 61 voters.

Example of use: buklinAny.py -t Cubic -r '(0.9,0.02,15),(0.4,0.02,20)' 3-61-IC.json
