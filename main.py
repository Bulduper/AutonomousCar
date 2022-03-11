###
#openCV must be imported before jetson.utils and jetson.inference
###
import time
import threading
import json

import camera_calibration
import utils
import lane_finder_module
import web_app_module as app
import object_detection_module as detection
import driver_module_new as driver
# import uart_module as uart
import auto_parking_module as parking
import jetson.utils

#Mode variables
REMOTE_DESKTOP = False
FOLLOW_LANE = False
SIGN_DETECTION = False
AUTO_PARK = False
OBSTACLES_AVOIDANCE = False

#threading variables
threads = []
lock = threading.Lock()

#jetson.utils CUDA image variables
frameGPU = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
frameGPU_bgr_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameGPU_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')

#fps counter vars
start_time = time.time()
counter = 0
#period for fps calculation [s]
T=1

# camera=None
# display = None

#dictionary for outcoming images
images = dict()

#initiate camera&display using jetson.utils (alternatively openCV with proper GStreamer pipeline can be used)
def cameraInit():
    global camera
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                    "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
    "display://0", argv=[])  # 'my_video.mp4' for file
    return camera, display
#count fps or loops per second and set it as dict var every T seconds
def fpsCount():
    global counter, start_time
    counter += 1
    if (time.time() - start_time) > T:
        fps = round(counter / (time.time() - start_time),1)
        # print("FPS: ", fps)
        app.json_dict['fps']=fps
        counter = 0
        start_time = time.time()

#fresh frame ready?
new_frame = False

#main loop
def videoLoop():
    global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small, frameNp_small_detection, new_frame
    camera, display = cameraInit()
    
    while display.IsStreaming():
        #get CUDA img
        frameGPU = camera.Capture()
        #resize CUDA img to 640x480
        jetson.utils.cudaResize(frameGPU,frameGPU_small)
        #convert colors from RGB to BGR as for openCV
        jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
        if SIGN_DETECTION:
            time4= time.time()
            detection.detectSigns(frameGPU_small)
            print('Detection T: ',time.time()-time4)
        #synchronizes GPU with CPU
        jetson.utils.cudaDeviceSynchronize()
        #make numpy array from small BGR CUDA img frame
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)
        new_frame = True
        #if there is a display connected to Jetson, frames can be displayed on it 
        if REMOTE_DESKTOP:
            display.Render(frameGPU)
        fpsCount()
        time1= time.time()
        #do the image processing with numpy array small frame
        imageProcessing(frameNp_small)
        # print('Img processing T: ',time.time()-time1)
#further process numpy array frame
def imageProcessing(img_in):
    global frameNp_small, frameNp_undist, new_frame, frameNp_small_detection
    global img_list
    center_offset = 0
    if new_frame:
        new_frame=False

        time3 = time.time()
        #get undistorted image - VERY TIME CONSUMING!!!
        img_undist = camera_calibration.undistort(img_in)
        #print('Undist T: ',time.time()-time3)
        #get lane line points
        left_line, center_line, right_line = lane_finder_module.getLanePoints(img_undist)
        
        #put images to dict
        images['raw']=img_in.copy()
        images['undistorted']=img_undist.copy()
        warped = lane_finder_module.warped_img.copy()
        images['warped']=warped.copy()
        mask = lane_finder_module.hsv_mask.copy()
        if FOLLOW_LANE:
            #get average curvature [deg] of the lane
            avg_angle = lane_finder_module.getCurveAngle(center_line)
            # middle_error = warped.shape[1]//2 - center_line[0]
            if center_line.any() and avg_angle:
                #display avg angle on the img
                utils.putText(warped,"Avg lane angle: {} deg".format(round(avg_angle,0)))
                #obtain steering (servo turn angle)
                center_offset = steering(avg_angle,center_line[0][0],warped.shape[1]//2)

        #mark line points
        utils.drawLaneLine(warped,left_line,color=(0,0,255))
        utils.drawLaneLine(warped,center_line,color=(255,0,0))
        utils.drawLaneLine(warped,right_line,color=(0,255,0))
        #draw line at the center of the screen
        utils.drawStraightLine(warped, (warped.shape[1]//2,warped.shape[0]),(warped.shape[1]//2,warped.shape[0]-30),color=(255,255,0))
        #request all the info from robot by UART
        # driver.requestTelemetry()           
        #TO DO: Optimise!
        #put images to dict
        images['warped_plot']=warped.copy()
        images['mask']=mask.copy()
        images['detection']=detection.getVisual()
        images['undistorted_plot'] = lane_finder_module.undist_plot.copy()
        img_list = [detection.getVisual(),img_undist,warped, mask, img_undist, warped,mask]
        time2 = time.time()
        #emit images to web app
        app.emitImages(images,scale=0.5)
        # print('Emiting T: ',time.time()-time2)

def steering(avg_angle, first_center, img_middle):
    #we don't neccessarily need to keep to the center of lane
    #if a right turn is detected we might want to keep to target_center which would be shifted to left

    offset_coeff = 0 #3.0
    # c = 0.5
    c = 0.5
    b = 0#-0.5
    center_offset = avg_angle * offset_coeff
    # middle_error = img_middle - (first_center+center_offset)
    middle_error = img_middle - first_center
    # output_angle = avg_angle+ c*middle_error
    output_angle = avg_angle*b + c*middle_error
    # print('Average curvature angle',avg_angle,'center offset:',center_offset,'middle error: ', middle_error, 'output angle:', output_angle)
    
    driver.turn(output_angle)
    return middle_error

#handle response from robot
def parseUartReponse(res):
    if  res != None:
        # print("UART RES",res)
        try:
            res_dict = json.loads(res)
        except:
            print(f"Error parsing incoming data to JSON: {res}")
            return
        if "speed" in res_dict:
            app.json_dict["current_speed"]=round(res_dict["speed"],1)
            parking.setSpeed(res_dict["speed"])
            if res_dict["pos_reg"] == 0 and parking.awaiting == True:
                print('DONE')
                parking.awaiting = False
        if "angle" in res_dict:
            app.json_dict["angle"] = res_dict["angle"]
        if "bat_vol" in res_dict:
            app.json_dict["voltage"] = round(res_dict["bat_vol"],1)
        if "sensors" in res_dict:
            app.json_dict["sensors"]=res_dict["sensors"]
            driver.sensors = res_dict["sensors"]
            if AUTO_PARK and parking.space_mapping:
                parking.update(res_dict["sensors"])
            if OBSTACLES_AVOIDANCE:
                if driver.checkForObstacles(trigger=8)!='none':
                    driver.speed(0)
            #     driver.speed(0.0)

#handle event from web App
def parseEventMsg(channel,data):
    global img_list, FOLLOW_LANE, AUTO_PARK, SIGN_DETECTION,OBSTACLES_AVOIDANCE
    print('parsing: ',data, 'on channel ',channel)
    if channel == 'capture':
        pass
    # if 'connected' in data:
    #     app.json_dict['images']=images;
    if 'targetSpeed' in data:
        driver.speed(data['targetSpeed'])
    if 'targetTurn' in data:
        driver.turn(data['targetTurn'])
    if 'speedLimit' in data:
        driver.setSpeedLimit(data['speedLimit'])
    if 'followLane' in data:
        state = data['followLane']['state']
        FOLLOW_LANE = state
    if 'signDetection' in data:
        state = data['signDetection']['state']
        SIGN_DETECTION = state
    if 'parking' in data:
        state = data['parking']['state']
        AUTO_PARK = state
    if 'obstacleAvoidance' in data:
        state = data['obstacleAvoidance']['state']
        OBSTACLES_AVOIDANCE = state
    if 'go' in data:
        state = data['go']['state']
        driver.speed(160)
    if 'stop' in data:
        state = data['stop']['state']
        driver.speed(0)
    if 'requestedImgs'in data:
        app.requestedImgKeys = data['requestedImgs']
    if 'capture'in data:
        utils.captureImg(images[data['capture']['imgKey']],'signs/'+data['capture']['imgKey'])

if __name__ == "__main__":
    global net
    if SIGN_DETECTION:
        detection.init()
    #import calibration matrices and params from files
    camera_calibration.import_calib(640)

    ######THREADS######
    # uart_thread = threading.Thread(target=uart.loop, daemon=True)
    parking_thread = threading.Thread(target=parking.loop, daemon=True)

    # threads.append(uart_thread)
    threads.append(parking_thread)
    app.sendLogsToServer()
    app.listenForEvents(parseEventMsg)
    driver.listenContinuously(parseUartReponse)
    app.emitDataToApp()
    for thread in threads:
        thread.start()
    if AUTO_PARK:
        parking.enable()
    videoLoop()
    driver.speed(0)

    for thread in threads:
        thread.join()


