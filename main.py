
###
#openCV must be imported before jetson.utils and jetson.inference
###
# from eventlet import monkey_patch

#monkey_patch in connection with socketio.sleep(0) (in cpu intensive threads) allows for relatively fluent
#message flow (emit)
# monkey_patch()
# ##without monkeypatch broadcasted events are not received by browser
#monkey_patch(thread=False) thread i coś jeszcze ale nwm co!
#from web_app.streamer_new import HttpStreamer 
# import web_app.streamer_new_noclass as streamer
# import web_app.web_app_server as streamer
#import web_app.streamer as streamer
import time
import threading
import json
import numpy as np


import camera_calibration
import utils
import lane_finder_module
import web_app_module as app
import img_recognition_module as recognition
import driver_module as driver
import uart_module as uart
import auto_parking_module as parking
import jetson.utils


REMOTE_DESKTOP = False
FOLLOW_LANE = False
SIGN_RECOGNITION = False
AUTO_PARK = False
MANUAL_MODE = True

threads = []

lock = threading.Lock()

frameGPU = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
frameGPU_bgr_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameGPU_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')


start_time = time.time()
counter = 0
#period for fps calc
T=1

camera=None
display = None


def cameraInit():
    global camera
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                    "--framerate=15", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    camera.Capture()

def fpsCount():
    global counter, start_time
    counter += 1
    if (time.time() - start_time) > T:
        print("FPS: ", counter / (time.time() - start_time))
        counter = 0
        start_time = time.time()
x=1.0

new_frame = False

def videoLoop():
    global camera, display,x
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                  "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
        "display://0", argv=[])  # 'my_video.mp4' for file
    global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small, frameNp_small_detection, new_frame
    while display.IsStreaming():
        frameGPU = camera.Capture()
        jetson.utils.cudaResize(frameGPU,frameGPU_small)
        jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
        if SIGN_RECOGNITION:
            recognition.detectSigns(frameGPU_small)
        jetson.utils.cudaDeviceSynchronize()
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)

        new_frame = True
        if REMOTE_DESKTOP:
            display.Render(frameGPU)
        fpsCount()

        imageProcessing(frameNp_small)


def imageProcessing(img_in):
    global frameNp_small, frameNp_undist, new_frame, frameNp_small_detection
    global img_list
    center_offset = 0
    if new_frame:
        new_frame=False
        img_undist = camera_calibration.undistort(img_in)

        left_line, center_line, right_line = lane_finder_module.getLanePoints(img_undist)
        warped = lane_finder_module.warped_img.copy()
        mask = lane_finder_module.hsv_mask.copy()
        avg_angle = lane_finder_module.getCurveAngle(center_line)
        # middle_error = warped.shape[1]//2 - center_line[0]
        if center_line.any() and avg_angle:
            center_offset = steering(avg_angle,center_line[0][0],warped.shape[1]//2)

        utils.drawLaneLine(warped,left_line,color=(0,0,255))
        utils.drawLaneLine(warped,center_line,color=(255,0,0))
        utils.drawLaneLine(warped,right_line,color=(0,255,0))
        #draw line at the center of the screen
        utils.drawStraightLine(warped, (warped.shape[1]//2,warped.shape[0]),(warped.shape[1]//2,warped.shape[0]-30),color=(255,255,0))
        
        # if center_offset:
            #draw the offset center
            # utils.drawStraightLine(warped, (int(warped.shape[1]//2 + center_offset),warped.shape[0]),(int(warped.shape[1]//2 +center_offset),warped.shape[0]-30),color=(255,0,255))


        #print('Lane algorithm: ',time.time()-start2)
        curv_coeff = 5 #5 was fine for distorted
        alignment_coeff = 0.5 #0.7 was fine with distorted
        disalignment = 0

        global target_center, lane_center
        if center_line.any():
            lane_center = center_line[0][0]
            target_center = lane_center #+ curvature*curv_coeff
            disalignment = (img_undist.shape[1]/2 - target_center)*alignment_coeff
            # cv2.line(warped,(int(target_center),warped.shape[0]),(int(target_center),warped.shape[0]-50),(255,255,0),2)
            # cv2.line(warped,(int(lane_center),warped.shape[0]),(int(lane_center),warped.shape[0]-30),(255,0,0),2)
            
        #we don't neccessarily need to keep to the center of lane
        #if a right turn is detected we might want to keep to target_center which would be shifted to left
        
        # cv2.line(warped,(int(warped.shape[1]/2),warped.shape[0]),(int(warped.shape[1]/2),warped.shape[0]-50),(255,0,0),2)
        #if right turn is detected keep to the left and respectively                
        if FOLLOW_LANE:
            driver.speed(100.0)
            driver.turn(disalignment)
        driver.requestTelemetry()           

        img_list = [recognition.getVisual(),img_undist,warped, mask]
        app.emitFrames(img_list,0.6)

def steering(avg_angle, first_center, img_middle):
    offset_coeff = 3.0
    c = 0.5
    center_offset = avg_angle * offset_coeff
    middle_error = img_middle - (first_center+center_offset)
    output_angle = avg_angle+ c*middle_error
    print('Average curvature angle',avg_angle,'center offset:',center_offset,'middle error: ', middle_error, 'output angle:', output_angle)
    
    driver.turn(output_angle)
    return middle_error

def parseResponse(res):
    if  res != None:
        #print("UART RES",res)
        try:
            res_dict = json.loads(res)
        except:
            print(f"Error parsing incoming data to JSON: {res}")
            return
        if "speed" in res_dict:
            app.json_dict["current_speed"]=res_dict["speed"]
            parking.setSpeed(res_dict["speed"])
            if res_dict["pos_reg"] == 0:
                parking.awaiting = False

        if "sensors" in res_dict:
            app.json_dict["sensors"]=res_dict["sensors"]
            if AUTO_PARK and parking.space_mapping:
                parking.update(res_dict["sensors"])
            #     driver.speed(0.0)


def parseEventMsg(channel,data):
    global img_list, FOLLOW_LANE, AUTO_PARK, MANUAL_MODE
    print('parsing: ',data, 'on channel ',channel)
    if channel == 'capture':
        pass
    if 'target_speed' in data:
        driver.speed(data['target_speed'])
    if 'target_angle' in data:
        driver.turn(data['target_angle'])
    # if message=='captureImg1':
    #     print('writing img: ')
    #     cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[0])
    # if message=='captureImg2':
    #     print('writing img: ')
    #     cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[1])
    # if message=='captureImg3':
    #     print('writing img: ')
    #     cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[2])
    # if message=='captureImg4':
    #     print('writing img: ')
    #     cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[3])                        
    # if message =='follow_lane':
    #     FOLLOW_LANE=True
    #     MANUAL_MODE=False
    # if message =='park':
    #     AUTO_PARK=True
    #     MANUAL_MODE=False
    # if message =='manual':
    #     MANUAL_MODE=True
    #     AUTO_PARK=False
    #     FOLLOW_LANE=False


if __name__ == "__main__":
    global net
    if SIGN_RECOGNITION:
        recognition.init()

    camera_calibration.import_calib(640)

    ######THREADS######
    uart_thread = threading.Thread(target=uart.loop, daemon=True)
    parking_thread = threading.Thread(target=parking.loop, daemon=True)

    threads.append(uart_thread)
    threads.append(parking_thread)

    app.listenForEvents(parseEventMsg)
    uart.onReceived(parseResponse)
    app.emitDataToApp()
    for thread in threads:
        thread.start()
    
    videoLoop()
    driver.speed(0)

    for thread in threads:
        thread.join()


