from flask_socketio import SocketIO, send
import redis
import threading
import base64
import cv2
import models
import json

socketio = SocketIO(message_queue='redis://localhost:7777')
r= redis.Redis(host='localhost', port=7777, db=0)

ps_serverToClient = r.pubsub()
ps_serverToClient.subscribe('settings')
ps_serverToClient.subscribe('capture')
ps_serverToClient.subscribe('event')

ps_clientToServer = r.pubsub()
ps_clientToServer.subscribe('logs')

#data from App parsing frequency
parse_freq = 5.0

#logs to Server sending frequency
logging_freq = 100.0

#other data sending frequency
to_server_freq = 5.0

json_dict = dict()
prev_telemetry = dict()

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
    global json_dict
    emit('robot_info',json_dict)
    json_dict = dict()
    threading.Timer(1.0/to_server_freq,emitDataToApp).start()

def emitUpdatedDatatoApp():
    global json_dict
    global prev_telemetry
    json_dict = models.getTelemetryChanges(prev_telemetry)
    prev_telemetry = models.telemetry.copy()
    if json_dict: emit('robot_info',json_dict)
    threading.Timer(1.0/to_server_freq,emitUpdatedDatatoApp).start()


def emitRequestedImages(imgDict:dict, scale=1.0):
    imagesToSend = dict()
    for imgKey in imgDict.keys():
        if imgKey in requestedImgKeys:
            img_resized = cv2.resize(imgDict[imgKey], (0, 0), None, scale, scale)
            imagesToSend[imgKey] = encodeFrame(img_resized)
        else:
            imagesToSend[imgKey]=None
    if imagesToSend: emit('images',imagesToSend)

def sendLogsToServer():
    message = ps_clientToServer.get_message()
    if message and message['channel'].decode("utf-8")=='logs' and message['type']!='subscribe':
        # print('Channel',message['channel'].decode("utf-8"), ' data: ',message['data'].decode("utf-8"))
        #To investigate!
        #If the logs come more often than this loop, msgs are piling up and it takes a lot of time to process all messages
        emit('logs',message['data'].decode("utf-8"))
    threading.Timer(1.0/logging_freq,sendLogsToServer).start()

def listenForEvents(func_on_event):
    message = ps_serverToClient.get_message()
    #ignore first 'subscribed' message
    if message and message['type']!='subscribe':
        # print('Event received', message)
        func_on_event(message['channel'].decode("utf-8"),json.loads(message['data'].decode("utf-8")))
    threading.Timer(1.0/parse_freq,listenForEvents,args=(func_on_event,)).start()
