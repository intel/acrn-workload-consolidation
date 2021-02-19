#! /usr/bin/env python3
import threading
import time
import redis

class expire_processor(threading.Thread):
    def __init__(self, redis_inst, db_key, expire, interval):
        super().__init__()
        self.redis_inst = redis_inst
        self.db_key = db_key 
        self.expire = expire
        self.interval = interval 
        self.event = threading.Event()

    def run(self):
        while not self.event.is_set():
            self.redis_inst.zremrangebyscore(self.db_key, 0, int(time.time()*1000) - self.expire*1000)
            self.event.wait(self.interval)

    def stop(self):
        self.event.set()


def main():
    r = redis.Redis(host='localhost', port=6379)
    #r.zremrangebyscore('cam1', 0, int(time.time()*1000)-*1000)
    expire_proc = expire_processor(r, 'cam1', 30, 5)
    expire_proc.start()
    time.sleep(600)
    print('stop thread after 10 mins.')
    expire_proc.stop()
    expire_proc.join()


if __name__ == "__main__":
    main()
