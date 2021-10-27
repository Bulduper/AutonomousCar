import serial


stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,
)

def writeCommand(prefix,data=""):
    stm32.write("{0}{1}".format(prefix,data).encode())

def receiveAsync():
    if stm32.inWaiting() > 0 :
        received = stm32.readline()
        return received
    return None