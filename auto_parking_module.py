import queue

import driver_module as driver
import time
import uart_module as uart

module_enabled = False
space_mapping = True
find_and_park = True

find_left = True
find_right = False
gap_found_left = False
gap_found_right= False
#resolution in cm/sample (measurement every N cm of forward distance)
resolution=3
#how far back will the measurements be remembered [cm]
along_dist = 60
#depth threshold of parking space in cm
depth_thr = 20
#length threshold of parking space in cm
length_thr = 35

left_map = queue.Queue(along_dist/resolution)
right_map = queue.Queue(along_dist/resolution)

left_len = -resolution
right_len = -resolution
#in cmps
driving_speed = 0.0

interval_default = 1.0
space_found = False
awaiting = False
#parking sequence by command
SEQUENCE = [('s',100),('P',200), ('T',60), ('P',-300), ('T',-60), ('P',-300), ('T',0)]
#current sequence step
seq_step = 0
#sequence complete?
seq_done = False
#parking procedure started?
now_parking = False

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
    #if queue is full - all 'along_dist' is scanned
    if left_map.full():
        #pull the oldest measurements
        left_map.get()
        right_map.get()
    #push new measurements
    left_map.put(dist_list[4])
    right_map.put(dist_list[1])
    #if it's said we want automatically park on found space and the parking is not performed already
    if find_and_park and not now_parking:
        #check for free space
        findParkingSpace(dist_list[4],dist_list[1])
#set speed for calculations
def setSpeed(speed):
    global driving_speed,space_mapping
    driving_speed = speed/10.0

#main loop
def loop():
    global interval_default,space_mapping, gap_found_right, gap_found_left
    while True:
        driver.requestDistance()
        if module_enabled:
            if driving_speed==0.0:
                space_mapping = False
            elif not now_parking: 
                space_mapping = True
                interval = resolution/abs(driving_speed)                
            
            if find_and_park and gap_found_left and now_parking:
                parkSequence('left')

            if find_and_park and gap_found_right and now_parking:
                parkSequence('right')

            if now_parking and seq_done:
                gap_found_left = False
                gap_found_right = False
                interval = 0.3
                align()
        else: interval = interval_default
        time.sleep(interval)


def findParkingSpace(left_depth, right_depth):
    global left_len, right_len, gap_found_right, gap_found_left, now_parking
    if left_depth>= depth_thr :
        left_len += resolution
    else:
        left_len = -resolution
    
    if right_depth>= depth_thr :
        right_len += resolution
    else:
        right_len = -resolution


    if left_len > length_thr and seq_step==0:
        print("Parking place found on the left!")
        gap_found_left = True
        driver.setLED(led1=True)
        if find_left: now_parking=True

    if right_len > length_thr and seq_step==0:
        print("Parking place found on the right!")
        gap_found_right = True
        driver.setLED(led1=True)
        if find_right: now_parking=True
    return gap_found_right, gap_found_left

def parkSequence(side):
    global now_parking, awaiting, seq_step, SEQUENCE, seq_done
    if side== 'left' and awaiting == False:
        uart.writeCmdBuffered(SEQUENCE[seq_step][0],SEQUENCE[seq_step][1])
        awaiting = True
        seq_step += 1
        if seq_step == len(SEQUENCE): 
            # now_parking = False
            seq_done = True

#align between front and rear obstacle (equal distance)
def align():
    global now_parking, seq_done
    print('Aligning...')
    error = driver.frontDistance() - driver.rearDistance()
    if abs(error)>3.0:
        driver.speed(error*20.0)
    else:
        print('Aligning done!')
        now_parking = False
        seq_done = False
        driver.speed(0)
        driver.setSpeedLimit(0)
        return