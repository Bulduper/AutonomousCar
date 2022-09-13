telemetry = dict(speed=0, speed_limit=0, angle=0, pv="speed", bat_vol=0, pos=0.0)
state = dict(followLane = False, detectSigns = False, respectSigns = False, parkingMode = False, avoidObstacles = False, undistort = False)
config = dict(speed_kP=0,speed_kI=0,speed_kD=0,pos_kP=0,pos_kI=0,pos_kD=0, state=state)
distance = [0,0,0,0,0,0]

def getTelemetryChanges(relTo:dict) -> dict:
    #return only key,value pairs that have changed relative to relTo
    newdict = dict()
    for k in telemetry.keys():
        if (k in relTo and relTo[k] != telemetry[k]) or k not in relTo:
            newdict[k] = telemetry[k]
    return newdict

def getModifiedProperties(of:dict, relTo: dict):
    #return only key,value pairs that have changed relative to relTo
    newdict = dict()
    for k in of.keys():
        if (k in relTo and relTo[k] != of[k]) or k not in relTo:
            newdict[k] = of[k]
    return newdict