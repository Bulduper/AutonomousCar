import time
import uart_module as uart


def turn(angle):
    uart.writeCmdBuffered("T",angle)
    #stm32.write("T{0}".format(angle).encode())

def speed(speed_mmps):
    uart.writeCmdBuffered("S",speed_mmps)
    #stm32.write("S{0}".format(speed_mmps).encode())

def position(rel_position_mm):
    uart.writeCmdBuffered("P",rel_position_mm)
    
def requestEnvironment(samples=1):
    #stm32.write("E{0}".format(samples).encode())
    uart.writeCmdBuffered("E",samples)

def requestTelemetry():
    uart.writeCmdBuffered("?")

def setLED(led1=False, led2=False, led3=False):
    command_val = int(led3)<<2 | int(led2)<<1 | int(led1)
    uart.writeCmdBuffered("L",command_val)