import wx

class Censor(wx.Frame):
	def __init__(self):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
				  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title='Censor', style = style)
		self.dragPos = None
		self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
		self.Bind(wx.EVT_MOTION, self.OnMouse)
		self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnterWindow)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeaveWindow)
		self.Show(True)

		height = 50
		width = 50
		self.SetSize((height, width))

		screenSize = wx.DisplaySize() # Place at center of screen
		self.SetPosition((screenSize[0]//2 - width//2, screenSize[1]//2 - height//2))

		self.minSize = 20 # Minimum height & width
		self.insideBox = None # If the cursor is inside the box for the long term, not just entering to shrink
		self.lastShrinking = None # Used if shrinking overrun

	def OnKeyUp(self, event):
		event.Skip() # Ignore keyboard inputs.

	def getRegionSize(self, size):
		if size.width >= 30: rSize = 20 # Width of a region in the right side
		elif size.width > 20: rSize = 10
		else: rSize = 5

		if size.height >= 30: bSize = 20 # Width of a region in the bottom side
		elif size.height > 20: bSize = 10
		else: bSize = 5
		return (rSize, bSize)

	def OnEnterWindow(self, event):
		insideBox = True # Note: Fix bug where cursor teleports into the box.
		size = self.GetSize()
		newSize = self.GetSize()
		mouse = event.GetPosition()
		rSize, bSize = self.getRegionSize(size)

		#Bottom right square
		if size.width - rSize <= mouse.x <= size.width and size.height - bSize <= mouse.y <= size.height:
			insideBox = False
			print("Little square!")
			pass # TODO: handler which teleports cursur a little away.
		else:
			if size.width-rSize <= mouse.x <= size.width: # Right side shrink
				newSize.width = size.width - 10
				insideBox = False
				self.lastShrinking = 'r'
			elif size.height-bSize <= mouse.y <= size.height: # Bottom side shrink
				newSize.height = size.height - 10
				insideBox = False
				self.lastShrinking = 'b'

		self.insideBox = insideBox
		self.SetSize((max(self.minSize, newSize.width), max(self.minSize, newSize.height)))

	def OnLeaveWindow(self, event):
		insideBox = False
		size = self.GetSize()
		newSize = self.GetSize()
		mouse = event.GetPosition()
		rSize, bSize = self.getRegionSize(size)

		if self.insideBox: # Ignore leaving window in shrinking & ignore leaving the bottom right square
			if size.width - rSize <= mouse.x: # Right side expand
				newSize.width += 50
			if size.height - bSize <= mouse.y: # Bottom side expand
				newSize.height += 50

		self.SetSize((max(self.minSize, newSize.width), max(self.minSize, newSize.height)))
		self.insideBox = insideBox

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

			if size.height - bSize <= mouse.y <= size.height: # Bottom side expand
				newSize.height = size.height + 10
		else: # Handle shrinking overrun
			if self.lastShrinking == 'r':
				newSize.width -= 3 * (size.width-mouse.x) + 30
			elif self.lastShrinking == 'b':
				newSize.height -= 3 * (size.height-mouse.y) + 30

		self.SetSize((max(self.minSize, newSize.width), max(self.minSize, newSize.height)))

app = wx.App()
f = Censor()
app.MainLoop()