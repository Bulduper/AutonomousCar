import threading
from flask import Flask, render_template, Response, request, json
from g_pipeline import gstreamer_pipeline
import cv2
import numpy as np
import time

#starts flask server and starts processing camera frames

outputFrame = [None,None]
lock = threading.Lock()
app=Flask(__name__)



def on_pic(func):
    global take_pic
    take_pic = func  


@app.route('/', methods=['GET','POST'])
def index():
    global take_pic
    if request.method == 'POST':
        #take_pic()

        if request.form.get('demo'):
            volume = request.form.get('demo')
            print('volume:', volume)
            #return jsonify({'volume': volume})
            return json.dumps({'volume': volume})
    return render_template('index.html')

def get_vid():
    while cap:
        ret_val, img = cap.read()
        if ret_val:
            #img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
            set_frame(img)
    cap.release()

def set_frame(frame, which = 0, scale = 0.4):
    global outputFrame, lock
    frame = cv2.resize(frame, (round(frame.shape[1]*scale), round(frame.shape[0]*scale)))
    with lock:
        outputFrame[which] = frame.copy()

def gen_frame_1():
    global outputFrame, lock
    while True:
        with lock:
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
        with lock:
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

def start_stream():
    app.run(host='0.0.0.0', threaded=True)
    #socketio.run(app,host='0.0.0.0',debug=True)

if __name__ == '__main__':
    global cap
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    time.sleep(2.0)
    t = threading.Thread(target=get_vid)
    t.daemon = True
    t.start()
    start_stream()


