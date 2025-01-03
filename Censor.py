import wx
import pyautogui as pag
pag.PAUSE = 0

NOTHINGFUNC = lambda *args, **kwargs: None
class Element: 
	def __init__(self, name):
		self.name = name
		for part in ["getRegion", "onClick", "onDrag", "render"]:
			self.newPart(part)

	# getRegion(self, frame) returns [x, y, h, w] within which it is considered to be within the element
	# onClick(self, frame, event) is called on a left click
	# onDrag(self, frame, event, previous, start, end, dragLength) is called after the first drag event.
	# render(self, frame, buffer) is called when to render the element when window is in focus.

	def newPart(self, name):
		setattr(self, '_'+name, NOTHINGFUNC)
		def newPartDecorator(func):
			nonlocal self, name
			setattr(self, '_'+name, func)

		def newPartCaller(*args, **kwargs): # Note: slow?
			nonlocal self, name
			return getattr(self, '_'+name)(self, *args, **kwargs)

		setattr(self, name+"Call", newPartDecorator)
		setattr(self, name, newPartCaller)

	def __repr__(self): # Not compliant but eh
		return "E-" + self.name

class Censor(wx.Frame):
	censors = []
	elements = []
	@classmethod
	def censor(cls, function):
		cls.censors.append([function.__name__, function])

	def __init__(self):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
				  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title='Censor', style = style)
		self.Bind(wx.EVT_MOTION, self.OnMouse)
		# self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
		# self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
		self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.Show(True)

		height = 50 # Initial dimensions
		width = 50

		self.currentCensor = 0 # Index of current censor

		self.minSize = 20 # Minimum height & width
		self.resize(wx.Size(height, width))

		screenSize = wx.DisplaySize() # Place at center of screen
		self.SetPosition((screenSize[0]//2 - width//2, screenSize[1]//2 - height//2))

		self.dragStartPos = None
		self.dragLength = 0
		self.dragElements = None
		self.dragPrevPos = None

	def resize(self, newSize):
		self.SetSize((max(self.minSize, newSize.width), max(self.minSize, newSize.height)))
		size = self.GetSize()
		self.buffer = wx.Image(size)
		self.rSize, self.bSize = self.getRegionSize(size)

	@staticmethod
	def regionSteps(dimension):
		if dimension >= 30: size = 20 
		elif dimension > 20: size = 10
		else: size = 5
		return size

	def getRegionSize(self, size):
		return (self.regionSteps(size.width), self.regionSteps(size.height))

	def OnPaint(self, event=None):
		dc = wx.PaintDC(self)
		dc.Clear()

		self.censors[self.currentCensor][1](self, event, self.buffer)
		if self.HasFocus():
			for element in self.elements:
				element.render(self, self.buffer)

		dc.DrawBitmap(wx.Bitmap(self.buffer), 0, 0) # Commit the buffer

	def elementsHit(self, x, y):
		results = []
		for element in self.elements:
			sx, sy, h, w = element.getRegion(self)
			ex, ey = (sx + w, sy + h)
			if sx <= x < ex and sy <= y < ey:
				results.append(element)
		return results

	def OnMouse(self, event):
		# Moving the window
		spot = event.GetPosition()
		if event.Dragging():
			print(f"Dragging, {spot}, {self.dragLength}, {self.dragElements}")
			self.dragLength += 1 # Number of drag events part of this drag, including this event
			if not self.dragStartPos: # First event
				self.dragStartPos = spot
				self.dragElements = self.elementsHit(spot.x, spot.y)
			else:
				for element in self.dragElements:
					element.onDrag(self, event, self.dragPrevPos, self.dragStartPos, spot, self.dragLength)
			self.dragPrevPos = spot
		else:
			self.dragStartPos = None
			self.dragElements = None
			self.dragLength = 0
			self.dragPrevPos = None

	def OnLeftUp(self, event):
		spot = event.GetPosition()
		if self.dragLength: # Ignore ending a drag
			if not (spot == self.dragStartPos and self.dragLength == 1): # Unless it is a 0-pixel accidental drag
				return
		elementsHit = self.elementsHit(spot.x, spot.y)
		for element in elementsHit:
			element.onClick(self, event)

	def OnRightDown(self, event):
		self.currentCensor = (self.currentCensor + 1) % len(self.censors)
		print(f"Now using censor {self.currentCensor}, {self.censors[self.currentCensor][0]}")
		self.OnPaint()

	# def OnEnterWindow(self, event):
	# 	pass

	# def OnLeaveWindow(self, event):
	# 	pass

# Let the frame be dragged around
drag = Element("Dragger")
Censor.elements.append(drag)
@drag.getRegionCall
def getRegion(self, frame):
	size = frame.GetSize()
	return [0, 0, size.height - frame.bSize, size.width - frame.rSize]

@drag.onDragCall
def onDrag(self, frame, event, previous, start, end, dragLength):
	delta = end - start
	oldPos = frame.GetPosition()
	frame.SetPosition(oldPos + delta)

rResize = Element(f"Right resize")
Censor.elements.append(rResize)
@rResize.getRegionCall
def getRegion(self, frame):
	size = frame.GetSize()
	return [size.width - frame.rSize, 0, size.height, frame.rSize]

@rResize.onDragCall
def onDrag(self, frame, event, previous, start, end, dragLength):
	delta = end - previous
	size = frame.GetSize()
	size.width += delta.x
	frame.resize(size)

# Very similar code
bResize = Element(f"Bottom resize")
Censor.elements.append(bResize)
@bResize.getRegionCall
def getRegion(self, frame):
	size = frame.GetSize()
	return [0, size.height - frame.bSize, frame.bSize, size.width]

@bResize.onDragCall
def onDrag(self, frame, event, previous, start, end, dragLength):
	delta = end - previous
	size = frame.GetSize()
	size.height += delta.y
	frame.resize(size)

close = Element("Close")
Censor.elements.append(close)
@close.getRegionCall
def getRegion(self, frame):
	return [0, 0, 10, 10]

@close.onClickCall
def onClick(self, frame, event):
	print("Close button pressed. Closing.")
	quit() # TODO: is this correct?

@Censor.censor
def black(frame, event, buffer):
	buffer.Clear()

@Censor.censor
def white(frame, event, buffer):
	buffer.Clear(value = bytes([255]))

app = wx.App()
f = Censor()
app.MainLoop()