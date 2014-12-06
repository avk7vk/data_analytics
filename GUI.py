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
import wx.lib.filebrowsebutton as filebrowse
import cv2
import re
import OpticsClusterArea as OP
from itertools import *
import AutomaticClustering as AutoC
import sqlite3 as lite




#################################################
# Display Panel for displaying the scatter plot #
#################################################
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

##################################################
# Option Panel for displaying the options    	 #
#	- Enable Updates during Iteration     	 #
#	- choose initial Centroids            	 #
##################################################

class OptionsPanel(wx.Panel):

	def __init__(self, mainFrame,parent, display):
		wx.Panel.__init__(self, parent)
		self.display = display
		self.mainFrame = mainFrame

		sizer = wx.StaticBoxSizer(wx.StaticBox(self, label = "Options"),
									wx.VERTICAL)
		s = wx.GridSizer(rows = 1, cols = 2)
		self.label = wx.StaticText(self, -1, "K-Value : ")
		self.textBox = wx.TextCtrl(self, -1, "5")
		s.Add(self.label,0,wx.BOTTOM|wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 2)
		s.Add(self.textBox,0,wx.BOTTOM|wx.LEFT, 2)
		sizer.Add(s)
		s = wx.GridSizer(rows = 1, cols = 2)
		self.showUpdates = wx.CheckBox(self, label = "Enable Updates during Iteration")
		self.chooseCentroid = wx.CheckBox(self,label="Choose Initial Centroids")
		self.chooseCentroid.Bind(wx.EVT_CHECKBOX, self.pkCentroid)
		s.Add(self.showUpdates, 0, wx.BOTTOM|wx.LEFT, 2)
		s.Add(self.chooseCentroid, 0, wx.BOTTOM|wx.LEFT, 2)
		sizer.Add(s)
		self.SetSizer(sizer)

	def pkCentroid(self, event):
		self.mainFrame.pickInputCentroids(self.chooseCentroid.IsChecked())



#####################################################################################
# Spin Panel for displaying the maximum and minimum values for two choosen features #
#####################################################################################

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

#####################################################################################
# AppFrame : Main Class for the GUI of the Application 								#
#####################################################################################
class AppFrame(wx.Frame):
	def __init__(self):
		setBaseDB('dass.db')
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

		################ Adding Drawing Panel ################

		self.displayPanel = DisplayPanel(self)
		self.figure = Figure()
		self.axes = self.figure.add_subplot(111)
		self.axes.set_axis_bgcolor('white')
		self.canvas = Canvas(self.displayPanel, -1, self.figure)

		################ Connecting the canvas to events for selecting intial centroid & nuclei ###################
		self.figure.canvas.mpl_connect('button_press_event', self.onGraphClick)
		self.figure.canvas.mpl_connect('pick_event', self.onNucleiPick)
		################ Connecting the canvas to events for selecting intial centroid & nuclei ###################
		
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
		self.centroids = []
		self.clusterIds = None
		self.colors = None
		self.k = 0
		self.iterTimer = 0
		self.iterations = 20
		self.sidePanel = wx.Panel(self)
		self.pointToPick = 0
		self.selectedFeaturesCount = 0
		self.isPickCentroids = False

		################ Adding Drawing Panel ################

		################ defining features for clustering algorithm ################

		self.dictionary = {'Area':'AREA', 'Perimeter':'PERIMETER',
							'Roundness':'ROUNDNESS','Equi-Diameter':'EQUI_DIAMETER',
							'Orientation':'ORIENTATION',
							'Convex Area':'CONVEX_AREA', 'Solidity': 'SOLIDITY',
							'Major Axis':'MAJOR_AXIS_LEN','Minor Axis': 'MINOR_AXIS_LEN',
							'Eccentricity':'ECCENTRICITY', 'Min Enclosing Rad':'CIR_RADIUS',
							'Shape Index':'SHAPE_INDEX','Border Index':'BORDER_INDEX','Aspect Ratio':'ASPECT_RATION', 
							'Mean Pixel Intensity':'MEAN_PIXEL_DEN',
							'Max Pixel Intensity':'MAX_PIXEL_DEN','Min Pixel Intensity':'MIN_PIXEL_DEN' 
							}

		featureList = ['Area', 'Perimeter', 'Roundness', 'Equi-Diameter','Orientation', 
						'Convex Area', 'Solidity', 'Major Axis', 'Minor Axis',
						'Eccentricity','Min Enclosing Rad','Shape Index','Border Index','Aspect Ratio',
						'Mean Pixel Intensity','Max Pixel Intensity', 'Min Pixel Intensity']

		################ defining features for clustering algorithm ################


		################ Adding File Open Dialog to Show the tiles Info ################ 

		self.chooseImagePanel = wx.Panel(self.sidePanel, -1)
		box = wx.StaticBox(self.chooseImagePanel, -1, 'Choose Image')
		self.subPanel = wx.Panel(self.chooseImagePanel, -1)

		sizer = wx.BoxSizer(wx.VERTICAL)
		self.filebrowser = filebrowse.FileBrowseButtonWithHistory(
							self.subPanel, -1, size=(450, -1), changeCallback = self.updateHistory)

		button = wx.Button(self.subPanel, -1, "View Image")
		button.Bind(wx.EVT_BUTTON, self.viewImage)

		sizer.Add(self.filebrowser,0,wx.EXPAND)
		sizer.Add(button,0,wx.ALL|wx.RIGHT|wx.ALIGN_RIGHT,5)
		self.subPanel.SetSizer(sizer)

		sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		sizer.Add(self.subPanel)
		self.chooseImagePanel.SetSizer(sizer)

		################ Adding File Open Dialog to Show the tiles Info ################ 

		################ Adding Algorithm Options Info ################ 

		self.algorithmPanel = wx.Panel(self.sidePanel, -1)
		box = wx.StaticBox(self.algorithmPanel, -1, 'Algorithms')
		self.subPanel = wx.Panel(self.algorithmPanel, -1)
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.algorithm1 = wx.RadioButton(self.subPanel, label="K-MEANS", style = wx.RB_GROUP)		
		self.algorithm2 = wx.RadioButton(self.subPanel, label="OPTICS")
		self.algorithm1.Bind(wx.EVT_RADIOBUTTON, self.kmeansSelected)
		self.algorithm2.Bind(wx.EVT_RADIOBUTTON, self.opticsSelected)

		sizer.Add(self.algorithm1 ,0,wx.ALL|wx.RIGHT|wx.ALIGN_LEFT, 5)
		sizer.Add((1,1),1)
		sizer.Add((1,1),1)
		sizer.Add(self.algorithm2 ,1,wx.ALL|wx.RIGHT|wx.ALIGN_RIGHT,5)
		self.subPanel.SetSizer(sizer)

		sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		sizer.Add(self.subPanel)
		self.algorithmPanel.SetSizer(sizer)

		################ Adding Algorithm Options Info ################ 

		################ Adding Features Panel ################ 

		self.featuresPanel = wx.Panel(self.sidePanel, -1)
		box = wx.StaticBox(self.featuresPanel, -1, 'Features')
		self.subPanel = wx.Panel(self.featuresPanel, -1)
		sizer = wx.GridSizer(rows = 6, cols = 3)

		global featureCB

		for feature in featureList:
			cb = wx.CheckBox(self.subPanel, label=feature)
			cb.Bind(wx.EVT_CHECKBOX, self.featuresSelected)
			featureCB[feature] = cb
			sizer.Add(cb, 0, wx.BOTTOM|wx.LEFT, 2)
		
		self.subPanel.SetSizer(sizer)

		sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
		sizer.Add(self.subPanel)
		self.featuresPanel.SetSizer(sizer)

		################ Adding Features Panel ################ 

		################ Adding Feature1, Feature2 Range Value ################ 

		self.feature1 = makeSP('FEATURE 1 RANGES',
							  (('Minimum', 1, 1, 3600),
								('Maximum', 1, 3600, 3600)))

		self.feature2 = makeSP('FEATURE 2 RANGES',
							  (('Minimum', 1, 1, 3600),
								('Maximum', 1, 3600, 3600)))

		################ Adding Feature1, Feature2 Range Value ################ 

		################ Adding all the panels to the main window ################ 

		self.optionPanel = OptionsPanel(self,self.sidePanel, self.displayPanel)
		self.buttonStart = wx.Button(self.sidePanel, -1, "Start")
		self.buttonStart.Bind(wx.EVT_BUTTON, self.startProcess)

		buttonClose = wx.Button(self.sidePanel, -1, "Close")
		buttonClose.Bind(wx.EVT_BUTTON, self.stopProcess)

		self.buttonGenerate = wx.Button(self.sidePanel, -1, "Generate Image")
		self.buttonGenerate.Bind(wx.EVT_BUTTON, self.generateImage)
		self.buttonReset = wx.Button(self.sidePanel, -1, "Show Image/Reset")
		self.buttonReset.Bind(wx.EVT_BUTTON, self.resetProcess)

		self.feature1.Enable(False)
		self.feature2.Enable(False)
		self.buttonStart.Enable(False)
		self.buttonGenerate.Enable(False)
		self.algorithmPanel.Enable(False)
		self.optionPanel.Enable(False)
		self.buttonReset.Enable(False)

		panelSizer = wx.BoxSizer(wx.VERTICAL)
		panelSizer.Add(self.chooseImagePanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.featuresPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.feature1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.feature2, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.algorithmPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		panelSizer.Add(self.optionPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(self.buttonStart ,0,wx.ALL|wx.RIGHT|wx.ALIGN_LEFT, 5)
		# sizer.Add((1,1),1)
		sizer.Add(self.buttonGenerate ,0,wx.ALL|wx.RIGHT|wx.ALIGN_CENTER,5)
		# sizer.Add((1,1),1)
		sizer.Add(self.buttonReset,0,wx.ALL|wx.RIGHT|wx.ALIGN_CENTER,5)
		
		sizer.Add(buttonClose ,0,wx.ALL|wx.RIGHT|wx.ALIGN_RIGHT,5)

		panelSizer.Add(sizer,0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		# panelSizer.Add(buttonStart, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
		# panelSizer.Add(buttonClose, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
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

		################ Adding all the panels to the main window ################

	################################################################################# 
	# featureSelected - event handler called when the feature check box is selected #
	#################################################################################
	
	def featuresSelected(self,event):
		if event.IsChecked():
			self.selectedFeaturesCount += 1
			if self.selectedFeaturesCount > 1 :
				self.optionPanel.Enable(True)
				self.algorithmPanel.Enable(True)
				self.buttonGenerate.Enable(True)
				self.buttonReset.Enable(True)
				self.feature1.Enable(True)
				self.feature2.Enable(True)
				if (self.algorithm1.GetValue()):
					self.buttonStart.Enable(True)

			if self.selectedFeaturesCount == 1:
				self.feature1.Enable(True)
				for key in featureCB.keys():
					if featureCB[key].GetValue() and key == "Mean Pixel Intensity":
						self.optionPanel.Enable(True)
						self.algorithmPanel.Enable(True)
						self.buttonGenerate.Enable(True)
						self.buttonStart.Enable(True)
						print key

		else:
			self.selectedFeaturesCount -= 1
			if self.selectedFeaturesCount <=1 :
				self.optionPanel.Enable(False)
				self.algorithmPanel.Enable(False)
				self.buttonStart.Enable(False)
				self.buttonGenerate.Enable(False)
				self.buttonReset.Enable(False)						
				self.feature1.Enable(False)
				self.feature2.Enable(False)
				self.axes.clear()
				self.canvas.draw()
			if self.selectedFeaturesCount == 1:
				for key in featureCB.keys():
					if featureCB[key].GetValue() and key == "Mean Pixel Intensity":
						self.optionPanel.Enable(True)
						self.algorithmPanel.Enable(True)
						self.buttonGenerate.Enable(True)
						self.buttonStart.Enable(True)
						print key
				self.feature1.Enable(True)


	def OnSpinback(self, name, value):
		if verbose:
			print 'On Spin Back', name, value



	################################################
	# stopProcess - event handler for close button #
	################################################
	
	def stopProcess(self,event):
		closeConnBaseDB()
		sys.exit()


	############################################################
	# resetProcess - event handler for reset/show image button #
	############################################################

	def resetProcess(self,event):
		self.axes.clear()
		self.canvas.draw()
		self.pointToPick = int(self.optionPanel.textBox.GetValue())
		if self.algorithm1.GetValue():
			self.buttonStart.Enable(True)
		else:
			self.buttonStart.Enable(False)

		featureList = []
		for key in featureCB.keys():
			if featureCB[key].GetValue():
				featureList.append(key)

		print featureList
		self.filename = self.filebrowser.GetValue().split('/')[-1].split('.')[0]
		self.fullFilename = self.filebrowser.GetValue()
		datalist = getFeatures(self.filename, self.dictionary[featureList[0]],
					 self.dictionary[featureList[1]])
		self.data = vstack([(f1,f2) for (f,n, f1, f2) in datalist])
		self.init_plot(self.data, self.k, featureList[0], featureList[1])
		self.centroids = []
		
	#####################################################################################
	# updateHistory - event handler for file open dialog to store recently opened files #
	#####################################################################################

	def updateHistory(self, event):

		self.featuresPanel.Enable(True)
		value = self.filebrowser.GetValue()
		print 'Update History',value
		if not value:
			return
		history = self.filebrowser.GetHistory()
		if value not in history:
			history.append(value)
			self.filebrowser.SetHistory(history)
			self.filebrowser.GetHistoryControl().SetStringSelection(value)


	##################################################################
	# viewImage - event handler for View Image button which displays #
	# 			  the image selected in the open dialog  #
	##################################################################
	def viewImage(self,event):
		print 'View Image'
		imageFile = self.filebrowser.GetValue()
		print imageFile
		win = wx.Frame(None, title = imageFile, size=(500,500), 
						style = wx.DEFAULT_FRAME_STYLE ^wx.RESIZE_BORDER) 
		ipanel = wx.Panel(win, -1)

		image = wx.ImageFromBitmap(wx.Bitmap(imageFile))
		image = image.Scale(500,500, wx.IMAGE_QUALITY_HIGH)
		bitmap = wx.BitmapFromImage(image)

		control = wx.StaticBitmap(ipanel,-1,bitmap)
		control.SetPosition((10,10))
		win.Show(True)


	#################################################################
	# generateImage - event handler for Generate Image image button #
	#################################################################

	def generateImage(self,event):
		print 'generate Image'
		self.generate_image()

	##############################################################################
	# generate_image -  method for generating an image of the tiles	   	     #
	#		    with mapping of clustered output i.e. each		     #
	#		    cluster is mapped in the tile image with specific colors # 
	##############################################################################

	def generate_image(self):
	#Red,Green,Blue,Marooon,Cyan,Yellow,Magenta,Purple,Navy,Gray(BGR format NOT RGB)
		#colors = {0:(0,0,255),1:(0,255,0),2:(255,0,0),3:(0,0,128),4:(255,255,0),5:(0,255,255),6:(255,0,255),7:(128,0,128)
		#		,8:(128,0,0),9:(128,128,128)}
		colors = [(0,0,255), (0,255,0), (255,0,0)]
		for i in range(self.k):
			colors.append((random.choice(range(256)), random.choice(range(256)),random.choice(range(256))))
		conn = getConnBaseDB()
		#Query DB to get boundary values for this image.
		c = conn.cursor()
		c.execute("SELECT BOUNDARY_VALS FROM Features WHERE IMAGE_NAME = '%s'" %self.filename)
		rows = c.fetchall()
		contour_list = []
		for row in rows:
			boundary_vals = row[0].strip().split(';')
			boundary_vals.pop()
			boundary_vals = [[int(float(n)) for n in i.split(',')] for i in boundary_vals]
			contr = np.array(boundary_vals)
			contour_list.append(contr)
		im = cv2.imread(self.fullFilename)
		for index,i in enumerate(self.clusterIds):
			cv2.drawContours(im,contour_list,index,colors[i],-1)

		outputfile = "Output_"+self.filename+"_clustered_"+str(int(time.time()))+".tif"
		cv2.imwrite(outputfile,im);
		cv2.imshow('image',im)
		cv2.waitKey()
		#closeConnBaseDB()
		#return(im)



	######################################################################
	# pickInputCentroids -  method for indicating whether to pick intial #
	#			centroids or not 			     #
	######################################################################

	def pickInputCentroids(self,userCentroid):
		self.pointToPick = int(self.optionPanel.textBox.GetValue())
		if userCentroid:
			self.buttonStart.Enable(False)
		else:
			self.buttonStart.Enable(True)


	##########################################################################
	# opticsSelected - radio button event for selecting OPTICS algortithm 	 #
	##########################################################################
	def opticsSelected(self,event):
		self.optionPanel.showUpdates.Enable(False)
		self.optionPanel.chooseCentroid.Enable(False)
		self.buttonStart.Enable(True)


	#######################################################################
	# kmeansSelected -  adio button event for selecting KMEANS algortithm #
	#######################################################################
	def kmeansSelected(self,event):
		self.optionPanel.showUpdates.Enable(True)
		self.optionPanel.chooseCentroid.Enable(True)
		if self.optionPanel.chooseCentroid.GetValue() and self.pointToPick == 0:
			self.buttonStart.Enable(True)
		elif not self.optionPanel.chooseCentroid.GetValue():
			self.buttonStart.Enable(True)
		


	######################################################################
	# onGraphClick -  mouse click event handler for selecting intial set #
	#				   of centroids from user  	     #
	######################################################################
	def onGraphClick(self,event):
		print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
			event.button, event.x, event.y, event.xdata, event.ydata)

		print self.optionPanel.chooseCentroid.GetValue()
		print self.pointToPick

		if self.optionPanel.chooseCentroid.GetValue() and self.pointToPick > 0:
			self.pointToPick -= 1
			#self.axes.plot(event.xdata,event.ydata, color='b',picker=5)
			self.axes.plot(event.xdata,event.ydata,color='r', marker='H',markersize=20.0,picker=5)
			self.canvas.draw()
			self.centroids.append([event.xdata,event.ydata])
			#np.concatenate((self.centroids,[event.xdata,event.ydata]))
			if self.pointToPick == 0 :
				self.buttonStart.Enable(True)



	######################################################################
	# onNucleiPick -  mouse click event handler for showing the metadata #
	#				  of selected nuclei 		     #
	######################################################################
	def onNucleiPick(self,event):
		thisline = event.artist
		xdata = thisline.get_xdata()
		ydata = thisline.get_ydata()
		ind = event.ind
		featureList = []
		featureKeys = featureCB.keys()
		for key in featureCB.keys():
			if featureCB[key].GetValue():
				featureList.append(key)
	
		print "xdata",xdata[ind][0]
		print "ydata",ydata[ind][0]
	
		dataList = getAllFeatures(self.filename, self.dictionary[featureList[0]],
			self.dictionary[featureList[1]],float(xdata[ind][0]),float(ydata[ind][0]));
		
		print dataList
		data = dataList[0]
		print len(data)
		win = wx.Frame(None, title = 'Nuclei Metadata', size=(500,500),
                                                style = wx.DEFAULT_FRAME_STYLE ^wx.RESIZE_BORDER)
		
		print "Creating New Frame"
		sizer = wx.GridSizer(rows = len(data), cols=2)	
		ipanel = wx.Panel(win, -1)
		for i in range (0,len(data)):
			label = wx.StaticText(ipanel, -1, featureKeys[i])
			sizer.Add(label, 0, wx.BOTTOM|wx.LEFT, 2)
			labCtrl = wx.TextCtrl(ipanel, -1, str(data[i]), style = wx.TE_READONLY)
			sizer.Add(labCtrl, 0, wx.BOTTOM|wx.LEFT, 2)
		ipanel.SetSizer(sizer)
		boxSizer = wx.BoxSizer(wx.VERTICAL)
		boxSizer.Add(ipanel)
		win.SetSizer(boxSizer)
		win.Fit()	
		win.Show(True)


	###########################################################################
	# startProcess -  event handler for start button 			  #
	#		  It initiates the process of clustering  		  #
	###########################################################################		
	def startProcess(self, event):
		print 'in kmeans'
		featureList =[]
		isShowUpdate = False
		k = self.optionPanel.textBox.GetValue()
		isShowUpdate = self.optionPanel.showUpdates.GetValue()
		isKmeans = self.algorithm1.GetValue()
		isOptics = self.algorithm2.GetValue()
		self.isPickCentroids = self.optionPanel.chooseCentroid.GetValue()

		print 'spin_panels', spinPanels.keys()
		for key in featureCB.keys():
			if featureCB[key].GetValue():
				featureList.append(key)
				print featureCB[key].GetValue()

		print "Feature List = ",featureList
		print "k-value = ",k
		print "Show Update = ",isShowUpdate
		print "Kmeans Selected= ",isKmeans
		print "OPTICS Selected= ",self.algorithm2.GetValue()

		self.buttonReset.Enable(True)
		self.buttonStart.Enable(False)

		for key in spinPanels.keys():
			print self.feature1.rangeValue[key].sc.GetValue()
			print self.feature2.rangeValue[key].sc.GetValue()

		print self.filebrowser.GetValue()
		self.filename = self.filebrowser.GetValue().split('/')[-1].split('.')[0]
		self.fullFilename = self.filebrowser.GetValue()
		if isKmeans:	
			#start the kmean process
			self.k = int(k)
			if not 'Mean Pixel Intensity' in featureList and len(featureList) > 2:
				print 'Performing kmeans for multiple features'
				fList = []
				for item in featureList:
					fList.append(self.dictionary[item])

				dataList = getFeaturesList(self.filename,fList)
				print dataList
				
				list1 = []
				list2 = []
				for index,j in enumerate(fList):
					list1.append('f'+str(index))
				
				list2 = ['f','n'] + list1
				new_list = [map(float,list2[2:])  for list2 in dataList]
				#new_list = [(float(j) for j in i)for i in new_list]
					
				print "new_list",new_list
				#self.data = vstack([list1  for list2 in dataList])
				self.data = vstack(new_list)
				#print self.data	
				self.init_plot(self.data, self.k, featureList[0], featureList[1])
				self.cluster_kmeansMul(fList, self.k, False)

			elif not 'Mean Pixel Intensity' in featureList and len(featureList) == 2:
				print self.filename
				datalist = getFeatures(self.filename, self.dictionary[featureList[0]],
							 self.dictionary[featureList[1]])
				#print datalist
				self.data = vstack([(f1,f2) for (f,n, f1, f2) in datalist])
				#Intial clusters from selecting points -- start


				#Intial clusters from selecting points -- end
				self.animation = isShowUpdate
				self.init_plot(self.data, self.k, featureList[0], featureList[1])
				time.sleep(1)
				if not self.animation:
					self.cluster_kmeans(datalist, self.k, False)
				else:
					print "isPickCentroids =",self.isPickCentroids
					print "initial centroisds = ", self.centroids
					if not self.isPickCentroids:
						self.centroids = self.init_cluster()
					self.iterTimer = 0
					self.redraw_timer.Start(2)
			else:
				self.data = vstack(self.helper_mean())
				self.pixel_kmeans()
		elif isOptics:
			print 'Calling OPTICS'
			self.gen_optic_cluster(featureList[0], featureList[1])
		else:
			print 'Select an algorithm'



	######################################################################
	# gen_optic_cluster -  method for executing OPTICS algorithm 	     #
	######################################################################

	def gen_optic_cluster(self, f1, f2):
		# generate some spatial data with varying densities
		np.random.seed(0)
		con = getConnBaseDB()
		X = []
		cur = con.cursor()
		stuple = (self.filename,)
		cur.execute("SELECT "+self.dictionary[f1]+", "+self.dictionary[f2]+" FROM Features WHERE IMAGE_NAME = '%s'" % stuple)
		rows = cur.fetchall()
		for row in rows:
			X.append([row[0], row[1]])
		print len(X)
		#plot scatterplot of points
		X = np.asarray(X)
		self.data = X
		#fig = plt.figure()
		#ax = fig.add_subplot(111)
		self.axes.clear()
		self.xlabel = f1
		self.ylabel = f2
		self.axes.set_xlabel(self.xlabel)
		self.axes.set_ylabel(self.ylabel)
		self.axes.set_title('Intial scatter plot before clustering')
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		self.axes.plot(X[:,0], X[:,1], 'bo')
		self.canvas.draw()
		#plt.savefig('Graph.png', dpi=None, facecolor='w', edgecolor='w',
		#	orientation='portrait', papertype=None, format=None,
		#	transparent=False, bbox_inches=None, pad_inches=0.1)
		#plt.show()



		#run the OPTICS algorithm on the points, using a smoothing value (0 = no smoothing)
		RD, CD, order = OP.optics(X,9)

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
		#fig = plt.figure()
		#ax = fig.add_subplot(111)
		self.axes.clear()
		self.xlabel = f1
		self.ylabel = f2
		self.axes.set_xlabel(self.xlabel)
		self.axes.set_ylabel(self.ylabel)
		self.axes.set_title('Final clusters formed')
		pylab.setp(self.axes.get_xticklabels(), fontsize=8)
		pylab.setp(self.axes.get_yticklabels(), fontsize=8)
		self.axes.plot(X[:,0], X[:,1], 'yo')
		#colors = cycle('gmkrcbgrcmk')
		colors = ['r','g','b']
		colors.extend([(random.random(), 
			random.random(), random.random()) for i in range(len(leaves)-3)])
		for item, c in zip(leaves, colors):
				node = []
				for v in range(item.start,item.end):
					node.append(RPoints[v])
				node = np.array(node)
				self.axes.plot(node[:,0],node[:,1], color=c,marker='o',linestyle='None',picker=5)
		self.canvas.draw()
		#plt.savefig('Graph2.png', dpi=None, facecolor='w', edgecolor='w',
			#orientation='portrait', papertype=None, format=None,
			#transparent=False, bbox_inches=None, pad_inches=0.1)
		#plt.show()


	############################################################################
	# pixel_kmeans -  method for executing kmeans algorithm for image related  #
	#				  features (mean pixel density). 	   #
	############################################################################
	def pixel_kmeans(self, feature1Bound=None,
						feature2Bound=None,iter=None):
		random.seed(time.time())
		self.centroids,_ = kmeans2(self.data, self.k)
		print len(self.centroids)
		self.clusterIds,_ = vq(self.data,self.centroids)
		sets = set(self.clusterIds)
		print sets
		self.generate_image()
		#TODO: If initial centroid not given only
		#self.centroids,_ = kmeans2(self.data, self.k, thresh=1e-05, minit='random')
		#lastCentroids = None
		#print self.centroids
		#print '\n'
		#i = 0
		#while not array_equal(lastCentroids,self.centroids) and i < self.iterations:
		#	i+=1
		#	lastCentroids = vstack(list(self.centroids)[:])
		#	self.centroids,_ = kmeans2(self.data, lastCentroids, iter=1, thresh=1e-05, minit='matrix')
		#	self.clusterIds,_ = vq(self.data,self.centroids)
		#self.redraw(-1)
		#print i, self.iterations
		#print self.centroids


	#######################################################################
	# helper_mean -  helper method for getting mean pixel density feature #
	#				 data for clustering.  	 	      #
	#######################################################################
	def helper_mean(self):
		conn = getConnBaseDB()
		c = conn.cursor()
		c.execute("SELECT MEAN_PIXEL_DEN FROM Features WHERE IMAGE_NAME = '%s'" %self.filename)
		rows = c.fetchall()
		data_list = []
		for row in rows:
			item = str(row[0])
			match = re.search(r'\((.*)\)',item)
			if match:
				data = match.group(1).split(',')
				data_list.append(data)
		data_list = [[float(j) for j in i ] for i in data_list]			
		#dbsetup.closeConnBaseDB()
		return data_list


	#######################################################################
	# init_cluster -  method for getting the initial set of centroids for #
	#				  kmeans CLUSTERING		      #
	#######################################################################
	def init_cluster(self):
		print "init_cluster function"
		centroids,_ = kmeans2(self.data, self.k, iter=1, thresh=1e-05, minit='random')
		return centroids


	######################################################################
	# timer_kmeans - method performs kmeans clustering and is invoked    #
	#		 when show updates option is enabled		     #
	######################################################################
	def timer_kmeans(self):
		lastCentroids = vstack(list(self.centroids)[:])
		print "timer Kmeans"
		print "last Centroids", lastCentroids
		self.centroids,_ = kmeans2(self.data, lastCentroids, iter=1, thresh=1e-05, minit='matrix')
		self.clusterIds,_ = vq(self.data,self.centroids)
		self.redraw(self.iterTimer)
		return array_equal(lastCentroids,self.centroids)


	#############################################################################
	# on_redraw_timer - method for calling the plot method to draw the clusters #
	#		    during each update in kmeans process 		    #
	#		    Called only when show updates method is selected 	    #
	#############################################################################
	def on_redraw_timer(self, event):
		print "self.iterTimer",self.iterTimer
		if self.iterTimer < self.iterations:
			changed = self.timer_kmeans()
			self.iterTimer+=1
			if self.iterTimer == self.iterations-1 or changed:
				self.redraw_timer.Stop()
				#self.redraw(self.data,self.centroids, clusterIds, self.k, -1)
				self.redraw(-1)



	#######################################################################
	# init_plot -  method for displaying the intial plot of the data with #
	#			   selected features.			      #
	#######################################################################
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




	#############################################################################
	# cluster_kmeansMul -  method performing kmeans for more than two features  # 
	#			selected and writes the cluster output to text file # 
	#############################################################################
	def cluster_kmeansMul(self, featureList,feature1Bound=None,
						feature2Bound=None,iter=None):
		random.seed(time.time())
		outputfile = "Output.txt"
		fh = open(outputfile, "w")
		
		print "In cluster_kmeansMul"	
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
		
		print i, self.iterations
		print self.centroids

		fh.write("Iteration Number --------->" + str(i))
		fh.write("Current Centroids --------->\n")
		print type(self.centroids.tolist())
		fh.write(str(self.centroids.tolist()))
		fh.write("Current clusters formed\n")
		for j in range(self.k):
			fh.write("Data points of cluster "+str(j)+"\n")
			for l in range(len(self.data)):
				if self.clusterIds[l] == j:
					fh.write(str(self.data[l])+"\n")
		#fh.write(str(self.clusterIds.tolist()))
		print self.data
		fh.close()
		print 'done'
		self.redraw(-1)
		



	########################################################################
	# cluster_kmeans -  method performing kmeans algorithm on data for     #
	#					selected features. This called if two features are #
	#					selected.										   #
	########################################################################

	def cluster_kmeans(self, feature1Bound=None,
						feature2Bound=None,iter=None):
		random.seed(time.time())
		#TODO: If initial centroid not given only
		print "Are initial centroid given::",self.isPickCentroids
		print "Initial Centroids Are ", self.centroids
		if not self.isPickCentroids:
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


	#####################################################################
	# redraw - method for invoking actual plot drawing module			#
	#####################################################################
	def redraw(self, iteration):
		 wx.CallAfter(self.redraw_actual, iteration)



	######################################################################
	# redraw_actual -   method for plotting the cluster output onto the  #
	#					scatter plot and display the number of clusters  #
	#					alomg with the centroids. 						 #	
	######################################################################
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
			self.axes.plot(self.data[self.clusterIds==i,0],self.data[self.clusterIds==i,1],color=self.colors[i],marker='o',linestyle='None',picker=5)
			self.axes.plot(self.centroids[i,0],self.centroids[i,1],color=self.colors[i], marker='H',markersize=20.0,picker=5)
		#for i in range(len(self.data)):  
			#self.axes.plot([self.data[i,0],self.centroids[self.clusterIds[i],0]],[self.data[i,1],self.centroids[self.clusterIds[i],1]], color=self.colors[self.clusterIds[i]],picker=5)
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




