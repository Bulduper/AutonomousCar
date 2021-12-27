from flask_socketio import SocketIO, send
import redis
import threading
import base64
import cv2
import time 
import json

socketio = SocketIO(message_queue='redis://localhost:7777')
r= redis.Redis(host='localhost', port=7777, db=0)
ps = r.pubsub()
ps.subscribe('settings')
ps.subscribe('capture')
ps.subscribe('event')

#data from App parsing frequency
parse_freq = 5.0

json_dict = dict()

requestedImgKeys = []

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

def emitDataToApp():
    emit('robot_info',json_dict)
    threading.Timer(0.2,emitDataToApp).start()

def emitImages(imgDict, scale=1.0):
    imagesToSend = dict()
    for imgKey in imgDict.keys():
        if imgKey in requestedImgKeys:
            imgDict[imgKey] = cv2.resize(imgDict[imgKey], (0, 0), None, scale, scale)
            imagesToSend[imgKey] = encodeFrame(imgDict[imgKey])
        else:
            imagesToSend[imgKey]=None
    if imagesToSend: emit('images',imagesToSend)
    
def listenForEvents(func_on_event):
    message = ps.get_message()
    #ignore first 'subscribed' message
    if message and message['type']!='subscribe':
        # print('Event received', message)
        func_on_event(message['channel'].decode("utf-8"),json.loads(message['data'].decode("utf-8")))
    threading.Timer(1.0/parse_freq,listenForEvents,args=(func_on_event,)).start()
