#! /usr/bin/env python3

import cv2
import os
import sys
import time
import threading 
import queue 
import redis
from camera_processor import camera_processor 
from expire_processor import expire_processor 

CAMERA_INDEX = os.environ.get('CAMERA_SRC', 0)
if not isinstance(CAMERA_INDEX, int):
    if CAMERA_INDEX.isdigit():
        CAMERA_INDEX = int(CAMERA_INDEX)    
CAMERA_REQUEST_VID_WIDTH = 640
CAMERA_REQUEST_VID_HEIGHT = 480

CAMERA_QUEUE_PUT_WAIT_MAX = 0.001
CAMERA_QUEUE_FULL_SLEEP_SECONDS = 0.01

CAMERA_QUEUE_SIZE = 1
#ip_camera=os.environ['IP_CAMERA']
#cap = cv2.VideoCapture('rtsp://localhost:554/video.h264')
#cap = cv2.VideoCapture("http://localhost:8090/facstream.mjpeg")
redis_host = os.environ.get('REDIS_HOST', 'localhost')
r = redis.StrictRedis(host=redis_host, port=6379, db=0)
print(CAMERA_INDEX, redis_host)

def main():

    # Queue of camera images.  Only need two spots
    camera_queue = queue.Queue(CAMERA_QUEUE_SIZE)
    # camera processor that will put camera images on the camera_queue
    camera_proc = camera_processor(camera_queue, CAMERA_QUEUE_PUT_WAIT_MAX, CAMERA_INDEX,
            CAMERA_REQUEST_VID_WIDTH, CAMERA_REQUEST_VID_HEIGHT, CAMERA_QUEUE_FULL_SLEEP_SECONDS)
    camera_proc.start_processing()

    # start thread to expire zset members
    expire_proc = expire_processor(r, 'cam1', 30, 5)
    expire_proc.start()

    n_frames = 0
    start = time.time()
    try:
        while True:
            f = camera_queue.get()
            camera_queue.task_done()
            
            ts = int(time.time()*1000.0)
            serialized = cv2.imencode('.jpg', f)[1].tostring()
            val = {'frame': serialized, 'timestamp': ts}
            r.hmset('cam1-current', val)
            r.zadd('cam1', ts, serialized)
            
            n_frames += 1
            if n_frames % 10 == 0:
                # print("FPS: {}".format(n_frames / (time.time() - start)))
                n_frames = 0
                start = time.time()
    except KeyboardInterrupt:
        sys.exit()
    finally:
        print('stop camera thread')
        camera_proc.stop_processing()
        camera_proc.cleanup()
        print('stop redis expire thread')
        expire_proc.stop()
        expire_proc.join()


def frames2video(save_name):
    fps = 15
    fourcc = 0x00000021 
    video_writer = cv2.VideoWriter(save_name, fourcc, fps, (CAMERA_REQUEST_VID_WIDTH, CAMERA_REQUEST_VID_HEIGHT), isColor=True)
    obj_lst = r.zrangebyscore('cam1', 0, '+inf')
    for frame in obj_lst:
        video_writer.write(pickle.loads(frame))
    video_writer.release()


if __name__ == "__main__":
    main()
    #frames2video('video.mp4')
