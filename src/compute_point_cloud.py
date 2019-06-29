#!/usr/bin/env python
#
# compute point cloud from depth image for monstar images
#
#

import rospy
import argparse
import yaml
import cv2
import time
import copy
import struct
import math
import make_caminfo_msg

from math import isnan
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import sensor_msgs.msg
from rosbag import Bag
from collections import defaultdict
from point_cloud_adjuster import PointCloudAdjuster

def read_yaml(filename):
    with open(filename, 'r') as y:
        try:
            return yaml.load(y)
        except yaml.YAMLError as e:
            print(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='compute point cloud from depth image.')
    parser.add_argument('--camera_info', '-i', action='store', required=True,
                        help='name of camerainfo file.')
    parser.add_argument(
        '--sensor_topic', '-n', action='store', default='/rig/monstar',
        help='name of depth sensor topic.')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')

    parser.add_argument('bagfile')

    args = parser.parse_args()

    rospy.init_node('compute_point_cloud')
    depth_topic  = args.sensor_topic + '/image_depth'
    points_topic = args.sensor_topic + '/points'
    camera_info  = make_caminfo_msg.from_ros(read_yaml(args.camera_info))
    adj = PointCloudAdjuster(camera_info)

    
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold \
                  if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            t0 = time.time()
            start_time = inbag.get_start_time()
            end_time   = inbag.get_end_time()
            total_time = end_time - start_time
            time_to_data = defaultdict(dict)
            last_percent = 0
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages():
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) \
                                / percent_done
                    print ("percent done: %5.0f, expected time " + \
                        "remaining: %5.0fs") % (percent_done, time_left)
                if topic == depth_topic:
                    outbag.write(topic, msg, t) # write depth image
                    time_to_data[msg.header.stamp][topic] = msg
                elif topic == points_topic:
#                    outbag.write(topic, msg, t) # write original points
                    time_to_data[msg.header.stamp][topic] = msg
                else:
                    outbag.write(topic, msg, t)
                if len(time_to_data[msg.header.stamp]) == 2:
                    points_msg = adj.adjust(
                        time_to_data[msg.header.stamp][depth_topic],
                        time_to_data[msg.header.stamp][points_topic])

                    outbag.write(points_topic, points_msg, t)
                    time_to_data.pop(msg.header.stamp)
                if rospy.is_shutdown():
                    break
                    
        outbag.close()
                    
