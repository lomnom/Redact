import wx

class Censor(wx.Frame):
	def __init__(self):
		style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
				  wx.NO_BORDER | wx.FRAME_SHAPED  )
		wx.Frame.__init__(self, None, title='Censor', style = style)
		self.dragPos = None
		self.Bind(wx.EVT_KEY_UP, self.OnKeyDown)
		self.Bind(wx.EVT_MOTION, self.OnMouse)
		self.Show(True)
		self.SetSize((50, 50))
		self.SetPosition((50,50))

	def OnKeyDown(self, event):
		event.Skip() # Ignore keyboard inputs.

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

			if size.width >= 30:
				rSize = 10 # Width of a region in the right side
			else:
				rSize = 5
			if size.width-rSize <= mouse.x <= size.width: # Right side shrink
				newSize.width = size.width - 10
			elif size.width - (2*rSize) <= mouse.x <= size.width-rSize: # Right side expand
				newSize.width = size.width + 10

			if size.height >= 30:
				bSize = 10 # Width of a region in the bottom side
			else:
				bSize = 5
			if size.height-bSize <= mouse.y <= size.height: # Bottom side shrink
				newSize.height = size.height - 10
			elif size.height - (2*bSize) <= mouse.y <= size.height-bSize: # Bottom side expand
				newSize.height = size.height + 10

			if newSize.height < 20:
				newSize.height = 20
			if newSize.width < 20:
				newSize.width = 20
			self.SetSize(newSize)

app = wx.App()
f = Censor()
app.MainLoop()