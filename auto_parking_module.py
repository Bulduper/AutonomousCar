import queue
import driver_module as driver
import time

left_map = queue.Queue(100)
resolution=20
driving_speed = None
def scan(dist_list):
    print("Distance readings:")
    print(dist_list[3],dist_list[0])
    print(dist_list[4],dist_list[1])
    print(dist_list[5],dist_list[2])
    print("----------------")
    if left_map.full():
        left_map.get()
    left_map.put(dist_list[4])
    #print(list(left_map.queue))

def setSpeed(speed):
    global driving_speed
    driving_speed = speed

def mapAlong():
    while True:
        if driving_speed is not None:
            interval = resolution/driving_speed
            driver.requestEnvironment()
            time.sleep(interval)

