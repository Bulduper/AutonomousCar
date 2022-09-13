import engineio
from flask import Flask, render_template, Response, request, json
from flask_socketio import SocketIO
from flask_socketio import send, emit
import redis

import time
import threading
import base64
import cv2

#sio = engineio.Server(async_mode='threading')
app = Flask(__name__)
#app.wsgi_app = engineio.WSGIApp(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app,message_queue="redis://localhost:7777", async_mode='threading')#, logger=True, engineio_logger=True)
r= redis.Redis(host='localhost', port=7777, db=0)
lock = threading.Lock()
frame = None
json_dict = dict()
x=3

emiting_period = 0.5

@socketio.on('event')
def onModeEvent(data):
    #assuming type of data is string (stringified JSON)
    if data:
        r.publish('event',data)


@socketio.on('connection')
def connection(data):
    global x
    print('received message: ' + str(data))
    # r.publish('event', {'connected': true})
    # while True:
    #     json_dict['speed']=x*3
    #     json_dict['angle']=x+5 
    #     x+=1
    #     emit('telemetry',json_dict)
    #     socketio.sleep(0.5)
# @socketio.on('logs')
# def sendLogsToClient(data):

# @socketio.on('get data')
# def send_data():
#     global x
#     json_dict['speed']=x*3
#     json_dict['angle']=x+5 
#     x+=1
#     emit('telemetry',json_dict)
#     socketio.sleep(0)

@app.route('/', methods=['GET','POST'])
def index():
    return render_template('index_all_io.html')

@app.route('/settings', methods=['GET','POST'])
def settings():
    return render_template('settings.html')

@app.route('/map', methods=['GET','POST'])
def spaceMap():
    return render_template('space_map.html')
# @app.route('/video1')
# def video_feed_1():
#     return Response(makeFrame(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

def makeFrame():
    global lock, frame
    while True:
        with lock:
            if frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", frame)

            if not flag:
                continue

        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
            bytearray(encodedImage) + b'\r\n')
        #important for good performance
        socketio.sleep(0.1)

def emitDataPeriodically():
    threading.Timer(emiting_period,emitDataPeriodically).start()
    if json_dict:
        socketio.emit('robotInfo',json_dict)

def setFrame(img,scale=0.5):
    global frame
    # frame = cv2.resize(img,(round(img.shape[1]*scale), round(img.shape[0]*scale)))
    frame = cv2.resize(img,320, 240)
    #with lock?

def emit(topic, json):
    socketio.emit(topic,json)
    #socketio.sleep(0)

def run():
    #app.run(host="0.0.0.0")
    socketio.run(app,host='0.0.0.0')

if __name__ == "__main__":
    run()