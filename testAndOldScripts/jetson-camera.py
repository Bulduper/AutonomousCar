import jetson.inference
import jetson.utils
import time



#net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.videoSource("csi://0",argv=["--input-height=1232","--input-width=1640",  "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
display = jetson.utils.videoOutput("display://0",argv=["--output-height=1232","--output-width=1640"]) # 'my_video.mp4' for file

x=3
start_time = time.time()
counter = 0

while display.IsStreaming():
	img = camera.Capture()
	#print(img.shape)
	#detections = net.Detect(img)
	# for detect in detections:
	# 	ID = detect.ClassID
	# 	item=net.GetClassDesc(ID)
	# 	print(item)
	display.Render(img)
	counter+=1
	if (time.time() - start_time) > x :
		print("FPS: ", counter / (time.time() - start_time))
		counter = 0
		start_time = time.time()
	# display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
