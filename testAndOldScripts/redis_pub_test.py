import redis

r = redis.Redis(host='localhost',port=7777, db=0)
ps = r.pubsub()

while True:
    try:
        value = input('Enter the command to be sent to robot: \n')
        print(f'You entered {value} and its type is {type(value)}')
        r.publish('uartOut',value)
        #time.sleep(1)
    except Exception as e:
        print(e)
        break