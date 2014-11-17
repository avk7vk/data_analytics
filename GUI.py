#
#   TEAM #1 
#   CLUSTERING ALGOTRITHM GUI
#
#


import wx
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

        self.showUpdates = wx.CheckBox(self, label = "Enable Updates during Iteration")
        sizer.Add(self.showUpdates, 0, wx.BOTTOM|wx.LEFT, 2)

        def createColorButton(label):
            button = cs.ColourSelect(self, size=(20,22))
            label = wx.StaticText(self, -1, label)
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(button)
            sizer.Add((4,4))
            sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
            return sizer, button

        s, self.fg = createColorButton('Foreground')
        sizer.Add(s)
        s, self.bg = createColorButton('Background')
        sizer.Add(s)
        self.SetSizer(sizer)

        self.Bind(cs.EVT_COLOURSELECT, self.OnSetFG, self.fg)
        self.Bind(cs.EVT_COLOURSELECT, self.OnSetFG, self.bg)

    def OnSetFG(self, evt):
        self.display.SetForegroundColour(evt.GetValue())
        
    def OnSetBG(self, evt):
        self.display.SetBackgroundColour(evt.GetValue())
        
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
        value = self.st.GetValue()
        if verbose:
            print 'On Spin', name, '=', value
        self.callback(name,value)

class AppFrame(wx.Frame):

    def __init__(self):
        def makeSP(name, labels, statictexts = None):
            panel = wx.Panel(self.sidePanel, -1)
            box = wx.StaticBox(panel,-1, name)
            sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

            for name, min_value, value, max_value in labels:
                sp = SpinPanel(panel, name, min_value, value, max_value, self.OnSpinback)
                sizer.Add(sp, 0, wx.EXPAND)

            if statictexts:
                for name, text in statictexts:
                    st = wx.StaticText(panel, -1, text)
                    spin_panels[name] = st
                    sizer.add(st, 0, wx.EXPAND)

            panel.SetSizer(sizer)
            return panel

        wx.Frame.__init__(self, None, title = "CLUSTERING ALGORITHM")

        self.displayPanel = DisplayPanel(self)
        self.sidePanel = wx.Panel(self)

        featureList = ['area', 'perimeter', 'texture1', 'eccentricity', 
                        'feature5', 'feature6', 'feature7', 'feature8',
                        'feature9', 'feature10']

        self.featuresPanel = wx.Panel(self.sidePanel, -1)
        box = wx.StaticBox(self.featuresPanel, -1, 'Features')
        self.subPanel = wx.Panel(self.featuresPanel, -1)
        sizer = wx.GridSizer(rows = 5, cols = 2)

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

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.featuresPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        panelSizer.Add(self.feature1, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        panelSizer.Add(self.feature2, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        panelSizer.Add(self.optionPanel, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
        panelSizer.Add(button, 0, wx.EXPAND|wx.TOP|wx.LEFT|wx.RIGHT, 5)
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

    def startProcess(self, event):
        print 'in kmeans'
        #start the kmean process


verbose = 0
spinPanels = {}
featureCB = {}
app = wx.App(False)
AppFrame()
if verbose:
    print 'Features', featureCB.keys()
app.MainLoop()




