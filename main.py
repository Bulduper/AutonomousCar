
###
#openCV must be imported before jetson.utils and jetson.inference
###
from eventlet import monkey_patch

#monkey_patch in connection with socketio.sleep(0) (in cpu intensive threads) allows for relatively fluent
#message flow (emit)
monkey_patch()
# ##without monkeypatch broadcasted events are not received by browser
#monkey_patch(thread=False) thread i coś jeszcze ale nwm co!
#from web_app.streamer_new import HttpStreamer 
from flask import json
import web_app.streamer_new_noclass as streamer
#import web_app.streamer as streamer
import jetson.utils
import jetson.inference
import time
import threading

import camera_calibration
import utils
import lane_detector_module
import driver_module as driver
import uart_module as uart
import auto_parking_module as parking



REMOTE_DESKTOP = False

threads = []
lock = threading.Lock()


#streamer = HttpStreamer()

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
def getVideoContinuous():
    global camera, display,x
    camera = jetson.utils.videoSource("csi://0", argv=["--input-height=1232", "--input-width=1640",
                                  "--framerate=30", "--flip-method=rotate-180"])      # '/dev/video0' for V4L2
    display = jetson.utils.videoOutput(
        "display://0", argv=[])  # 'my_video.mp4' for file
    global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small, new_frame
    while display.IsStreaming():
        frameGPU = camera.Capture()
        jetson.utils.cudaResize(frameGPU,frameGPU_small)
        jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
        jetson.utils.cudaDeviceSynchronize()
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)
        new_frame = True
        if REMOTE_DESKTOP:
            display.Render(frameGPU)
        fpsCount()
        # streamer.setFrame(frameNp_small)
        #socketio.sleep(0) (in cpu intensive threads) in connection with monkey_patch allows for relatively fluent
        #message flow (emit)
        x+=1
        streamer.json_dict['speed']=x

        # global frameNp_undist
        # new_frame=False
        # frameNp_undist = camera_calibration.undistort(frameNp_small)
        # streamer.setFrame(frameNp_undist)
        streamer.socketio.sleep(0)

def getFrame():
    threading.Timer(1.0, getFrame).start()
    print('hello')
    global camera, display, REMOTE_DESKTOP
    if display is None and REMOTE_DESKTOP:
        display = jetson.utils.videoOutput(
            "display://0", argv=[])  # 'my_video.mp4' for file
    global frameGPU,frameGPU_bgr_small, frameGPU_small, frameNp_small
    with lock:
        frameGPU = camera.Capture()
        jetson.utils.cudaResize(frameGPU,frameGPU_small)
        jetson.utils.cudaConvertColor(frameGPU_small, frameGPU_bgr_small)
        jetson.utils.cudaDeviceSynchronize()
        frameNp_small = jetson.utils.cudaToNumpy(frameGPU_bgr_small)
    if REMOTE_DESKTOP:
        display.Render(frameGPU)
    streamer.setFrame(frameNp_small)

json_dict = dict()
speed_dict = dict()
angle_dict = dict()

#json_dict[]
def OneHzLoop():
    global x
    threading.Timer(0.5,OneHzLoop).start()
    json_dict['speed']=x*3
    json_dict['angle']=x+5
    x+=1
    streamer.emit('telemetry',json_dict)

def imageProcessingLoop():
    global frameNp_small, frameNp_undist, new_frame
    while True:
        if new_frame:
            new_frame=False
            frameNp_undist = camera_calibration.undistort(frameNp_small)
            streamer.setFrame(frameNp_undist)
        streamer.socketio.sleep(0)

if __name__ == "__main__":
    camera_calibration.import_calib(640)

    ######THREADS######
    video_thread = threading.Thread(target=getVideoContinuous, daemon=True)
    streamer_thread = threading.Thread(target=streamer.run, daemon=True)
    uart_thread = threading.Thread(target=uart.loop, daemon=True)
    image_processing_thread = threading.Thread(target=imageProcessingLoop, daemon=True)

    threads.append(video_thread)
    threads.append(streamer_thread)
    threads.append(uart_thread)
    threads.append(image_processing_thread)
    
    for thread in threads:
        thread.start()
    #streamer.run()
    streamer.emitDataPeriodically()

    for thread in threads:
        thread.join()


