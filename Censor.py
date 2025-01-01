import wx
import pyautogui as pag
pag.PAUSE = 0

class Censor(wx.Frame):
	censors = []
	@classmethod
	def censor(cls, function):
		cls.censors.append([function.__name__, function])

	def __init__(self):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
				  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title='Censor', style = style)
		self.dragPos = None
		self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.Bind(wx.EVT_MOTION, self.OnMouse)
		self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Show(True)

		height = 50 # Initial dimensions
		width = 50

		self.currentCensor = 0 # Index of current censor

		self.minSize = 20 # Minimum height & width
		self.resize(wx.Size(height, width))

		screenSize = wx.DisplaySize() # Place at center of screen
		self.SetPosition((screenSize[0]//2 - width//2, screenSize[1]//2 - height//2))

		self.insideBox = None # If the cursor is inside the box for the long term, not just entering to shrink
		self.lastChange = None # Used by shrinking overrun & checking expansion overrun

	def OnKeyUp(self, event):
		event.Skip() # Ignore keyboard inputs.

	def handleSquare(self):
		self.currentCensor = (self.currentCensor + 1) % len(self.censors)

	def OnPaint(self, event):
		self.censors[self.currentCensor][1](self, event)

	def resize(self, newSize, render = True):
		self.SetSize((max(self.minSize, newSize.width), max(self.minSize, newSize.height)))
		self.buffer = wx.Image(self.GetSize())

	def getRegionSize(self, size, bigger = False):
		# Width of a region in the right side
		if bigger and size.width >= 60: rSize = 40 
		elif size.width >= 30: rSize = 20 
		elif size.width > 20: rSize = 10
		else: rSize = 5

		# Width of a region in the bottom side
		if bigger and size.height >= 60: bSize = 40 
		elif size.height >= 30: bSize = 20 
		elif size.height > 20: bSize = 10
		else: bSize = 5
		return (rSize, bSize)

	def OnEnterWindow(self, event):
		if self.dragPos is not None: # Ignore everything which happens during a drag to avoid resizing
			return
		insideBox = True 
		size = self.GetSize()
		newSize = self.GetSize()
		mouse = event.GetPosition()
		rSize, bSize = self.getRegionSize(size, bigger = True) # Make it bigger to reduce overruns

		#Bottom right square
		if size.width - rSize <= mouse.x <= size.width and size.height - bSize <= mouse.y <= size.height:
			insideBox = False
			pag.move(rSize, bSize) # Teleport cursor away from the box
			self.handleSquare()
		else:
			if size.width-rSize <= mouse.x <= size.width: # Right side shrink
				newSize.width = size.width - 10
				insideBox = False
				self.lastChange = "r-"
				self.resize(newSize)
				print("Shrinking right")
			elif size.height-bSize <= mouse.y <= size.height: # Bottom side shrink
				newSize.height = size.height - 10
				insideBox = False
				self.lastChange = "b-"
				self.resize(newSize)
				print("Shrinking bottom")

		if insideBox:
			print("Now inside.")
		self.insideBox = insideBox

	def OnLeaveWindow(self, event):
		if self.dragPos is not None: # Ignore everything which happens during a drag to avoid resizing
			return
		size = self.GetSize()
		newSize = self.GetSize()
		mouse = event.GetPosition()
		rSize, bSize = self.getRegionSize(size)

		# Expansion overruns
		# Ignore if leaving window in shrinking & ignore if leaving the bottom right square
		# Last change must be an expansion or it is probably a late resize.
		if self.lastChange and self.lastChange[1] == '+' and self.insideBox: 
			if size.width - rSize <= mouse.x: # Right side expand overrun
				newSize.width += 60
				self.resize(newSize)
				print("Expansion overrun right")
			if size.height - bSize <= mouse.y: # Bottom side expand overrun
				newSize.height += 60
				self.resize(newSize)
				print("Expansion overrun bottom")

		self.insideBox = False

	def OnMouse(self, event):
		# Moving the window
		if event.Dragging():
			if not self.dragPos:
				self.dragPos = event.GetPosition()
			else:
				pos = event.GetPosition()
				displacement = self.dragPos - pos
				self.SetPosition(self.GetPosition() - displacement)
			return
		else:
			self.dragPos = None

		size = self.GetSize()
		newSize = self.GetSize()
		mouse = event.GetPosition()
		rSize, bSize = self.getRegionSize(size)
		if self.insideBox: # Expanding
			# Note that the bottom right square expands both from inside.
			if size.width - rSize <= mouse.x <= size.width: # Right side expand
				newSize.width = size.width + 10
				self.resize(newSize)
				self.lastChange = "r+"
				print("Growing right")
			if size.height - bSize <= mouse.y <= size.height: # Bottom side expand
				newSize.height = size.height + 10
				self.resize(newSize)
				self.lastChange = "b+"
				print("Growing bottom")
		else: # Shrinking extensions. TODO: Overruns where the cursor teleports past the trigger region are not handled.
			# TODO: Going in from the far right of the top side at an angle directly downwards causes a huge shrink
			if self.lastChange == "r-" and size.width != self.minSize:
				newSize.width -= 3 * (size.width-mouse.x) + 30
				self.resize(newSize)
				print("Shrink overrun right")
			elif self.lastChange == "b-" and size.height != self.minSize:
				newSize.height -= 3 * (size.height-mouse.y) + 30
				self.resize(newSize)
				print("Shrink overrun bottom")

@Censor.censor
def black(self, event):
	dc = wx.PaintDC(self)
	dc.Clear()
	size = self.GetSize()
	self.buffer.Clear()

	dc.DrawBitmap(wx.Bitmap(self.buffer), 0, 0)

app = wx.App()
f = Censor()
app.MainLoop()