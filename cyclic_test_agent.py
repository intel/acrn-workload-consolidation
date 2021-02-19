#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import division
import sys
import os
import pyinotify
import re
import time
import queue
import argparse
from json import dumps
from collections import Counter, OrderedDict
from mqtt_pub_sub import MqttClient


SchedLatQueueMax=10000
SchedLatQueueHead=0
SchedLatQueueTail=0
LastSchedLatQueueTail=0
SchedLatQueueLen = 0
SchedLatGlobLen = 0
LastSchedLatGlobLen = 0
SchedLatMin = 0xffffffff
SchedLatAvg = 0
SchedLatMax = 0
SchedLatMissRate10us = 0
SchedLatMissRate15us = 0
SchedLatMissRate20us = 0
SchedLatMissRate30us = 0

# matlab can process N points/second
LatencyDataProcessSpeed = 10000
SchedLatBufferMax = 100*SchedLatQueueMax/LatencyDataProcessSpeed
LatencyLogReadBlockSize = 1024 * 512
SchedLatHistWinSize = SchedLatQueueMax
LastLatencyLogSize = 0

SchedLatQueue = []
SchedLatBufferNum = 0

def generate_report(mqttc, debug):
    global SchedLatQueueLen, SchedLatQueueLen, SchedLatBufferNum, SchedLatSort, SchedLatQueueHead, SchedLatQueueMax, SchedLatQueueTail, SchedLatQueue, LastSchedLatGlobLen, SchedLatQueueLen, SchedLatMin, SchedLatAvg, SchedLatMax, SchedLatMissRate10us, SchedLatMissRate15us, SchedLatMissRate20us, SchedLatMissRate30us, LastSchedLatQueueTail
    if debug:
        print(len(SchedLatQueue), SchedLatQueueTail, SchedLatBufferNum)
    print("now {} Sched points".format(SchedLatQueueLen))
    #print("now {} OsTick points".format(OsTickLatQueueLen))
    print("=================================================================\n");
    if SchedLatQueueLen != 0:
        if SchedLatBufferNum == 0: return 
        #    continue
        # Compute the Sched Latency Distribution
        SchedLatSort = None
        if SchedLatQueueLen < SchedLatQueueMax:
            SchedLatQueueHead = 0
        else:
            SchedLatQueueHead = SchedLatQueueTail
            if SchedLatQueueHead >= SchedLatQueueMax - 1:
                SchedLatQueueHead = SchedLatQueueHead - SchedLatQueueMax

        if SchedLatQueueHead == 0:
            SchedLatSort = SchedLatQueue[0:SchedLatQueueLen]
        else:
            SchedLatSort = SchedLatQueue[SchedLatQueueHead:SchedLatQueueMax] + SchedLatQueue[0:SchedLatQueueTail]

        # Real-Time statistic since run
        SchedLatBufferSort = None
        #print(LastSchedLatQueueTail, SchedLatQueueTail)
        if LastSchedLatQueueTail < SchedLatQueueTail:
            SchedLatBufferSort = SchedLatQueue[LastSchedLatQueueTail:SchedLatQueueTail]
        elif LastSchedLatQueueTail >= SchedLatQueueTail:
            SchedLatBufferSort = SchedLatQueue[LastSchedLatQueueTail:SchedLatQueueMax] + SchedLatQueue[0:SchedLatQueueTail]

        BufferSchedLatMin = min(SchedLatBufferSort)
        BufferSchedLatMax = max(SchedLatBufferSort)
        BufferSchedLatAvg = round(sum(SchedLatBufferSort)/len(SchedLatBufferSort), 3)
        lenth=len(SchedLatBufferSort)
        #print("sum: {}, len: {}".format(sum(SchedLatBufferSort), lenth))
        BufferSchedLatMissDeadline10us=[i > 10000 for i in SchedLatBufferSort]
        BufferSchedLatMissRate10us=sum(BufferSchedLatMissDeadline10us)*100/lenth

        BufferSchedLatMissDeadline15us=[i > 15000 for i in SchedLatBufferSort]
        BufferSchedLatMissRate15us=sum(BufferSchedLatMissDeadline15us)*100/lenth
        BufferSchedLatMissDeadline20us=[i > 20000 for i in SchedLatBufferSort]
        BufferSchedLatMissRate20us=sum(BufferSchedLatMissDeadline20us)*100/lenth
        BufferSchedLatMissDeadline30us=[i > 30000 for i in SchedLatBufferSort]
        BufferSchedLatMissRate30us=sum(BufferSchedLatMissDeadline30us)*100/lenth
        if SchedLatMin > BufferSchedLatMin:
            SchedLatMin = BufferSchedLatMin
        if SchedLatMax < BufferSchedLatMax:
            SchedLatMax = BufferSchedLatMax

        SchedLatAvg = round((SchedLatAvg*LastSchedLatGlobLen + BufferSchedLatAvg*SchedLatBufferNum)/(LastSchedLatGlobLen + SchedLatBufferNum), 3)
        SchedLatMissRate10us = (SchedLatMissRate10us*LastSchedLatGlobLen + BufferSchedLatMissRate10us*SchedLatBufferNum)/(LastSchedLatGlobLen + SchedLatBufferNum)
        SchedLatMissRate15us = (SchedLatMissRate15us*LastSchedLatGlobLen + BufferSchedLatMissRate15us*SchedLatBufferNum)/(LastSchedLatGlobLen + SchedLatBufferNum)
        SchedLatMissRate20us = (SchedLatMissRate20us*LastSchedLatGlobLen + BufferSchedLatMissRate20us*SchedLatBufferNum)/(LastSchedLatGlobLen + SchedLatBufferNum)
        SchedLatMissRate30us = (SchedLatMissRate30us*LastSchedLatGlobLen + BufferSchedLatMissRate30us*SchedLatBufferNum)/(LastSchedLatGlobLen + SchedLatBufferNum)

        if debug:
            print("BufferSchedLatMin:{}".format(BufferSchedLatMin))
            print("BufferSchedLatAvg:{}".format(BufferSchedLatAvg))
            print("BufferSchedLatMax:{}".format(BufferSchedLatMax))
            print("BufferSchedLatMissRate10us:{}".format(BufferSchedLatMissRate10us))
            print("BufferSchedLatMissRate15us:{}".format(BufferSchedLatMissRate15us))
            print("BufferSchedLatMissRate20us:{}".format(BufferSchedLatMissRate20us))
            print("BufferSchedLatMissRate30us:{}".format(BufferSchedLatMissRate30us))
            print("LastSchedLatGlobLen:{}".format(LastSchedLatGlobLen))
            print("SchedLatGlobLen:{}".format(SchedLatGlobLen))
            print("SchedLatBufferNum:{}".format(SchedLatBufferNum))
            print("SchedLatMin:{}".format(SchedLatMin))
            print("SchedLatAvg:{}".format(SchedLatAvg))
            print("SchedLatMax:{}".format(SchedLatMax))
            print("SchedLatMissRate10us:{}".format(SchedLatMissRate10us))
            print("SchedLatMissRate15us:{}".format(SchedLatMissRate15us))
            print("SchedLatMissRate20us:{}".format(SchedLatMissRate20us))
            print("SchedLatMissRate30us:{}".format(SchedLatMissRate30us))

        # Real-Time statistic in last N seconds
        ShortTimeSchedLatMin = min(SchedLatSort)
        ShortTimeSchedLatMax = max(SchedLatSort)
        ShortTimeSchedLatAvg = round(sum(SchedLatSort)/len(SchedLatSort), 3)
        lenth=len(SchedLatSort)
        ShortTimeSchedLatMissDeadline10us=[i > 10000 for i in SchedLatSort]
        ShortTimeSchedLatMissRate10us=sum(ShortTimeSchedLatMissDeadline10us)*100/lenth
        ShortTimeSchedLatMissDeadline15us=[i > 15000 for i in SchedLatSort]
        ShortTimeSchedLatMissRate15us=sum(ShortTimeSchedLatMissDeadline15us)*100/lenth
        ShortTimeSchedLatMissDeadline20us=[i > 20000 for i in SchedLatSort]
        ShortTimeSchedLatMissRate20us=sum(ShortTimeSchedLatMissDeadline20us)*100/lenth
        ShortTimeSchedLatMissDeadline30us=[i > 30000 for i in SchedLatSort]
        ShortTimeSchedLatMissRate30us=sum(ShortTimeSchedLatMissDeadline30us)*100/lenth

        if debug:
            print("Min:{} Avg:{} Max:{}".format(ShortTimeSchedLatMin, ShortTimeSchedLatAvg, ShortTimeSchedLatMax))
            print("10us:{} 15us:{} 20us:{}".format(ShortTimeSchedLatMissRate10us, ShortTimeSchedLatMissRate15us, ShortTimeSchedLatMissRate20us))
            
        Dis_all = Counter(SchedLatSort)

        # filter the data whose distribution% < 0.01%
        Dis_all = { k:v for k, v in Dis_all.items() if v/lenth * 100 > 0.01 }
        Dis_all = OrderedDict(sorted(Dis_all.items()))

        # send data stream back
        keys = list(Dis_all.keys())
        vals = list(Dis_all.values())
        ret_len = len(keys)
        dis_data = [{'x': keys[i], 'y': vals[i]/lenth * 100} for i in range(ret_len)]

        if SchedLatQueueLen <= SchedLatHistWinSize:
            sched_ticks = SchedLatQueueLen - 1
        else:
            sched_ticks = SchedLatHistWinSize

        y_vals = SchedLatSort[SchedLatQueueLen - sched_ticks - 1:SchedLatQueueLen - 1]
        his_data = [{'x': i, 'y': y_vals[i-1]} for i in range(1,sched_ticks + 1)]
        text = {'chartPeriod': SchedLatGlobLen/100, 'chartMin': SchedLatMin, 'chartMax':SchedLatMax, 'chartAvg':
        SchedLatAvg }
        data = dumps({'dis': dis_data, 'his': his_data, 'text': text})
        mqttc.publish(topic="cyclic_test", msg=data)

        LastSchedLatGlobLen = SchedLatGlobLen
        LastSchedLatQueueTail = SchedLatQueueTail - 1 if SchedLatQueueTail > 0 else 0

        #if SchedLatQueueLen == 0 and OsTickLatQueueLen == 0:
        #    print("did't get Sched Latency or OS tick Latency data\n");
        #    continue


def parse_result(message, mqttc, debug):
    if not message: return 
    
    global SchedLatGlobLen, SchedLatQueueMax, SchedLatQueue, SchedLatQueueTail, SchedLatQueueLen, SchedLatBufferNum
    string = re.search( r'T:.*', message)
    if string:
        if string.group(0)[0] != 'T':
            return
        RES_b = [int(x) for x in re.findall('\d+', string.group(0))]

        sz = len(RES_b);
        if sz != 9: return

        SchedRES = RES_b

        if SchedLatGlobLen >= SchedLatQueueMax:
            SchedLatQueue[SchedLatQueueTail] = SchedRES[7-1]
        else:
            SchedLatQueue.insert(SchedLatQueueTail, SchedRES[7-1])
        SchedLatQueueLen = SchedLatQueueLen + 1
        if SchedLatQueueLen > SchedLatQueueMax:
            SchedLatQueueLen = SchedLatQueueMax
        SchedLatQueueTail = SchedLatQueueTail + 1
        if SchedLatQueueTail > SchedLatQueueMax - 1:
            SchedLatQueueTail = 0

        SchedLatGlobLen = SchedLatGlobLen + 1
        SchedLatBufferNum = SchedLatBufferNum + 1
        if SchedLatBufferNum >= SchedLatBufferMax:
            generate_report(mqttc, debug)
            SchedLatBufferNum = 0

 
class EventHandler(pyinotify.ProcessEvent):
    def my_init(self, **kargs):
        self.monfile = kargs.get('mon_file')
        self.file_ = open(self.monfile, 'r')
        self.fsize = os.stat(self.monfile).st_size
        # Go to the end of file
        self.file_.seek(0, 2)
        self.queue = kargs.get('queue')
        self.debug = kargs.get('debug')

    def process_IN_MODIFY(self, event):
        if self.monfile not in os.path.join(event.path, event.name):
            return
        curr_fsize = os.stat(self.monfile).st_size
        if curr_fsize < self.fsize:
            # file truncated, adjust the file pointer position
            if self.debug:
                print("Current size: {}, previous size: {}".format(curr_fsize, self.fsize))
            print("file {} has been truncated.".format(self.monfile))
            self.fsize = curr_fsize
            self.file_.seek(curr_fsize)
            return
        else:
            self.fsize = curr_fsize
        print("Modify file:%s." % os.path.join(event.path, event.name))
        self.tail_file()

    def tail_file(self):
        try:
            curr_pos = self.file_.tell()
            lines = self.file_.readlines()
            if not lines:
                self.file_.seek(curr_pos)
            else:
                for line in lines:
                    self.queue.put(line)
        except:
            raise


def main():
    desp = "A client agent on linux to publish cyclic test result."
    parser = argparse.ArgumentParser(description=desp)
    parser.add_argument("monfile", type=str, help="path to the monitored log file")
    parser.add_argument("-d", "--debug", help="print debug messages", action="store_true", dest="debug", default=False)
    parser.add_argument("-s", "--mqtt-host", help="mqtt server hostname or ip address", dest="mqtt_host")
    parser.add_argument("-p", "--mqtt-port", help="mqtt server port", type=int, default=1883, dest="mqtt_port")

    args = parser.parse_args()

    if not os.path.isfile(args.monfile):
        parser.error("The log file does not exist or is inaccesible.")
        sys.exit(1)

    monfile = os.path.abspath(args.monfile)
    if args.debug:
        print("log file path={0}".format(monfile))


    if not args.mqtt_host:
        print("Mqtt host is not given. Use 'localhost' by default.")
        args.mqtt_host = 'localhost'


    try:
        #file_handler = open(monfile, "r")
        mqttc = MqttClient(host=args.mqtt_host, port=args.mqtt_port, name="cyclic", pub_only=True)
        mqttc.start()

        q = queue.Queue()

        wm = pyinotify.WatchManager()
        notifier = pyinotify.ThreadedNotifier(wm, EventHandler(mon_file=monfile, queue=q, debug=args.debug))
        notifier.start()
        wd = wm.add_watch(monfile, pyinotify.IN_MODIFY, rec=False)
        #wm.add_watch(os.path.dirname(monfile), pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO, rec=False)
        print("watching {0} ...".format(monfile))
        
        ln = None
        while True:
            ln = q.get()
            q.task_done()
            parse_result(ln, mqttc, args.debug)    
    finally:
        if notifier: notifier.stop()
        file_handler.close()
        mqttc.disconnect()
    
 
if __name__ == "__main__":
    main()
