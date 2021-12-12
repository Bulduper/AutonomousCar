
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
import base64
from flask_socketio import SocketIO, send
import redis
import time
import threading
import cv2
import json

import camera_calibration
import utils
import lane_detector_module
import driver_module as driver
import uart_module as uart
import auto_parking_module as parking
import jetson.utils
import jetson.inference


REMOTE_DESKTOP = False
FOLLOW_LANE = False
SIGN_RECOGNITION = True
AUTO_PARK = False
MANUAL_MODE = True

threads = []
socketio = SocketIO(message_queue='redis://localhost:7777')
r= redis.Redis(host='localhost', port=7777, db=0)
ps = r.pubsub()
ps.subscribe('buttonPressed')
#ignore first 'subscribed' message
ps.get_message()
lock = threading.Lock()

json_dict = dict()

#streamer = HttpStreamer()

frameGPU = jetson.utils.cudaAllocMapped(width=1640, height=1232, format='rgb8')
frameGPU_bgr_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')
frameGPU_small = jetson.utils.cudaAllocMapped(width=640, height=480, format='rgb8')
frameGPU_bgr_small_detection = jetson.utils.cudaAllocMapped(width=640, height=480, format='bgr8')

start_time = time.time()
counter = 0
#period for fps calc
T=1

#data from App parsing frequency
parse_freq = 5.0


camera=None
display = None


# @socketio.on('my event')
# def handle_message(data):
#     global x
#     print('received message: ' + str(data))

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
def getVideoContinuous():
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
            detectSigns(frameGPU_small)
            jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small_detection)
        jetson.utils.cudaDeviceSynchronize()
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)
        if SIGN_RECOGNITION:
            frameNp_small_detection = jetson.utils.cudaToNumpy(frameGPU_bgr_small_detection)
        new_frame = True
        if REMOTE_DESKTOP:
            display.Render(frameGPU)
        fpsCount()
        # streamer.setFrame(frameNp_small)
        #socketio.sleep(0) (in cpu intensive threads) in connection with monkey_patch allows for relatively fluent
        #message flow (emit)
        

        # global frameNp_undist
        # new_frame=False
        # frameNp_undist = camera_calibration.undistort(frameNp_small)
        # streamer.setFrame(frameNp_undist)

        imageProcessing()
        # streamer.socketio.sleep(0)

def encodeFrame(frame):
    # frame= cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
    frame = cv2.imencode('.jpg', frame)[1].tobytes()
    frame= base64.encodebytes(frame).decode("utf-8")
    return frame

def emitFrames(frames, scale=1.0):
    for i, frame in enumerate(frames):
        frame = cv2.resize(frame, (0, 0), None, scale, scale)
        emit('image'+str(i+1),encodeFrame(frame))

def emit(topic,data):
    socketio.emit(topic,data)

# def getFrame():
#     threading.Timer(1.0, getFrame).start()
#     print('hello')
#     global camera, display, REMOTE_DESKTOP
#     if display is None and REMOTE_DESKTOP:
#         display = jetson.utils.videoOutput(
#             "display://0", argv=[])  # 'my_video.mp4' for file
#     global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small
#     with lock:
#         frameGPU = camera.Capture()
#         jetson.utils.cudaResize(frameGPU,frameGPU_small)
#         jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
#         jetson.utils.cudaDeviceSynchronize()
#         frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)
#     if REMOTE_DESKTOP:
#         display.Render(frameGPU)
#     streamer.setFrame(frameNp_small)

json_dict = dict()
speed_dict = dict()
angle_dict = dict()

#json_dict[]
# def OneHzLoop():
#     global x
#     threading.Timer(0.5,OneHzLoop).start()
#     json_dict['speed']=x*3
#     json_dict['angle']=x+5
#     x+=1
#     streamer.emit('telemetry',json_dict)


def imageProcessing():
    global frameNp_small, frameNp_undist, new_frame, frameNp_small_detection
    global img_list
    if new_frame:
        new_frame=False
        frameNp_undist = camera_calibration.undistort(frameNp_small)
        # streamer.setFrame(frameNp_undist)

        ldm_img_list = lane_detector_module.findLines(frameNp_undist)
        center_line, curvature, debug_img = lane_detector_module.findCurvature(ldm_img_list[0],ldm_img_list[2])
        #print('Lane algorithm: ',time.time()-start2)
        curv_coeff = 5 #5 was fine for distorted
        alignment_coeff = 0.5 #0.7 was fine with distorted
        disalignment = 0
        warped = debug_img.copy()
        global target_center, lane_center
        if center_line.any():
            lane_center = center_line[0][0]
            target_center = lane_center + curvature*curv_coeff
            disalignment = (frameNp_undist.shape[1]/2 - target_center)*alignment_coeff
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

        # stack = utils.stackImages(0.5,[ldm_img_list[1],warped,ldm_img_list[0], ldm_img_list[2]])
        img_list = [ldm_img_list[1],warped,ldm_img_list[0], ldm_img_list[2]]
        img_list = [frameNp_small_detection,frameNp_small,frameNp_undist,ldm_img_list[0]]
        emitFrames(img_list,0.6)

def imageProcessingLoop():
    global frameNp_small, frameNp_undist, new_frame

    while True:
        imageProcessing()
        # streamer.socketio.sleep(0)

def detectSigns(cuda_img):
    global net
    detections= net.Detect(cuda_img,640,480)
    for detect in detections:
        ID = detect.ClassID
        item=net.GetClassDesc(ID)
        print(item)

def listenForEvents():
    message = ps.get_message()
    if message:
        print('Event received',message)
        parseEventMsg(message['data'].decode("utf-8"))
    threading.Timer(1.0/parse_freq,listenForEvents).start()

def parseEventMsg(message):
    global img_list, FOLLOW_LANE, AUTO_PARK, MANUAL_MODE
    print('parsing: ',message)
    if message=='captureImg1':
        print('writing img: ')
        cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[0])
    if message=='captureImg2':
        print('writing img: ')
        cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[1])
    if message=='captureImg3':
        print('writing img: ')
        cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[2])
    if message=='captureImg4':
        print('writing img: ')
        cv2.imwrite('./img/captured/capture_%d.jpg' % int(time.time()), img_list[3])                        
    if message =='follow_lane':
        FOLLOW_LANE=True
        MANUAL_MODE=False
    if message =='park':
        AUTO_PARK=True
        MANUAL_MODE=False
    if message =='manual':
        MANUAL_MODE=True
        AUTO_PARK=False
        FOLLOW_LANE=False
        


def parseAppInput():
    #string format
    user_input_raw = r.get('user_input')
    if not user_input_raw:
        threading.Timer(1.0/parse_freq,parseAppInput).start()
        return
    #dictionary format
    user_input = json.loads(user_input_raw)
    if not user_input:
        threading.Timer(1.0/parse_freq,parseAppInput).start()
        return
    #print(user_input)
    #decode dict from byte data
    # user_input = {k.decode('utf8'): v.decode('utf8') for k, v in user_input.items()}
    t_speed = user_input.get('target_speed')
    t_angle = user_input.get('target_angle')
    if MANUAL_MODE:
        if not t_speed is None:
            driver.speed(t_speed)
        if not t_angle is None:
            driver.turn(t_angle)
    threading.Timer(1.0/parse_freq,parseAppInput).start()

def processResponse(res):
    if  res != None:
        #print("UART RES",res)
        try:
            res_dict = json.loads(res)
        except:
            print(f"Error parsing incoming data to JSON: {res}")
            return
        if "speed" in res_dict:
            json_dict["current_speed"]=res_dict["speed"]
            parking.setSpeed(res_dict["speed"])
            if res_dict["pos_reg"] == 0:
                parking.awaiting = False

        if "sensors" in res_dict:
            json_dict["sensors"]=res_dict["sensors"]
            if AUTO_PARK and parking.space_mapping:
                parking.update(res_dict["sensors"])
            #     driver.speed(0.0)

def emitDataToApp():
    emit('robot_info',json_dict)
    threading.Timer(0.2,emitDataToApp).start()

if __name__ == "__main__":
    global net
    if SIGN_RECOGNITION:
        net = jetson.inference.detectNet(argv=["--model=./networks/ssd-mobilenet.onnx", "--labels=./networks/labels.txt", "--input-blob=input_0", "--output-cvg=scores", "--output-bbox=boxes"], threshold=0.2)

    camera_calibration.import_calib(640)

    ######THREADS######
    video_thread = threading.Thread(target=getVideoContinuous, daemon=True)
    # streamer_thread = threading.Thread(target=streamer.run, daemon=True)
    uart_thread = threading.Thread(target=uart.loop, daemon=True)
    image_processing_thread = threading.Thread(target=imageProcessingLoop, daemon=True)
    parking_thread = threading.Thread(target=parking.loop, daemon=True)

    #threads.append(video_thread)
    # threads.append(streamer_thread)
    threads.append(uart_thread)
    threads.append(parking_thread)
    #threads.append(image_processing_thread)

    parseAppInput()
    listenForEvents()
    uart.onReceived(processResponse)
    emitDataToApp()
    for thread in threads:
        thread.start()
    #streamer.run()
    # streamer.emitDataPeriodically()
    #driver.speed(100)
    getVideoContinuous()
    driver.speed(0)

    for thread in threads:
        thread.join()


