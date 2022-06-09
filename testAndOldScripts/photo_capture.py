import threading
import cv2
import numpy as np

#import sys
#sys.path.append('./vid_stream')
import vid_stream.streamer as streamer
from g_pipeline import gstreamer_pipeline
import time
import calib_from_img
import utils
#LEFT ENTER TO TAKE&SAVE PHOTO
#ESC TO QUIT

frame_no = 1

def get_vid():
    global img, undist
    while cap:
        #window_handle = cv2.namedWindow("Undist", cv2.WINDOW_AUTOSIZE)
        ret_val, img = cap.read()
        if ret_val:
            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            #img = calib_from_img.find_chessboard(img,draw=True, calibrate=True)
            undist = calib_from_img.undistort(img)
            #streamer.set_frame(img,0,scale=0.2)
            #streamer.set_frame(undist,1,scale=0.2)
            stack = utils.stackImages(.25,[img, undist])
            streamer.set_frame(stack,0,scale=0.6)
            
            cv2.imshow('Undist',stack)
            #print(undist.shape)
            keyCode = cv2.waitKey(30) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
            if keyCode == 13:
                global frame_no
                print('Capturing this frame no '+str(frame_no))
                cv2.imwrite('./img/chessbrd%d.jpg' % frame_no, img)
                frame_no+=1
    cap.release()
    cv2.destroyAllWindows()

def take_picture():
    calib_from_img.calibrate(True)
    # global frame_no, img
    # print('Capturing this frame no '+str(frame_no))
    # cv2.imwrite('./img/chessbrd%d.jpg' % frame_no, img)
    # frame_no+=1



if __name__ == "__main__":
    # print(gstreamer_pipeline())
    # cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    # frame_no = 1
    # if cap.isOpened():
    #     #window_handle = cv2.namedWindow("CSI Camera", cv2.WINDOW_AUTOSIZE)
    #     stream.start_stream()
    #     # Window
    #     #while cv2.getWindowProperty("CSI Camera", 0) >= 0 or True:
    #     while True:
    #         ret_val, img = cap.read()
    #         #cv2.imshow("CSI Camera", img)
    #         stream.set_frame(img)
    #         # This also acts as
    #         keyCode = cv2.waitKey(30) & 0xFF
    #         # Stop the program on the ESC key
    #         if keyCode == 27:
    #             break
    #         if keyCode == 13:
    #             print('Capturing this frame no '+str(frame_no))
    #             cv2.imwrite('./img/chessbrd%d.jpg' % frame_no, img)
    #             frame_no+=1
    #     cap.release()
    #     cv2.destroyAllWindows()
    # else:
    #     print("Unable to open camera")
    global cap
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    time.sleep(2.0)
    calib_from_img.import_calib()
    t = threading.Thread(target=get_vid)
    t.daemon = True
    t.start()
    streamer.on_pic(take_picture)
    streamer.start_stream()
    #calib_from_img.import_calib()

if not cap is None:
    cap.release()
