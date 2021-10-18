import serial


stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,


)

def turn(angle):
    stm32.write("T{0}".format(angle).encode())

def speed(speed_cmps):
    stm32.write("S{0}".format(speed_cmps).encode())