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
import wx.lib.colourselect as cs


class DisplayPanel(wx.Panel):
	def __init__(self, *args, **kw):
		wx.Panel.__init__(self, *args, **kw)
		self.InitBuffer()
		self.SetBackgroundColour((51, 51, 51))
		self.SetForegroundColour((164, 211, 238))

	def InitBuffer(self):
		size = self.GetClientSize()
		self.buffer = wx.EmptyBitmap(max(1, size.width),
									 max(1, size.height))

	def Clear(self):
		dc = self.useBuffer and wx.MemoryDC(self.buffer) or wx.ClientDC(self)
		dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
		dc.Clear()
		if self.useBuffer:
			self.Refresh(False)

class OptionsPanel(wx.Panel):

	def __init__(self, parent, display):
		wx.Panel.__init__(self, parent)
		self.display = display

		sizer = wx.StaticBoxSizer(wx.StaticBox(self, label = "Options"),
									wx.VERTICAL)
		s = wx.GridSizer(rows = 1, cols = 2)
		self.label = wx.StaticText(self, -1, "K-Value : ")
		self.textBox = wx.TextCtrl(self, -1, "5")
		s.Add(self.label,0,wx.BOTTOM|wx.LEFT, 2)
		s.Add(self.textBox,0,wx.BOTTOM|wx.LEFT, 2)
		sizer.Add(s)

		self.showUpdates = wx.CheckBox(self, label = "Enable Updates during Iteration")
		sizer.Add(self.showUpdates, 0, wx.BOTTOM|wx.LEFT, 2)
		self.SetSizer(sizer)

		
class SpinPanel(wx.Panel):
	def __init__(self, parent, name, minValue, value, maxValue, callback):
		wx.Panel.__init__(self, parent, -1)
		if "wxMac" in wx.PlatformInfo:
			self.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)

		self.st = wx.StaticText(self, -1, name)
		self.sc = wx.SpinCtrl(self, -1, "", size = (70, -1))
		self.sc.SetRange(minValue, maxValue)
		self.sc.SetValue(value)
		self.sc.Bind(wx.EVT_SPINCTRL, self.OnSpin)
		self.callback = callback

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.st, 0, wx.ALIGN_CENTER_VERTICAL)
		sizer.Add((1,1),1)
		sizer.Add(self.sc)
		self.SetSizer(sizer)
		
		global spinPanels
		spinPanels[name] = self

	def SetValue(self, value):
		self.sc.SetValue(value)

	def OnSpin(self, event):
		name = self.st.GetLabel()
		value = self.sc.GetValue()
		if verbose:
			print 'On Spin', name, '=', value
		self.callback(name,value)

class AppFrame(wx.Frame):
	def __init__(self):
		#setBaseDB('dass1.db')
		initializeBaseDB()
		def makeSP(name, labels, statictexts = None):
			panel = wx.Panel(self.sidePanel, -1)
			box = wx.StaticBox(panel,-1, name)
			sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
			
			panel.rangeValue = {}

			for name, min_value, value, max_value in labels:
				sp = SpinPanel(panel, name, min_value, value, max_value, self.OnSpinback)
				panel.rangeValue[name] = sp
				sizer.Add(sp, 0, wx.EXPAND)

			print "done"

			panel.SetSizer(sizer)
			return panel

		wx.Frame.__init__(self, None, title = "CLUSTERING ALGORITHM")

		self.displayPanel = DisplayPanel(self)
		self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
		self.axes.set_axis_bgcolor('white')
		self.canvas = Canvas(self.displayPanel, -1, self.figure)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.canvas, 1, wx.EXPAND)
		self.displayPanel.SetSizer(sizer)
		self.displayPanel.Fit()
		self.toolbar = NavigationToolbar(self.canvas)
		self.SetToolBar(self.toolbar)
		self.toolbar.Realize()
		tw, th = self.toolbar.GetSizeTuple()
		fw, fh = self.canvas.GetSizeTuple()
		self.toolbar.SetSize(wx.Size(fw, th))
		self.toolbar.update()
		self.redraw_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
		self.stopStart = threading.Event()
		self.data = None
		self.centroids = None
		self.clusterIds = None
		self.colors = None
		self.k = 0
		self.iterTimer = 0
		self.iterations = 15
		self.sidePanel = wx.Panel(self)
		self.dictionary = {'Area':'AREA', 'Perimeter':'PERIMETER',
							'Roundness':'ROUNDNESS','Equi-Diameter':'EQUI_DIAMETER',
							'Convex Area':'CONVEX_AREA', 'Solidity': 'SOLIDITY',
							'Major Axis':'MAJOR_AXIS_LEN','Minor Axis': 'MINOR_AXIS_LEN',
							'Eccentricity':'ECCENTRICITY', 'Mean Pixel Intensity':'MEAN_PIXEL_DEN',
							'Max Pixel Intensity':'MAX_PIXEL_DEN'
							}
		featureList = ['Area', 'Perimeter', 'Roundness', 'Equi-Diameter', 
						'Convex Area', 'Solidity', 'Major Axis', 'Minor Axis',
						'Eccentricity', 'Mean Pixel Intensity', 'Max Pixel Intensity']

		self.featuresPanel = wx.Panel(self.sidePanel, -1)
		box = wx.StaticBox(self.featuresPanel, -1, 'Features')
		self.subPanel = wx.Panel(self.featuresPanel, -1)
		sizer = wx.GridSizer(rows = 6, cols = 2)

		global featureCB

		for feature in featureList:
			cb = wx.CheckBox(self.subPanel, label=feature)
			featureCB[feature] = cb
			sizer.Add(cb, 0, wx.BOTTOM|wx.LEFT, 2)
		
		self.subPanel.SetSizer(sizer)

		sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		sizer.Add(self.subPanel)
		self.featuresPanel.SetSizer(sizer)

		self.feature1 = makeSP('FEATURE 1 RANGES',
							  (('Minimum', 1, 1, 3600),
							   ('Maximum', 1, 3600, 3600)))

		self.feature2 = makeSP('FEATURE 2 RANGES',
							  (('Minimum', 1, 1, 3600),
							   ('Maximum', 1, 3600, 3600)))

		self.optionPanel = OptionsPanel(self.sidePanel, self.displayPanel)


		button = wx.Button(self.sidePanel, -1, "START")
		button.Bind(wx.EVT_BUTTON, self.startProcess)

		buttonClose = wx.Button(self.sidePanel, -1, "CLOSE")
		buttonClose.Bind(wx.EVT_BUTTON, self.stopProcess)

		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panelSizer.Add(self.featuresPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.feature1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.feature2, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.optionPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(button, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(buttonClose, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		self.sidePanel.SetSizer(panelSizer)

		mainSizer = wx.BoxSizer(wx.HORIZONTAL)
		mainSizer.Add(self.displayPanel, 1, wx.EXPAND)
		mainSizer.Add(self.sidePanel, 0, wx.EXPAND)
		self.SetSizer(mainSizer)

		mainSizer.Fit(self)
		rw, rh = self.displayPanel.GetSize()
		sw, sh = self.sidePanel.GetSize()
		fw, fh = self.GetSize()
		h = max(600, fh)
		w = h + fw - rw

		if verbose:
			print 'Display Panel Size', (rw, rh)
			print 'Side Panel Size', (sw, sh)
			print 'Frame Size', (fw, fh)

		self.SetSize((w,h))
		self.Show()

	def OnSpinback(self, name, value):
		if verbose:
			print 'On Spin Back', name, value


	def stopProcess(self,event):
		closeConnBaseDB()
		sys.exit()


	def startProcess(self, event):
		print 'in kmeans'
		featureList =[]
		isShowUpdate = False
		k = self.optionPanel.textBox.GetValue()
		isShowUpdate = self.optionPanel.showUpdates.GetValue()

		print 'spin_panels', spinPanels.keys()
		for key in featureCB.keys():
			if featureCB[key].GetValue():
				featureList.append(key)
				print featureCB[key].GetValue()

		print featureList
		print k
		print isShowUpdate

		for key in spinPanels.keys():
			print self.feature1.rangeValue[key].sc.GetValue()
			print self.feature2.rangeValue[key].sc.GetValue()
		#start the kmean process
		self.displayPanel
		datalist = getFeatures(self.dictionary[featureList[0]],
					 self.dictionary[featureList[1]])
		print datalist
		self.data = vstack([(f1,f2) for (n, f1, f2) in datalist])
		self.k = int(k)
		#Intial clusters from selecting points -- start
		#-------------------
		#Intial clusters from selecting points -- end
		self.animation = isShowUpdate
		self.init_plot(self.data, self.k, featureList[0], featureList[1])
		time.sleep(1)
		if not self.animation:
			self.cluster_kmeans(datalist, self.k, False)
		else:
			self.centroids = self.init_cluster()
			self.iterTimer = 0
			self.redraw_timer.Start(2)

	def init_cluster(self):
		centroids,_ = kmeans2(self.data, self.k, iter=1, thresh=1e-05, minit='random')
		return centroids
	def timer_kmeans(self):
		lastCentroids = vstack(list(self.centroids)[:])
		self.centroids,_ = kmeans2(self.data, lastCentroids, iter=1, thresh=1e-05, minit='matrix')
		self.clusterIds,_ = vq(self.data,self.centroids)
		self.redraw(self.iterTimer)
		return array_equal(lastCentroids,self.centroids)
	def on_redraw_timer(self, event):
		if self.iterTimer < self.iterations:
			changed = self.timer_kmeans()
			self.iterTimer+=1
			if self.iterTimer == self.iterations-1 or changed:
				self.redraw_timer.Stop()
				#self.redraw(self.data,self.centroids, clusterIds, self.k, -1)
				self.redraw(-1)

	def init_plot(self,data,k, feature1, feature2):
		self.axes.clear()
		x = array([d[0] for d in data])
		y = array([d[1] for d in data])
		maxX = max(x)
		minX = min(x)
		maxY = max(y)
		minY = min(y)
		self.xlabel = feature1
		self.ylabel = feature2
		self.axes.set_xlabel(self.xlabel)
		self.axes.set_ylabel(self.ylabel)
		self.axes.set_title('Intial scatter plot before clustering')
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		self.axes.plot(x,y,'bo')
		self.canvas.draw()
		self.colors = ['r','g','b']
		self.colors.extend([(random.random(), 
			random.random(), random.random()) for i in range(k)])

	def cluster_kmeans(self, feature1Bound=None,
						feature2Bound=None,iter=None):
		random.seed(time.time())
		#TODO: If initial centroid not given only
		self.centroids,_ = kmeans2(self.data, self.k, iter=1, thresh=1e-05, minit='random')
		lastCentroids = None
		print self.centroids
		print '\n'
		i = 0
		while not array_equal(lastCentroids,self.centroids) and i < self.iterations:
			i+=1
			lastCentroids = vstack(list(self.centroids)[:])
			self.centroids,_ = kmeans2(self.data, lastCentroids, iter=1, thresh=1e-05, minit='matrix')
			self.clusterIds,_ = vq(self.data,self.centroids)
		self.redraw(-1)
		print i, self.iterations
		print self.centroids

	def redraw(self, iteration):
		 wx.CallAfter(self.redraw_actual, iteration)
	def redraw_actual(self, iteration):
		self.axes.clear()
		self.axes.set_xlabel(self.xlabel)
		self.axes.set_ylabel(self.ylabel)
		if iteration == -1:
			self.axes.set_title('Final clusters formed')
		else:
			self.axes.set_title('Clusters during kmeans iteration '+str(iteration))
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		for i in range(self.k):
			self.axes.plot(self.data[self.clusterIds==i,0],self.data[self.clusterIds==i,1],color=self.colors[i],marker='o',linestyle='None')
			self.axes.plot(self.centroids[i,0],self.centroids[i,1],color=self.colors[i], marker='H',markersize=20.0)
		for i in range(len(self.data)):  
			self.axes.plot([self.data[i,0],self.centroids[self.clusterIds[i],0]],[self.data[i,1],self.centroids[self.clusterIds[i],1]], color=self.colors[self.clusterIds[i]])
		self.canvas.draw()
'''
	def redraw(self, data, centroids,clusterIds,k,iteration):
		 wx.CallAfter(self.redraw_actual, data, centroids,clusterIds,k, iteration)
	def redraw_actual(self, data, centroids,clusterIds,k, iteration):
		self.axes.clear()
		self.axes.set_xlabel(self.xlabel)
		self.axes.set_ylabel(self.ylabel)
		if iteration == -1:
			self.axes.set_title('Final clusters formed')
		else:
			self.axes.set_title('Clusters during kmeans iteration '+str(iteration))
		#self.axes.set_xbound(-10, 1200)
		#self.axes.set_ybound(-10, 1200)
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		for i in range(k):
			self.axes.plot(data[clusterIds==i,0],data[clusterIds==i,1],color=self.colors[i],marker='o',linestyle='None')
			self.axes.plot(centroids[i,0],centroids[i,1],color=self.colors[i], marker='H',markersize=20.0)
		for i in range(len(data)):  
			self.axes.plot([data[i,0],centroids[clusterIds[i],0]],[data[i,1],centroids[clusterIds[i],1]], color=self.colors[clusterIds[i]])
		self.canvas.draw()
'''
if __name__ == '__main__':		
	verbose = 0
	spinPanels = {}
	featureCB = {}
	app = wx.App(False)
	AppFrame()
	if verbose:
		print 'Features', featureCB.keys()
	app.MainLoop()




