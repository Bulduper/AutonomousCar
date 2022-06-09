# import cv2
# import numpy as np

# if __name__ == '__main__':
#     print('Hello motherfucker')
#     cap = cv2.VideoCapture('nvarguscamerasrc ! video/x-raw(memory:NVMM), width=3280, height=2464, format=(string)NV12, framerate=(fraction)20/1 ! nvvidconv ! video/x-raw, width=640, height=480, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink' , cv2.CAP_GSTREAMER)
#     while True:
#         _, frame = cap.read()

#         cv2.imshow('Okno',frame)

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
#     cap.release()

import cv2
import time

# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Defaults to 1280x720 @ 60fps
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of the window on the screen
from g_pipeline import gstreamer_pipeline

last_tim = 0.0
#display framerate every x seconds
x=3
start_time = time.time()
counter = 0
def show_camera():
    global last_tim,counter,start_time,x
    # To flip the image, modify the flip_method parameter (0 and 2 are the most common)
    print(gstreamer_pipeline(flip_method=0))
    cap = cv2.VideoCapture(gstreamer_pipeline(sensor_mode=1,framerate=20 ,flip_method=0,display_height=720,display_width=1280), cv2.CAP_GSTREAMER)
    if cap.isOpened():
        window_handle = cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)
        # Window
        while cv2.getWindowProperty("CSI Camera", 0) >= 0:
            #t1=time.time()
            ret_val, img = cap.read()
            #print(img.shape)
            #print(time.time()-t1)
            cv2.imshow("CSI Camera", img)
            
            #print(time.time()-last_tim)
            #last_tim=time.time()
            # This also acts as
            keyCode = cv2.waitKey(1) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
                

            counter+=1
            if (time.time() - start_time) > x :
                print("FPS: ", counter / (time.time() - start_time))
                counter = 0
                start_time = time.time()
        cap.release()
        cv2.destroyAllWindows()
    else:
        print("Unable to open camera")


if __name__ == "__main__":
    show_camera()