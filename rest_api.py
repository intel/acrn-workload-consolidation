import math
import os
import pytz
import time
import datetime
from flask import Flask, jsonify, request, Response, abort, send_file
#from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from flask_cors import CORS
from bson.json_util import dumps
import traceback
#from flask_socketio import SocketIO
#from flask_socketio import SocketIO, emit, send, disconnect
from flask_sse import sse
from concurrent.futures import ThreadPoolExecutor


executor = ThreadPoolExecutor(1)

# create an Instance of Flask
app = Flask(__name__, static_url_path='')
"""random secret key"""
KEY_SIZE = 32
SECRET_KEY = os.urandom(KEY_SIZE)
app.config['SECRET_KEY'] = SECRET_KEY
MONGO_DB = 'edge2cloud'
MONGO_HOST = os.environ.get('MONGO_HOST', 'localhost')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
print(MONGO_HOST, REDIS_HOST)
cors = CORS(app, resources={r"/api/v1/*": {"origins": "*"}, 
                            r"/stream": {"origins": "*"},
                            r"/*":{"origins": "*"}})
#socketio = SocketIO(app)
conn = MongoClient(hostname=MONGO_HOST, port=MONGO_PORT, replicaSet=True)
db = conn[MONGO_DB]
app.config["REDIS_URL"] = "redis://{}".format(REDIS_HOST)

app.register_blueprint(sse, url_prefix="/stream")


@app.route("/api/v1/count", methods=['GET'])
def get_alerts_count():
    tz_str = request.args.get('tz')
    # print(tz_str)
    if not tz_str in pytz.all_timezones:
        abort(400)
    time_now = time.time()
    start_time = (time_now - 4*60*60) * 1000
    tz = pytz.timezone(tz_str)
    dt = datetime.datetime.fromtimestamp(time_now, tz)
    hour = dt.hour
    #labels = [ get_hour(hour-4) , get_hour(hour-3), get_hour(hour-2), get_hour(hour-1), hour ]
    labels = [ get_hour(hour-h) for h in range(4, -1, -1)]

    #start_time = 1546504974674
    pipeline = [
        {"$match": {"timestamp": {"$gte" : start_time}}},
        {
            "$project" : {
                "_id" : "$_id",
                "class_id": 1,
                "dt" : {"$add": [datetime.datetime(1970, 1, 1, 0, 0, 0), "$timestamp"]}
            },
        },
        {
            "$project" : {
                "_id" : "$_id",
                "class_id": 1,
                "hour" : {"$hour": {"date": "$dt", "timezone": tz_str}}
            },
        },    
        {"$unwind": "$class_id" },
        {"$group": { "_id": {"hour": "$hour", "class": "$class_id"}, "count": { "$sum": 1 }}}
    ]
    try:
        count = list(db.alerts.aggregate(pipeline))
        data = {}
        for cn in count:
            cls_id = cn["_id"]["class"]
            if not cls_id in data:
                data[cls_id] = [0] * 5
            if cn["_id"]["hour"] in labels:
            	data[cls_id][labels.index(cn["_id"]["hour"])] = cn["count"]
        #print(result)
        return dumps({"labels": labels, "data": data})
    except:
        traceback.print_exc()
        return jsonify(error="Internal server error"), 500


def get_hour(hour):
    return (24 + hour) if (hour < 0) else hour


@app.route("/api/v1/alerts", methods=['POST'])
def create_alerts():
    """
       Function to create alerts.
    """
    try:
        # validate post json data
        content = request.json
        print(content)
        if not content: raise ValueError("Empty value")
        if not 'timestamp' in content or not 'camera_id' in content or not 'class_id' in content: raise KeyError("Invalid dictionary keys")
        if not isinstance(content.get('timestamp'), int): raise TypeError("Timestamp must be in int64 type")
        if not isinstance(content.get('camera_id'), int): raise TypeError("Camera_id must be in int32 type")
        class_id = content.get('class_id')
        if not isinstance(class_id, list): raise TypeError("Class_id must be an array")
        for val in class_id:
            if not isinstance(val, int): raise TypeError("Array class_id values must be in int32 type")
    except (ValueError, KeyError, TypeError) as e:
        traceback.print_exc()
        resp = Response({"Json format error"}, status=400, mimetype='application/json')
        return resp
    try:
        record_created = db.alerts.insert_one(content)
        return jsonify(id=str(record_created.inserted_id)), 201
    except:
        #traceback.print_exc()
        return jsonify(error="Internal server error"), 500


@app.route("/api/v1/alerts", methods=['GET'])
def get_alerts():
    """
        Funtion to get latest 50 alerts 
    """
    start = request.args.get('page', 1)
    limit = request.args.get('per_page', 5)
    #print(isinstance(start, int), limit)
    try:
        start = int(start)
        limit = int(limit)
    except:
        abort(400)
    try:
        #alts = list(mongo.db.alerts.find().sort('timestamp', -1).limit(50))
        alts = get_paginated_alerts(request.base_url, int(start), int(limit))
        #print(alts)
        return dumps(alts)
    except:
        traceback.print_exc()
        return jsonify(error="Internal server error"), 500


def get_paginated_alerts(url, start, limit):
    result = list(db.alerts.find().skip((start-1)*limit).limit(limit).sort('timestamp', -1))
    count = db.alerts.find().count()
    if start < 1:
        abort(404)
    # construct response
    obj = {}
    obj['current_page'] = start
    obj['per_page'] = limit
    obj['total'] = count
    obj['from'] = (start - 1) * limit + 1
    obj['to'] = start * limit
    obj['last_page'] = math.ceil(count/limit)
    # make URLs
    if start == 1:
        obj['prev_page_url'] = ''
    else:
        obj['prev_page_url'] = url + '?page=%d&per_page=%d' % (start - 1, limit)
    # make next url
    if start*limit + limit > count:
        obj['next_page_url'] = ''
    else:
        obj['next_page_url'] = url + '?page=%d&per_page=%d' % (start + 1, limit)
    obj['data'] = result
    return obj


def notification():
    try:
        #for insert_change in db.collection.alerts.watch([{'$match': {'operationType': 'insert'}}]):
        with app.app_context():
            for insert_change in db.alerts.watch([{'$match': {'operationType': 'insert'}}]):
                #print(insert_change)
                sse.publish(dumps(insert_change), type="notification")
        return "Notification sent"
    except PyMongoError:
        # We know it's unrecoverable: todo resume connection
        print('connection closed unexpectedly.') 


@app.route('/video', methods=['GET'])
def media():
    # todo: take camera id as param
    camID = request.args.get('cam', 1)
    ts = request.args.get('ts', "")
    return send_file("video/cam{}_{}.mp4".format(camID, ts))


@app.before_first_request
def task():
    print("before request.")
    executor.submit(notification)
    return "One job was launched in background!"  


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
