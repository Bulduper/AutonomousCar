import redis
import time

r= redis.Redis(host='localhost', port=7777, db=0)
ps = r.pubsub()
ps.subscribe('event')
msg = ps.get_message()
while True:
    msg = ps.get_message()
    if msg:
        print(msg)
    time.sleep(0.001)