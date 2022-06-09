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
import driver_module as driver
# import uart_module as uart
import auto_parking_module as parking
import jetson.utils

#Mode variables
REMOTE_DESKTOP = False
FOLLOW_LANE = False
SIGN_DETECTION = True
RESPECT_SIGNS = True
AUTO_PARK = False
OBSTACLES_AVOIDANCE = False
UNDISTORT = False

#Detection ROI
det_roi_x = (0.2,0.8)
det_roi_y = (0.5,0.7)

#threading variables
threads = []
lock = threading.Lock()

#jetson.utils CUDA image variables
frameCuda = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
frameCudaRedBgr = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameCudaRed = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')


fps = utils.FPSCounter(1)

# camera=None
# display = None

#dictionary for outcoming images
images = dict()

#initiate camera&display using jetson.utils (alternatively openCV with proper GStreamer pipeline can be used)
def cameraInit():
    global camera, display
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                    "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
    "display://0", argv=[])  # 'my_video.mp4' for file
    # return camera, display

def makeStateDict():
    state_dict = dict()
    state_dict['followLane'] = FOLLOW_LANE
    state_dict['detectSigns'] = SIGN_DETECTION
    state_dict['respectSigns'] = RESPECT_SIGNS
    state_dict['parkingMode'] = AUTO_PARK
    state_dict['avoidObstacles'] = OBSTACLES_AVOIDANCE
    state_dict['undistort'] = UNDISTORT
    return state_dict

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
    
    driver.setTurn(output_angle)
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
                    driver.setSpeed(0)


#handle event from web App
def parseEventMsg(channel,data):
    global FOLLOW_LANE, AUTO_PARK, SIGN_DETECTION,OBSTACLES_AVOIDANCE,RESPECT_SIGNS, UNDISTORT
    print('parsing: ',data, 'on channel ',channel)
    if channel == 'capture':
        pass
    if 'connected' in data:
        app.json_dict['state']=makeStateDict()
    if 'targetSpeed' in data:
        driver.setSpeed(data['targetSpeed'])
    if 'targetTurn' in data:
        driver.setTurn(data['targetTurn'])
    if 'speedLimit' in data:
        driver.setSpeedLimit(data['speedLimit'])
    if 'followLane' in data:
        state = data['followLane']['state']
        FOLLOW_LANE = state
    if 'detectSigns' in data:
        state = data['detectSigns']['state']
        SIGN_DETECTION = state
    if 'respectSigns' in data:
        state = data['respectSigns']['state']
        RESPECT_SIGNS = state
    if 'parkingMode' in data:
        state = data['parkingMode']['state']
        AUTO_PARK = state
    if 'avoidObstacles' in data:
        state = data['avoidObstacles']['state']
        OBSTACLES_AVOIDANCE = state
    if 'undistort' in data:
        state = data['undistort']['state']
        UNDISTORT = state
    if 'go' in data:
        state = data['go']['state']
        driver.setSpeed(160)
    if 'stop' in data:
        state = data['stop']['state']
        driver.setSpeed(0)
    if 'requestedImgs'in data:
        app.requestedImgKeys = data['requestedImgs']
    if 'capture'in data:
        utils.captureImg(images[data['capture']['imgKey']],'signs/'+data['capture']['imgKey'])


def getVideoFrame():
    if display.IsStreaming():
        #get CUDA img
        return camera.Capture()

def reduceCudaFrame(source, destination):
    #resize CUDA img to 640x480
    jetson.utils.cudaResize(source,destination)

def cudaToNumpy(source):
    #convert colors from RGB to BGR as for openCV
    jetson.utils.cudaConvertColor(source, frameCudaRedBgr)
    return jetson.utils.cudaToNumpy(frameCudaRedBgr)

def detectSigns(source):
    detections = detection.detectSigns(source)
    detectedSignsList = []
    for sign in detections:
        detectedSignsList.append(detection.getClassName(sign.ClassID))
    return detections, detectedSignsList

def detectLane(source):
    global images
    left_line, center_line, right_line = lane_finder_module.getLanePoints(source)
    avg_angle = lane_finder_module.getCurveAngle(center_line)
    warped = lane_finder_module.warped_img.copy()
    if center_line.any() and avg_angle:
        #display avg angle on the img
        utils.putText(warped,"Avg lane angle: {} deg".format(round(avg_angle,0)))

    #mark line points
    utils.drawLaneLine(warped,left_line,color=(0,0,255))
    utils.drawLaneLine(warped,center_line,color=(255,0,0))
    utils.drawLaneLine(warped,right_line,color=(0,255,0))
    #draw line at the center of the screen
    utils.drawStraightLine(warped, (warped.shape[1]//2,warped.shape[0]),(warped.shape[1]//2,warped.shape[0]-30),color=(255,255,0))

    images['warped_plot']=warped.copy()

    return center_line, avg_angle

def followLane(center_line, avg_angle, img_width):
    if center_line.any() and avg_angle:
        #obtain steering (servo turn angle)
        center_offset = steering(avg_angle,center_line[0][0],img_width//2)

def mainLoop():
    global frameCuda, images
    frameCuda = getVideoFrame()
    reduceCudaFrame(frameCuda, frameCudaRed)
    frameNumpy = cudaToNumpy(frameCudaRed)
    if SIGN_DETECTION:
        # crop the original frame to a usecase specific roi
        frameRoi = utils.cropRelative(frameCuda, (det_roi_x[0], det_roi_y[0], det_roi_x[1], det_roi_y[1]))
        detections, detectedSigns = detectSigns(frameRoi)
        # detections, detectedSigns = detectSigns(frameCuda)
        driver.reactToSigns(detectedSigns)
    
    #synchronizes GPU with CPU
    jetson.utils.cudaDeviceSynchronize()

    #get undistorted image - VERY TIME CONSUMING!!!
    img_undist = None
    if UNDISTORT:
        img_undist = camera_calibration.undistort(frameNumpy)

    #get lane line points
    if img_undist is not None:
        center_line, avg_angle = detectLane(img_undist)
    else:
        center_line, avg_angle = detectLane(frameNumpy)

    if FOLLOW_LANE:
        followLane(center_line, avg_angle, frameNumpy.shape[1])
    
    #put images to dict
    images['raw']=frameNumpy.copy()
    images['warped']=lane_finder_module.warped_img.copy()
    images['mask']=lane_finder_module.hsv_mask.copy()
    if UNDISTORT and img_undist is not None: 
        images['undistorted']=img_undist.copy()
        images['undistorted_plot'] = lane_finder_module.undist_plot.copy()
    images['detection']=detection.getVisual()
    
    app.json_dict['fps'] = fps.getFps()
    #emit images to web app
    app.emitRequestedImages(images,scale=0.5)


if __name__ == "__main__":
    #optional, because it would be done automatically later anyways
    if SIGN_DETECTION:
        detection.init()
    #import calibration matrices and params from files
    camera_calibration.import_calib(640)

    ######THREADS######
    parking_thread = threading.Thread(target=parking.loop, daemon=True)

    threads.append(parking_thread)
    app.sendLogsToServer()
    app.listenForEvents(parseEventMsg)
    driver.listenContinuously(parseUartReponse)
    app.emitDataToApp()
    for thread in threads:
        thread.start()
    if AUTO_PARK:
        parking.enable()
    # videoLoop()
    cameraInit()
    while True:
        mainLoop()
    driver.setSpeed(0)

    for thread in threads:
        thread.join()


