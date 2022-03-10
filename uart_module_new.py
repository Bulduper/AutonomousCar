import json
import serial
import redis
import argparse

parser = argparse.ArgumentParser(description='This script listens to uartOut channel of redis-server,\
 sends the data through UART, receives data from UART and publishes it to uartIn channel.')

parser.add_argument("-d","--debug", action='store_true',help="Enabled debug - print in console")
parser.add_argument("-l","--logs",action='store_true',help="Enable logging broadcasting (only with debug flag!) over REDIS on channel 'logs'")
parser.add_argument("-p","--port", default=7777, help="Redis server port (default 7777)")
args = parser.parse_args()

r = redis.Redis(host='localhost',port=args.port, db=0)
ps = r.pubsub()
ps.subscribe('uartOut')

DEBUG = args.debug
LOG_PUBLISH = args.logs

stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,
)



def transmitUartMessage(serial,message):
    global DEBUG
    if message is None: return
    if DEBUG: _print('Sending normal: {0}'.format(message))
    serial.write("{0}\n".format(message).encode())
    return

def transmitUartKeyValue(serial,key,value=''):
    global DEBUG
    if key is None: return
    if DEBUG: _print('Sending dict: {0}{1}'.format(key,value))
    serial.write("{0}{1}\n".format(key,value).encode())
    return

def transmitUart(serial, message):
    jsonDict = is_json(message)
    if jsonDict:
        for key in jsonDict:
            transmitUartKeyValue(serial,key,jsonDict[key])
    else:
        transmitUartMessage(serial,message)

def _print(log):
    global LOG_PUBLISH
    print(f'UART: {log}')
    if LOG_PUBLISH: r.publish('logs',f'UART: {log}')

def is_json(myjson):
    try:
        dic = json.loads(myjson)
    except ValueError as e:
        return False
    return dic

if DEBUG: _print('Uart module (process) started with debugging')

#MAIN LOOP
while True:
    #Listen for received (UART)
    if stm32.inWaiting() > 0:
        received = stm32.readline()
        r.publish('uartIn',received)
        if DEBUG: _print(f'Received: {received.decode("utf-8")}'.rstrip())
    
    #Listen for transmit (REDIS)
    message = ps.get_message()
    if message and message['type']!='subscribe': 
        if message['data'].decode("utf-8") != '':
            transmitUart(stm32, message['data'].decode("utf-8"))
    


