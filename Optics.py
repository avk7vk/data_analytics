"""
Created on Mar 17, 2012

@author: Amy X Zhang
amy.xian.zhang@gmail.com
http://amyxzhang.wordpress.com


Demo of OPTICS Automatic Clustering Algorithm
https://github.com/amyxzhang/OPTICS-Automatic-Clustering

"""

import numpy as np
import matplotlib.pyplot as plt
import OpticsClusterArea as OP
from itertools import *
import AutomaticClustering as AutoC
import sqlite3 as lite
import sys
'''Input : 
	f1 - Feature 1
	f2 - Feature 2
'''
def gen_optic_cluster(f1, f2):
	# generate some spatial data with varying densities
	np.random.seed(0)
	con = lite.connect('dass.db')
	X = []
	with con:

		cur = con.cursor()
		cur.execute("SELECT {}, {} FROM Features".format(f1, f2))
		rows = cur.fetchall()
	for row in rows:
		X.append([row[0], row[1]])
	print len(X)
	#plot scatterplot of points
	X = np.asarray(X)
	fig = plt.figure()
	ax = fig.add_subplot(111)

	ax.plot(X[:,0], X[:,1], 'bo')

	plt.savefig('Graph.png', dpi=None, facecolor='w', edgecolor='w',
    	orientation='portrait', papertype=None, format=None,
    	transparent=False, bbox_inches=None, pad_inches=0.1)
	#plt.show()



	#run the OPTICS algorithm on the points, using a smoothing value (0 = no smoothing)
	RD, CD, order = OP.optics(X,100)

	RPlot = []
	RPoints = []
        
	for item in order:
    		RPlot.append(RD[item]) #Reachability Plot
    		RPoints.append([X[item][0],X[item][1]]) #points in their order determined by OPTICS

	#hierarchically cluster the data
	rootNode = AutoC.automaticCluster(RPlot, RPoints)

	#print Tree (DFS)
	#AutoC.printTree(rootNode, 0)

	#graph reachability plot and tree
	#AutoC.graphTree(rootNode, RPlot)

	#array of the TreeNode objects, position in the array is the TreeNode's level in the tree
	array = AutoC.getArray(rootNode, 0, [0])

	#get only the leaves of the tree
	leaves = AutoC.getLeaves(rootNode, [])
	print 'leaves length = ',len(leaves)
	#graph the points and the leaf clusters that have been found by OPTICS
	fig = plt.figure()
	ax = fig.add_subplot(111)

	ax.plot(X[:,0], X[:,1], 'yo')
	colors = cycle('gmkrcbgrcmk')
	for item, c in zip(leaves, colors):
    		node = []
    		for v in range(item.start,item.end):
        		node.append(RPoints[v])
    		node = np.array(node)
    		ax.plot(node[:,0],node[:,1], c+'o')

	#plt.savefig('Graph2.png', dpi=None, facecolor='w', edgecolor='w',
    	#orientation='portrait', papertype=None, format=None,
    	#transparent=False, bbox_inches=None, pad_inches=0.1)
	plt.show()
if __name__ == '__main__':
	gen_optic_cluster(sys.argv[1], sys.argv[2])
