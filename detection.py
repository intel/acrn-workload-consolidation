import sys
import os
import json
import cv2
import numpy as np
import redis
import tensorflow as tf

sys.path.append(".")

from object_detection.utils import label_map_util
from object_detection.utils import ops as utils_ops
from object_detection.utils import visualization_utils as vis_util
from mqtt_pub_sub import MqttClient


#PATH_TO_CKPT = "pre-trained-models/bigfoot/frozen_inference_graph.pb"
#PATH_TO_LABELS = "pre-trained-models/bigfoot/pascal_label_map.pbtxt"
#NUM_CLASSES = 2
redis_host = os.environ.get('REDIS_HOST', 'localhost')
mosquitto_host = os.environ.get('MOSQUITTO_HOST', 'localhost')
PATH_TO_CKPT = "/mobilenet/ssd_mobilenet_v1_coco_2017_11_17/frozen_inference_graph.pb"
PATH_TO_LABELS = "/streamapp/object_detection/data/mscoco_label_map.pbtxt"
NUM_CLASSES = 90
detection_set_string = os.environ.get('DETECTION_SET')
print(redis_host, mosquitto_host, detection_set_string)
DETECTION_SET =  [int(s) for s in detection_set_string.split(',')] if detection_set_string else [77, 47] # cup and cell phone
ALERT_INTERVAL = 10 * 1000 # 5 seconds
DETECT_THRESHOLD = 0.5

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)

sess = tf.Session(graph=detection_graph)


def run_inference_for_single_image(image, sess, graph):
   # Get handles to input and output tensors
   ops = graph.get_operations()
   all_tensor_names = {output.name for op in ops for output in op.outputs}
   tensor_dict = {}
   for key in [
       'num_detections', 'detection_boxes', 'detection_scores',
       'detection_classes', 'detection_masks'
   ]:
       tensor_name = key + ':0'
       if tensor_name in all_tensor_names:
           tensor_dict[key] = graph.get_tensor_by_name(tensor_name)
   if 'detection_masks' in tensor_dict:
       # The following processing is only for single image
       detection_boxes = tf.squeeze(tensor_dict['detection_boxes'], [0])
       detection_masks = tf.squeeze(tensor_dict['detection_masks'], [0])
       # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
       real_num_detection = tf.cast(tensor_dict['num_detections'][0], tf.int32)
       detection_boxes = tf.slice(detection_boxes, [0, 0], [real_num_detection, -1])
       detection_masks = tf.slice(detection_masks, [0, 0, 0], [real_num_detection, -1, -1])
       detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
           detection_masks, detection_boxes, image.shape[0], image.shape[1])
       detection_masks_reframed = tf.cast(
           tf.greater(detection_masks_reframed, 0.5), tf.uint8)
       # Follow the convention by adding back the batch dimension
       tensor_dict['detection_masks'] = tf.expand_dims(
           detection_masks_reframed, 0)
   image_tensor = graph.get_tensor_by_name('image_tensor:0')

   # Run inference
   output_dict = sess.run(tensor_dict,
                          feed_dict={image_tensor: np.expand_dims(image, 0)})

   # all outputs are float32 numpy arrays, so convert types as appropriate
   output_dict['num_detections'] = int(output_dict['num_detections'][0])
   output_dict['detection_classes'] = output_dict[
       'detection_classes'][0].astype(np.uint8)
   output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
   output_dict['detection_scores'] = output_dict['detection_scores'][0]
   if 'detection_masks' in output_dict:
       output_dict['detection_masks'] = output_dict['detection_masks'][0]
   return output_dict

r = redis.StrictRedis(host=redis_host, port=6379, db=0)
mqttc = MqttClient(host=mosquitto_host, name="detection", pub_only=True)
mqttc.start()
last_timestamp = {}


def get_detected_classes(boxes, classes, scores):
    detected = []
    for i in range(boxes.shape[0]):
        if not scores is None and scores[i] > DETECT_THRESHOLD:
            if not classes[i] in DETECTION_SET: continue
            if not classes[i] in detected: detected.append(int(classes[i])) 
    return detected        


def get_frame():
    dic = r.hgetall('cam1-current')
    nparr = np.fromstring(dic[b'frame'], np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #frame = pickle.loads(dic[b'frame'])
    ts = int(dic[b'timestamp'])
    # frame = pickle.loads(r.get('img'))
    output_dict = run_inference_for_single_image(frame, sess, detection_graph)
    # print(output_dict)
    vis_util.visualize_boxes_and_labels_on_image_array(
        frame,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        instance_masks=output_dict.get('detection_masks'),
        use_normalized_coordinates=True,
        line_thickness=8)
    ret, frame = cv2.imencode('.jpg', frame)
    class_ids = get_detected_classes(output_dict['detection_boxes'], output_dict['detection_classes'], output_dict['detection_scores'])
    if class_ids:
        # print(class_ids)
        publish = False
        for cid in class_ids:
            if last_timestamp.get(cid) is None:
                #print("Set class timestamp for class {} and sent alert.".format(cid))
                last_timestamp[cid] = ts
                publish = True
                break
            elif ts - last_timestamp.get(cid) <= ALERT_INTERVAL: continue
            else:
                last_timestamp[cid] = ts
                publish = True
                break
        if publish:
            data = { 
                        'timestamp': ts,
                        'class_id': class_ids,
                        'camera_id': 1
                    }
            print("Sent alert for class {} at {} {}.".format(cid, ts, last_timestamp.get(cid)))
            mqttc.publish(topic="detected_objects", msg=data)
    return frame.tostring()

