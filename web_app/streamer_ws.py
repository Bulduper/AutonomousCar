from threading import Lock
from flask import Flask, render_template, Response, request
from g_pipeline import gstreamer_pipeline
import cv2
import numpy as np
import time
from flask_socketio import SocketIO, emit, disconnect

#starts flask server and starts processing camera frames
async_mode = None
outputFrame = [None,None]
app=Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app,async_mode=async_mode)
thread_lock = Lock()

def on_pic(func):
    global take_pic
    take_pic = func  


@app.route('/', methods=['GET','POST'])
def index():
    global take_pic
    if request.method == 'POST':
        take_pic()
    return render_template('index2.html', async_mode=socketio.async_mode)

def get_vid():
    while cap:
        ret_val, img = cap.read()
        if ret_val:
            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            set_frame(img)
    cap.release()

def set_frame(frame, which = 0, scale = 0.4):
    global outputFrame, thread_lock
    frame = cv2.resize(frame, (round(frame.shape[1]*scale), round(frame.shape[0]*scale)))
    #print('bef lock')
    with thread_lock:
        print('aft lock')
        outputFrame[which] = frame.copy()
        (flag, encodedImage) = cv2.imencode(".jpg", outputFrame[0])
        if flag:
            socketio.emit('video',{'image_data':encodedImage})
            print('VIDEO EvENT')

@socketio.on('video')
def asd():
    print('received on video')

def gen_frame_1():
    global outputFrame, lock
    while True:
        with thread_lock:
            if outputFrame[0] is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame[0])

            if not flag:
                continue

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')

def gen_frame_2():
    global outputFrame, lock
    while True:
        with thread_lock:
            if outputFrame[1] is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame[1])

            if not flag:
                continue

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')


@app.route('/video1')
def video_feed_1():
    return Response(gen_frame_1(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video2')
def video_feed_2():
    return Response(gen_frame_2(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/chuj', methods=['POST'])
def fun():
    print('chuj')

  
@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)

@socketio.on('slider')
def handle_message(data):
    im = cv2.imread('chessbrd7.jpg')
    cv2.imshow('asd',im)
    (flag, encodedImage) = cv2.imencode(".jpg", im)
    emit('video',{'image_data':encodedImage})
    print('slider: ' + data)

def start_stream():
    #app.run(host='0.0.0.0', threaded=True)
    socketio.run(app,host='0.0.0.0',debug=True)

# if __name__ == '__main__':
#     global cap
#     cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
#     time.sleep(2.0)
#     t = threading.Thread(target=get_vid)
#     t.daemon = True
#     t.start()
#     start_stream()


