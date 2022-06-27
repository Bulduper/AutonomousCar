import serial
import time

stm32 = serial.Serial(
    port = '/dev/ttyTHS1',
    baudrate = 115200,
    # bytesize = serial.EIGHTBITS,
    # parity = serial.PARITY_NONE,
    # stopbits = serial.STOPBITS_ONE,
    timeout = 0,


)
print(stm32.name)

for i in range(10):
    stm32.write("S0\n".encode())
    stm32.write("S0\n".encode())
    # stm32.write("S100\n".encode())
    # time.sleep(0.0001)


stm32.close()

# while True:
#     try:
#         value = input('Enter the command to be sent to robot: \n')
#         print(f'You entered {value} and its type is {type(value)}')
#         stm32.write(value.encode())
#         data = stm32.readline()
#         if data:
#            print(data)
#         #time.sleep(1)
#     except Exception as e:
#         print(e)
#         stm32.close()
#         break
        
