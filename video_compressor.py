import time
import redis
import json
import os
import cv2
import subprocess
import requests
import numpy as np
from mqtt_pub_sub import MqttClient

CAMERA_REQUEST_VID_WIDTH = 640
CAMERA_REQUEST_VID_HEIGHT = 480
OUTPUT_RATE = 20
VIDEO_SERVER_PATH = "/cloudapp/video/"
redis_host = os.environ.get('REDIS_HOST', 'localhost')
mosquitto_host = os.environ.get('MOSQUITTO_HOST', 'localhost')
rest_api = os.environ.get('REST_API', 'localhost')
REST_URL = "http://{}:3000/api/v1/alerts".format(rest_api)

r = redis.StrictRedis(host=redis_host, port=6379, db=0)

def send_alerts(payload):
    r = requests.post(REST_URL, headers={"ContentType": "application/json"}, json=payload)
    if r.status_code == 201:
        print("Record id {} created in mongodb".format(r.json().get("id")))
    else:
        print("Failed to update record (timestamp: {}) to DB ".format(payload.get("timestamp")))


def frames2video(cam_id, timestamp):
    start = time.time()
    filename = os.path.join(VIDEO_SERVER_PATH, "cam{}_{}.mp4".format(cam_id, timestamp))
    print(filename)
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = 0x00000021
    video_writer = cv2.VideoWriter(filename, fourcc, OUTPUT_RATE, (CAMERA_REQUEST_VID_WIDTH, CAMERA_REQUEST_VID_HEIGHT))

    key = "cam{}".format(cam_id)
    #print(key, timestamp, timestamp-10000, timestamp+10000)
    obj_lst = r.zrangebyscore(key, timestamp-8000, timestamp+8000)
    print("Video length: {} seconds".format(len(obj_lst)//OUTPUT_RATE))
    for frame in obj_lst:
        nparr = np.fromstring(frame, np.uint8)
        f = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        video_writer.write(f)

    video_writer.release()
    #mid = time.time()
    #convert2mp4(filename)
    end = time.time()
    print("Time consumed for converting {} is {} seconds".format(filename, end-start))


def on_message(client, userdata, message):
    # print("%s %s" % (message.topic, message.payload))
    payload = json.loads(message.payload.decode())
    print(payload)
    try:
        frames2video(payload['camera_id'], payload['timestamp'])
        send_alerts(payload)
    except Exception as e:
        # the exception must be handled otherwise it will quit the callback
        print(e.message)


mqttc = MqttClient(host=mosquitto_host, name="compressor", sub_only=True)
mqttc.start()
mqttc.subscribe("detected_objects", on_message=on_message)


try:
    while True:
        time.sleep(0.1)  
except KeyboardInterrupt:
    mqttc.stop()
