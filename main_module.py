import threading
import cv2
import numpy as np

#import sys
#sys.path.append('./vid_stream')
#import web_app.streamer as streamer
import web_app.streamer as streamer
from g_pipeline import gstreamer_pipeline
import time
import camera_calibration
import utils
import lane_detector_module
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
            #img = camera_calibration.find_chessboard(img,draw=True, calibrate=True)
            undist = camera_calibration.undistort(img)
            undist = cv2.resize(undist,(640,480))
            img_list = lane_detector_module.findLines(undist)
            left_line, right_line = lane_detector_module.findCurvature(img_list[0])
            #print(x1,x2)

            warped = img_list[2].copy()
            for pt in left_line:
                cv2.circle(warped,pt,5,(0,0,255),cv2.FILLED)

            for pt in right_line:
                cv2.circle(warped,pt,5,(0,255,0),cv2.FILLED)
            #cv2.circle(warped,right_line,5,(0,255,0),cv2.FILLED)
            

            #streamer.set_frame(img,0,scale=0.2)
            #streamer.set_frame(undist,1,scale=0.2)
            stack = utils.stackImages(.7,[img_list[1],warped,img_list[0]])
            #streamer.set_frame(stack,0,scale=0.6)
            cv2.imshow('Images',stack)
            keyCode = cv2.waitKey(30) & 0xFF
            # Stop the program on the ESC key
            if keyCode == 27:
                break
    cap.release()
    cv2.destroyAllWindows()

def take_picture():
    camera_calibration.calibrate(True)
    # global frame_no, img
    # print('Capturing this frame no '+str(frame_no))
    # cv2.imwrite('./img/chessbrd%d.jpg' % frame_no, img)
    # frame_no+=1

if __name__ == "__main__":
    global cap
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    time.sleep(2.0)
    camera_calibration.import_calib()
    lane_detector_module.init()
    
    t = threading.Thread(target=get_vid)
    t.daemon = True
    t.start()
    #streamer.on_pic(take_picture)
    #streamer.start_stream()
    #camera_calibration.import_calib()
    
    #wait till the thread is completed
    t.join()
    



if not cap is None:
    cap.release()
