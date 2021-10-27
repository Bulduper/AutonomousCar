import time
import uart_module as uart

def turn(angle):
    uart.writeCommand("T",angle)
    #stm32.write("T{0}".format(angle).encode())

def speed(speed_cmps):
    uart.writeCommand("S",speed_cmps)
    #stm32.write("S{0}".format(speed_cmps).encode())

def requestEnvironment(samples=1):
    #stm32.write("E{0}".format(samples).encode())
    uart.writeCommand("E",samples)