import jetson.inference
import jetson.utils
import time
#import cv2
import numpy as np


#net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)
camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                  "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
display = jetson.utils.videoOutput(
    "display://0", argv=["--output-height=480", "--output-width=640"])  # 'my_video.mp4' for file

x = 3
start_time = time.time()
counter = 0
imgOutput = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
img_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')

# def rotateImg(img, degrees=180):
#     center = (img.shape[1]//2, img.shape[0]//2)
#     M = cv2.getRotationMatrix2D(center, degrees, scale=1.0)
#     tim2 = time.time()
#     rotated = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
#     print(time.time()-tim2)
#     return rotated


while display.IsStreaming():
    img = camera.Capture()

    jetson.utils.cudaConvertColor(img, imgOutput)
    #jetson.utils.cudaResize(imgOutput,img_small)
    #tim1 = time.time()
    #img_np = jetson.utils.cudaToNumpy(img_small)
    #jetson.utils.cudaDeviceSynchronize()
    #img_np = cv2.resize(img_np,(640,480))
    #img_np = rotateImg(img_np)
    #print(time.time()-tim1)
    #cv2.imshow("window", img_np)
    # print(img.shape)
    #detections = net.Detect(img)
    # for detect in detections:
    # 	ID = detect.ClassID
    # 	item=net.GetClassDesc(ID)
    # 	print(item)
    display.Render(imgOutput)
    #keyCode = cv2.waitKey(1) & 0xFF
    # Stop the program on the ESC key
    # if keyCode == 27:
    #     break

    counter += 1
    if (time.time() - start_time) > x:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()
    # display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))
