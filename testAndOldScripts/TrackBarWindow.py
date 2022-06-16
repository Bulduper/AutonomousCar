import cv2

class TrackBarWindow:
	defaultWindowName = "Trackbars"
	
	
	def __init__(self,properties):
		self.properties = properties
		cv2.namedWindow(self.defaultWindowName)
		cv2.resizeWindow(self.defaultWindowName,320,240)
		for prop in properties:
			cv2.createTrackbar(prop[0],self.defaultWindowName,prop[1],prop[2],self.empty)
			print('New trackbar named',prop[0],'startVal',prop[1],'maxVal',prop[2])
		
	def empty(self,a):
		pass
		
	def getValues(self):
		trackBarResults = []
		for prop in self.properties:
			trackBarResults.append(cv2.getTrackbarPos(prop[0],self.defaultWindowName))
		return trackBarResults
