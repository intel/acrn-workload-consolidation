#!/usr/bin/env python
from flask import Flask, render_template, Response
import time
from detection import get_frame, mqttc


app = Flask(__name__)


def gen():
    n_frames = 0
    fps = 0
    start = time.time()
    while True:
        n_frames += 1
        frame = get_frame()
        if not frame:
            continue
        fps = n_frames / (time.time() - start)
        if n_frames % 10 == 0:
            print(str(fps) + " FPS")
            n_frames = 0
            start = time.time()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def video_feed():
        return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
