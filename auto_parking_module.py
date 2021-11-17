import queue

from cv2 import threshold
import driver_module as driver
import time
import uart_module as uart

module_enabled = False

find_left = True
find_right = False
#resolution in cm/sample (measurement every N cm of forward distance)
resolution=3
#how far back will the measurements be remembered [cm]
along_dist = 60
#depth of parking space in cm
depth_thr = 20
length_thr = 35

left_map = queue.Queue(along_dist/resolution)
right_map = queue.Queue(along_dist/resolution)

left_len = -resolution
right_len = -resolution
#in cmps
driving_speed = 0.0

space_found = False
awaiting = False

SEQUENCE = [('P',200), ('T',60), ('P',-300), ('T',-60), ('P',-300), ('T',0), ('P',80)]
seq_step = 0

def enable():
    global module_enabled 
    module_enabled = True

def disable():
    global module_enabled 
    module_enabled = False

def update(dist_list):
    # print("Distance readings:")
    # print(dist_list[3],dist_list[0])
    # print(dist_list[4],dist_list[1])
    # print(dist_list[5],dist_list[2])
    # print("----------------")
    if left_map.full():
        left_map.get()
        right_map.get()
    left_map.put(dist_list[4])
    right_map.put(dist_list[1])
    # for item in list(left_map.queue):
    #     print(item)
    # #print(list(left_map.queue))
    # print('############################')
    findParkingSpace(dist_list[4],dist_list[1])

def setSpeed(speed):
    global driving_speed
    driving_speed = speed/10.0

def loop():
    while True:
        if module_enabled:
            if driving_speed != 0.0:
                interval = resolution/abs(driving_speed)
                driver.requestEnvironment()
                time.sleep(interval)
            parkSequence()

def findParkingSpace(left_depth, right_depth):
    global left_len, right_len, space_found
    if left_len>= depth_thr :
        left_len += resolution
    else:
        left_len = -resolution
    
    if right_len>= depth_thr :
        right_len += resolution
    else:
        right_len = -resolution


    if left_len > length_thr and seq_step==0:
        print("PARKING SPACE FOUND!!!!")
        space_found = True
        driver.setLED(led1=True)
        return True
    return False



def parkSequence():
    global space_found, awaiting, seq_step, SEQUENCE
    if space_found and awaiting == False:
        uart.writeCmdBuffered(SEQUENCE[seq_step][0],SEQUENCE[seq_step][1])
        awaiting = True
        seq_step += 1
        if seq_step == len(SEQUENCE): space_found = False


