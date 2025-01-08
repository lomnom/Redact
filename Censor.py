import wx
import pyautogui as pag
from mss import mss # Screenshots
# from PIL import Image
from time import perf_counter as timePoint
pag.PAUSE = 0

NOTHINGFUNC = lambda *args, **kwargs: None
class Element: 
	def __init__(self, name, permeable = True):
		self.name = name
		self.permeable = permeable # If multiple elements will get the event or just this one
		for part in ["getRegion", "onClick", "onDrag", "render", "onDragEnd"]:
			self.newPart(part)

	# getRegion(self, frame) returns [x, y, h, w] within which it is considered to be within the element
	# onClick(self, frame, event) is called on a left click
	# onDrag(self, frame, event, previous, start, end, dragLength) is called after the first drag event.
	# onDragEnd(self, frame, event, previous, start, end, dragLength) is called at the end of a drag.
	# render(self, frame, dc) is called when to render the element when window is in focus.

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

	def __init__(self, x = None, y = None):
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

		if x is None and y is None:
			screenSize = wx.DisplaySize() # Place at center of screen
			self.SetPosition((screenSize[0]//2 - width//2, screenSize[1]//2 - height//2))
		else:
			self.SetPosition((x, y))

		self.dragStartPos = None
		self.dragLength = 0
		self.dragElements = None
		self.dragPrevPos = None

		# Update every second
		self.timer = wx.Timer(self) 
		self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
		self.timer.Start(1000)

		# self.mouseHover = False # If the mouse is currently hovering over the censor

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

	def OnTimer(self, event):
		self.Refresh()

	def OnPaint(self, event=None):
		startPoint = timePoint()
		dc = wx.PaintDC(self)
		dc.Clear()

		self.censors[self.currentCensor][1](self, event, self.buffer)
		dc.DrawBitmap(wx.Bitmap(self.buffer), 0, 0) # Commit the buffer

		# if self.HasFocus():
		# 	print("HAS FOCUS")
		# 	for element in self.elements:
		# 		element.render(self, dc)

		print(f"Render took {round(timePoint() - startPoint, 4)}s")

	def elementsHit(self, x, y):
		results = []
		for element in self.elements:
			sx, sy, h, w = element.getRegion(self)
			ex, ey = (sx + w, sy + h)
			if sx <= x < ex and sy <= y < ey:
				if not element.permeable:
					return [element]
				else:
					results.append(element)
		return results

	helpText = "Right click to change mode.\n" \
	           "Drag right or bottom sides to resize.\n" \
	           "Drag anywhere else to move.\n" \
	           "Click top left to close. \n" \
	           "Drag from the top left for another censor.\n" \
	           "@ https://github.com/lomnom/Redact"

	def OnMouse(self, event):
		event.GetEventObject().SetToolTip(self.helpText)
		# Moving the window
		spot = event.GetPosition()
		if event.Dragging():
			# print(f"Dragging, {spot}, {self.dragLength}, {self.dragElements}")
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
		if self.dragLength: # Ending a drag
			if not (spot == self.dragStartPos and self.dragLength == 1): # Unless it is a 0-pixel accidental drag
				for element in self.dragElements:
					element.onDragEnd(self, event, self.dragPrevPos, self.dragStartPos, spot, self.dragLength)
				return
		elementsHit = self.elementsHit(spot.x, spot.y)
		for element in elementsHit:
			element.onClick(self, event)

	def OnRightDown(self, event):
		self.currentCensor = (self.currentCensor + 1) % len(self.censors)
		print(f"Now using censor {self.currentCensor}, {self.censors[self.currentCensor][0]}")
		self.Refresh()

	# def OnEnterWindow(self, event):
	# 	self.mouseHover = True

	# def OnLeaveWindow(self, event):
	# 	self.mouseHover = False

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

manage = Element("Manage", permeable = False)
Censor.elements.append(manage)
@manage.getRegionCall
def getRegion(self, frame):
	return [0, 0, 10, 10]

@manage.onClickCall
def onClick(self, frame, event):
	print("Manage button pressed. Closing.")
	frame.Close()
	removeFrame(frame)

@manage.onDragEndCall
def onDragEnd(self, frame, event, previous, start, end, dragLength):
	framePos = frame.GetPosition()
	newFrame = Censor(x = framePos.x + end.x, y = framePos.y + end.y)
	addFrame(newFrame)
	print("New censor created.")

# Censors
@Censor.censor
def black(frame, event, buffer):
	buffer.Clear()

@Censor.censor
def white(frame, event, buffer):
	buffer.Clear(value = bytes([255]))

width, height = pag.size()
ssTaker = mss()
monitor = ssTaker.monitors[1]
def screenshot(x, y, h, w): 
	output = f"sct-{x}x{y}_{w}x{h}.png"
	sct_img = ssTaker.grab({"top": y, "left": x, "width": w, "height": h})
	# Image.frombytes('RGB', sct_img.size, sct_img.bgra, 'raw', 'BGRX').show()
	return (sct_img.raw, sct_img.size)

# REMEMBER
# The image is arranged as such:
# 1 2 3 4
# 5 6 7 8

offset = 1 # Distance from window to capture
@Censor.censor
def camouflage(frame, event, buffer): # TODO: make sure censor cannot clip out of screen
	framePos = frame.GetPosition()
	frameSize = frame.GetSize()
	buffer.Clear()

	top, topSize = screenshot(framePos.x, framePos.y - offset, 1, frameSize.width)
	bottom, _ = screenshot(framePos.x, framePos.y + frameSize.height + offset, 1, frameSize.width)

	left, leftSize = screenshot(framePos.x - offset, framePos.y, frameSize.height, 1)
	right, _ = screenshot(framePos.x + frameSize.width + offset, framePos.y, frameSize.height, 1)

	# Skip every leftsize.width th item to only get first row!!
	top, bottom, left, right = ((top, 1), (bottom, 1), (left, leftSize.width), (right, leftSize.width)) 

	ssScale = (leftSize.height) // frameSize.height # Compensate for 2x on retina displays
	def get(strip, pos): # Relative to window
		buffer, skip = strip
		pos *= ssScale * skip
		return (buffer[pos*4 + 2], buffer[pos*4 + 1], buffer[pos*4]) # (r, g, b)

	# The default margin specifies the distance where they are considered to be the same
	def closeEnough(ar, ag, ab, br, bg, bb, margin = 4):
		return abs(ar - br) + abs(ag - bg) + abs(ab - bb) <= margin

	# Detect congruence from top to bottom or left to right, and render those
	VERT, HORIZ = (False, True)
	regions = [] # [[VERT/HORIZ, start, end (so range(start, end))], ...]

	def getRegions(sideA, sideB, sideSize, axis, regions):
		pr, pg, pb = (-99, -99, -99) # Last colour
		lastMatches = False # If the last index matched both sides
		for pos in range(sideSize):
			ar, ag, ab = get(sideA, pos)
			br, bg, bb = get(sideB, pos)
			if closeEnough(ar, ag, ab, br, bg, bb):
				if lastMatches:
					if closeEnough(pr, pg, pb, ar, ag, ab): # Still within the current region
						pass
					else: # Match but chunk the region because its too different
						regions[-1][2] = pos # End the previous region here 
						regions.append([axis, pos, None]) # New region here
				else:
					regions.append([axis, pos, None]) # New region

				lastMatches = True
				pr, pg, pb = ar, ag, ab
			else:
				if lastMatches: # End region
					regions[-1][2] = pos
				else:
					pass # This is the empty case
				lastMatches = False
		if regions and regions[-1][2] is None:
			regions[-1][2] = sideSize
	getRegions(top, bottom, frameSize.width, HORIZ, regions)
	getRegions(left, right, frameSize.height, VERT, regions)

	regions.sort(key = lambda region: region[2] - region[1], reverse = True) # Sort by region length, big to small

	for region in regions:
		axis, start, end = region
		if axis == HORIZ:
			for x in range(start, end):
				r, g, b = get(top, x)
				for y in range(frameSize.height):
					buffer.SetRGB(x, y, r, g, b)
		elif axis == VERT:
			for y in range(start, end):
				r, g, b = get(left, y)
				for x in range(frameSize.width):
					buffer.SetRGB(x, y, r, g, b)

	# print(regions)

	# Why is there no better way
	bufferGet = lambda x, y: (buffer.GetRed(x, y), buffer.GetGreen(x, y), buffer.GetBlue(x, y))
	for x in range(frameSize.width):
		if bufferGet(x, 0) == (0, 0, 0): # Yes it may actually be black but eh
			buffer.SetRGB(x, 0, *get(top, x))
	for y in range(frameSize.height):
		if bufferGet(0, y) == (0, 0, 0): 
			buffer.SetRGB(0, y, *get(left, y))

	for y in range(1, frameSize.height):
		previous = bufferGet(0, y)
		for x in range(1, frameSize.width):
			here = bufferGet(x, y)
			if here == (0, 0, 0) and here != previous and here != bufferGet(x, y-1):
				buffer.SetRGB(x, y, previous[0], previous[1], previous[2])
				previous = previous
			else:
				previous = here

frames = []
def addFrame(frame):
	frames.append(frame)
def removeFrame(frame):
	frames.remove(frame)
	if len(frames) == 0:
		print("No frames left. exiting.")
		wx.Exit()

app = wx.App()
addFrame(Censor())
app.MainLoop()