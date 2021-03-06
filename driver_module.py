import json
import threading
import redis
from collections import OrderedDict

sensors = []
dict_queue = OrderedDict()

r= redis.Redis(host='localhost', port=7777, db=0)
ps = r.pubsub()
ps.subscribe('uartIn')

LISTEN_FREQ = 5.0

def setTurn(angle):
    publishKeyValue("T",angle)

def setSpeed(speed_mmps):
    publishKeyValue("S",speed_mmps)

def setSpeedLimit(limit):
    publishKeyValue("s",limit)

def position(rel_position_mm):
    publishKeyValue("P",rel_position_mm)

#request distance measurements, average of {sample} samples
def requestDistance(samples=1):
    publishKeyValue("E",samples)

def requestTelemetry():
    publishKeyValue("?")

def setLED(led1=False, led2=False, led3=False):
    command_val = int(led3)<<2 | int(led2)<<1 | int(led1)
    publishKeyValue("L",command_val)

def frontDistance():
    global sensors
    if sensors:
        return min(sensors[3],sensors[0])

def rearDistance():
    global sensors
    if sensors:
        return min(sensors[2],sensors[5])

def checkForObstacles(trigger):
    if frontDistance() < trigger: return 'front'
    elif rearDistance() <trigger: return 'rear'
    return 'none' 


def listenToUart():
    # message = ps.get_message()
    message = r.get('uart')
    # if message and message['type']!='subscribe':
    #     return message['data'].decode("utf-8")
    if message:
        return message.decode("utf-8")
    return None

def listenContinuously(parserFunction):
    global LISTEN_FREQ
    data = listenToUart()
    #request all the info from robot by UART
    requestTelemetry()
    if data:
        parserFunction(data)
    threading.Timer(1.0/LISTEN_FREQ,listenContinuously,args=(parserFunction,)).start()


def reactToSigns(detectedSigns):
    if 'speedlimit_50' in detectedSigns:
        print('Driver sets speed to 50')
        setSpeedLimit(50)
    else: setSpeedLimit(0)
    if 'stop_sign' in detectedSigns:
        print('Driver stops on stop sign')
        setSpeed(0)

def publishKeyValue(key,value=''):
    r.publish("uartOut",json.dumps(dict({key:value})))
    # r.publish("uartOut",json.loads)