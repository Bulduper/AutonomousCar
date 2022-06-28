telemetry = dict(speed=0, speed_limit=0, turn=0, pv="speed", bat_vol=0)
config = dict(speed_kP=0,speed_kI=0,speed_kD=0,pos_kP=0,pos_kI=0,pos_kD=0)
distance = [0,0,0,0,0,0]

def getTelemetryChanges(relTo:dict) -> dict:
    #return only key,value pairs that have changed relative to relTo
    newdict = dict()
    for k in telemetry.keys():
        if k in relTo and relTo[k] != telemetry[k]:
            newdict[k] = telemetry[k]
    return newdict