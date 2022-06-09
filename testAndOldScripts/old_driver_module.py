import time
import testAndOldScripts.old_uart_module as uart

global sensors
sensors = []

def turn(angle):
    uart.writeCmdBuffered("T",angle)
    #stm32.write("T{0}".format(angle).encode())

def speed(speed_mmps):
    uart.writeCmdBuffered("S",speed_mmps)
    #stm32.write("S{0}".format(speed_mmps).encode())
def setSpeedLimit(limit):
    uart.writeCmdBuffered("s",limit)

def position(rel_position_mm):
    uart.writeCmdBuffered("P",rel_position_mm)

#request distance measurements, average of {sample} samples
def requestDistance(samples=1):
    uart.writeCmdBuffered("E",samples)

def requestTelemetry():
    uart.writeCmdBuffered("?")

def setLED(led1=False, led2=False, led3=False):
    command_val = int(led3)<<2 | int(led2)<<1 | int(led1)
    uart.writeCmdBuffered("L",command_val)

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