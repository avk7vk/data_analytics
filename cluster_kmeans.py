#/usr/bin/python
import numpy as np
from numpy import vstack,array, array_equal
from numpy.random import rand
from scipy.cluster.vq import kmeans2,vq
from dbsetup import *
import random
import time
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
	FigureCanvasWxAgg as Canvas, \
	NavigationToolbar2WxAgg as NavigationToolbar
import wx
import pylab
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import threading
import sys

class Plot (threading.Thread):
#class Plot:
	app = wx.PySimpleApp()
	frame = wx.Frame(None,title="Clusters over generations")
	panel = wx.Panel(frame)
	figure = Figure()
	axes = figure.add_subplot(111)
	axes.set_axis_bgcolor('white')
	#axes.set_title('Very important random data', size=12)
	canvas = Canvas(panel, -1, figure)
	sizer = wx.BoxSizer(wx.HORIZONTAL)
	sizer.Add(canvas, 1, wx.EXPAND)
	panel.SetSizer(sizer)
	panel.Fit()
	toolbar = NavigationToolbar(canvas)
	frame.SetToolBar(toolbar)
	toolbar.Realize()
	tw, th = toolbar.GetSizeTuple()
	fw, fh = canvas.GetSizeTuple()
	toolbar.SetSize(wx.Size(fw, th))
	mainSizer = wx.BoxSizer(wx.VERTICAL)
	mainSizer.Add(panel, 1, wx.EXPAND)
	#mainSizer.Add(toolbar, 0, wx.LEFT | wx.EXPAND)
	toolbar.update()
	frame.SetSizer(mainSizer)
	mainSizer.Fit(frame)
	rw, rh = panel.GetSize()
	fw, fh = frame.GetSize()
	h = max(600, fh)
	w = h + fw - rw
	frame.SetSize((w,h))
	def init_plot(self,data,k):
		x = array([d[0] for d in data])
		y = array([d[1] for d in data])
		maxX = max(x)
		minX = min(x)
		maxY = max(y)
		minY = min(y)
		self.axes.set_xbound(-10, 1200)
		self.axes.set_ybound(-10, 1200)
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		self.axes.plot(x,y,'bo')
		self.colors = ['r','g','b']
		self.colors.extend([(random.random(), random.random(), random.random()) for i in range(k)])
	def run(self):
		self.frame.Show()
		self.app.MainLoop()
	def redraw(self, data, centroids,clusterIds,k):
		 wx.CallAfter(self.redraw_actual, data, centroids,clusterIds,k)
	def redraw_actual(self, data, centroids,clusterIds,k):
		self.axes.clear()
		self.axes.set_xbound(-10, 1200)
		self.axes.set_ybound(-10, 1200)
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		for i in range(k):
			self.axes.plot(data[clusterIds==i,0],data[clusterIds==i,1],color=self.colors[i],marker='o',linestyle='None')
			self.axes.plot(centroids[i,0],centroids[i,1],color=self.colors[i], marker='H',markersize=20.0)
		for i in range(len(data)):	
			self.axes.plot([data[i,0],centroids[clusterIds[i],0]],[data[i,1],centroids[clusterIds[i],1]], color=self.colors[clusterIds[i]])
		self.canvas.draw()

def cluster_kmeans(datalist, k, animation=True, feature1Bound=None,
					feature2Bound=None,iter=None):
	data = vstack([(f1,f2) for (n, f1, f2) in datalist])
	random.seed(time.time())
	centroids,_ = kmeans2(data, k, iter=1, thresh=1e-05, minit='random')
	lastCentroids = None
	print centroids
	print '\n'
	i = 0
	plotThread = Plot()
	plotThread.init_plot(data,k)
	plotThread.start()
	time.sleep(1)
	while not array_equal(lastCentroids,centroids) and i < 10:
		i+=1
		lastCentroids = vstack(list(centroids)[:])
		centroids,_ = kmeans2(data, lastCentroids, iter=1, thresh=1e-05, minit='matrix')
		clusterIds,_ = vq(data,centroids)
		plotThread.redraw(data,centroids, clusterIds, k)
		time.sleep(1)	
	print i
	print centroids
	plotThread.join()
	













'''
	datalist = [(f1,f2) for (n, f1, f2) in data]
	arraydata = vstack(datalist)
	print arraydata
	centroids,_ = kmeans(arraydata,k)
	clusterIdArray,_ = vq(arraydata,centroids)
	#print clusterIdArray, len(clusterIdArray)
	#print centroids
	print arraydata[clusterIdArray==0,0]
	x = array([data[0] for data in arraydata])
	y = array([data[1] for data in arraydata])
	colors =  rand(k)
	area  = [((i+1)*5) for i in clusterIdArray];
	print colors,area, clusterIdArray
	plt.scatter(x,y,s=area, c=colors,alpha=1)
	plt.show()
	pass
'''
if __name__ == '__main__':
	initializeBaseDB()
	data = getFeatures('AREA', 'PERIMETER')
	#print data
	closeConnBaseDB()
	cluster_kmeans(data,int(sys.argv[1]))
	sys.exit()
