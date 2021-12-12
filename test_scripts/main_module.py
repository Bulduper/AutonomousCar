import threading
import cv2
import numpy as np
import json
import time
import jetson.utils
import jetson.inference

#My imports
import web_app.streamer as streamer
from g_pipeline import gstreamer_pipeline
import camera_calibration
import utils
import lane_detector_module
import driver_module as driver
import uart_module as uart
import auto_parking_module as parking

#net = jetson.inference.detectNet("ssd-mobilenet-v2",threshold=.7)

#net = jetson.inference.detectNet(argv=["--model=./ssd-mobilenet.onnx", "--labels=./labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=0.2)

frame_no = 1
last_put_time = 0
REMOTE_DESKTOP = False
FOLLOW_LANE = False
AUTO_PARK = False

threads = []

def calibrationLoop(img):
    driver.speed(0)
    img = camera_calibration.find_chessboard(img,draw=True, calibrate=True)
    streamer.set_frame(img,0,scale=0.8)
    keyCode = cv2.waitKey(1000) & 0xFF

#TODO Change a name of this function
def get_vid():
    global img, undist
    #driver.speed(100)
    start1 = 0
    while cap:
        #window_handle = cv2.namedWindow("Undist", cv2.WINDOW_AUTOSIZE)
        ret_val, img = cap.read()
        if ret_val:
            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            #print('looptime: ',time.time()-start1)
            #start1 = time.time()
            img = cv2.resize(img,(640,480))
            # calibrationLoop(img)
            # continue
            # img = cv2.resize(img,(640,480))
            undist = camera_calibration.undistort(img)
            
            # cuda_mem = jetson.utils.cudaFromNumpy(undist)
            # detections= net.Detect(cuda_mem,640,480)
            # for detect in detections:
            #     ID = detect.ClassID
            #     item=net.GetClassDesc(ID)
            #     print(item)
            #class_desc = net.GetClassDesc(class_idx)
            #print("image is recognized as '{:s}' (class #{:d}) with {:f}% confidence".format(class_desc, class_idx, confidence * 100))
            #undist = img.copy()
            #undist = cv2.resize(undist,(640,480))
            #cv2.imshow('Undist',undist)
            #start2 = time.time()
            img_list = lane_detector_module.findLines(undist)
            center_line, curvature, debug_img = lane_detector_module.findCurvature(img_list[0],img_list[2])
            #print('Lane algorithm: ',time.time()-start2)
            curv_coeff = 5 #5 was fine for distorted
            alignment_coeff = 0.5 #0.7 was fine with distorted
            disalignment = 0
            warped = debug_img.copy()
            global target_center, lane_center
            if center_line.any():
                lane_center = center_line[0][0]
                target_center = lane_center + curvature*curv_coeff
                disalignment = (undist.shape[1]/2 - target_center)*alignment_coeff
                cv2.line(warped,(int(target_center),warped.shape[0]),(int(target_center),warped.shape[0]-50),(255,255,0),2)
                cv2.line(warped,(int(lane_center),warped.shape[0]),(int(lane_center),warped.shape[0]-30),(255,0,0),2)
                
            #we don't neccessarily need to keep to the center of lane
            #if a right turn is detected we might want to keep to target_center which would be shifted to left
            
            cv2.line(warped,(int(warped.shape[1]/2),warped.shape[0]),(int(warped.shape[1]/2),warped.shape[0]-50),(255,0,0),2)
            #if right turn is detected keep to the left and respectively                
            if FOLLOW_LANE:
                driver.turn(disalignment)
            driver.requestTelemetry()           

            #streamer.set_frame(img,0,scale=0.2)
            #streamer.set_frame(undist,1,scale=0.2)
            stack = utils.stackImages(1,[img, img_list[1],warped,img_list[0], img_list[2]])
            streamer.set_frame(stack,0,scale=1)
            if REMOTE_DESKTOP:
                cv2.imshow('Images',stack)
                keyCode = cv2.waitKey(30) & 0xFF
                # Stop the program on the ESC key
                #print(keyCode)
                if keyCode == 27:   #ESC key
                    break
                if keyCode == 115:  #S key
                    driver.speed(0)
                if keyCode == 102:  #F key
                    driver.speed(100)
    driver.speed(0)
    cap.release()
    cv2.destroyAllWindows()
var=0
def take_picture():
    #camera_calibration.calibrate(True)
    # global var
    # var=var+1
    # if var % 2 == 1:
    #     driver.speed(100)
    # else: driver.speed(0)


    global frame_no, img
    print('Capturing this frame no '+str(frame_no))
    cv2.imwrite('./img/signs/sign_detection_set_%d.jpg' % frame_no, undist)
    frame_no+=1

def processResponse(res):
    #print('HELLO',res)
    if  res != None:
        #print("UART RES",res)
        try:
            res_dict = json.loads(res)
        except:
            print(f"Error parsing incoming data to JSON: {res}")
            return

        if "sensors" in res_dict:
            if AUTO_PARK and parking.update(res_dict["sensors"]) is True:
                driver.speed(0.0)
        if "speed" in res_dict:
            parking.setSpeed(res_dict["speed"])
            if res_dict["pos_reg"] == 0:
                parking.awaiting = False

if __name__ == "__main__":
    global cap
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    time.sleep(2.0)
    camera_calibration.import_calib(640)
    uart.onReceived(processResponse)
    if REMOTE_DESKTOP:
        lane_detector_module.init()
    
    t = threading.Thread(target=get_vid)
    uart_thread = threading.Thread(target=uart.loop)
    park_thread = threading.Thread(target=parking.loop)
    t.daemon = True
    uart_thread.deamon = True
    park_thread.deamon = True
    t.start()
    uart_thread.start()
    park_thread.start()
    streamer.on_pic(take_picture)
    streamer.start_stream()
    #camera_calibration.import_calib()
    driver.setLED()


    #wait till the thread is completed
    t.join()
    uart_thread.join()
    park_thread.join()
    

if not cap is None:
    cap.release()
