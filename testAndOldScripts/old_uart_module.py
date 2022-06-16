import time
import serial
from collections import OrderedDict
# import web_app.streamer_new_noclass as streamer

stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,
)

dict_queue = OrderedDict()

func_on_received = None

#add to buffer (ordered dict)
def writeCmdBuffered(prefix,data=""):
    if prefix not in dict_queue:
        dict_queue[prefix]=data
    
def onReceived(func):
    global func_on_received
    func_on_received = func

def receiveAsync():
    global func_on_received
    if stm32.inWaiting() > 0 and func_on_received is not None:
        received = stm32.readline()
        func_on_received(received)
        #return received
    #return None

#every 100ms try to send oldest record (command) from ordered dict
def loop():
    while True:
        receiveAsync()
        sendFromQueue()
        time.sleep(0.1)

#send the latest command from queue
def sendFromQueue():
    if len(dict_queue)!=0:
        key,value = dict_queue.popitem(last=False)
        # print("sending...",key, value)
        stm32.write("{0}{1}\n".format(key,value).encode())
        
