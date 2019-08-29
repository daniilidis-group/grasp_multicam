#!/usr/bin/env python
#------------------------------------------------------------------------------
# process raw falcam bag to standard form
#
# 2019 Bernd Pfrommer

import rospy
import argparse
import copy
import yaml
import re
import numpy as np
import geometry_msgs
import sensor_msgs
import tf2_msgs
import time
import make_caminfo_msg
import read_calib

from tf.transformations import *
from rosbag import Bag
from collections import defaultdict
from point_cloud_adjuster import PointCloudAdjuster


topic_map = {
    '/rig/monstar/camera_info':        {'name': '/monstar/camera_info'},
    '/rig/monstar/image_depth':        {'name': '/monstar/image_depth'},
    '/rig/monstar/image_mono8':        {'name': '/monstar/image_mono8'},
    '/rig/monstar/image_noise':        {'name': '/monstar/image_noise'},
    '/rig/monstar/points':             {'name': '/monstar/points'},

    '/rig/imu':                        {'name': '/falcam/imu'},
    '/rig/left/image_mono':            {'name': '/falcam/cam_0/image_raw'},
    '/rig/left/camera_info':           {'name': '/falcam/cam_0/camera_info'},
    '/rig/right/image_mono':           {'name': '/falcam/cam_1/image_raw'},
    '/rig/right/camera_info':          {'name': '/falcam/cam_1/camera_info'},
    
    '/rig/pg_color/camera_info':       {'name': '/color_camera/camera_info'},
    '/rig/pg_color/image_raw':         {'name': '/color_camera/image_raw'},
}

mapped_topics = topic_map.keys()

frame_id_map = {
    'falcam_left':   'falcam/cam_0',
    'falcam_right':  'falcam/cam_1',
    'rig/monstar_optical_frame': 'monstar',
    'imu':           'falcam/imu',
    'pg_color':      'color_camera',
    'odom':          'online/vio_odom',
    'vision':        'vision',
}

def replace_camera_info(topic, msg, camera_infos):
    mmsg = camera_infos[topic]
    mmsg.header = msg.header
    return mmsg



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Turn bag into standard form.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument(
        '--calib',  action='store', default=None, required=True,
        help='name of calibration file')
    parser.add_argument(
        '--id_map',  action='store', default=None, required=True,
        help='name of topic_to_id yaml file')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    topic_to_id_map = read_calib.read_yaml(args.id_map)
    static_transforms, camera_infos = read_calib.read_calib(
        args.calib, topic_to_id_map)
    adjuster = PointCloudAdjuster(camera_infos['/monstar/camera_info'])
    
    rospy.init_node('standardize_bag')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            time_to_data = defaultdict(dict)
            last_percent = 0
            t0 = time.time()
            start_time = inbag.get_start_time()
            end_time   = inbag.get_end_time()
            total_time = end_time - start_time
            first_time = True
            depth_topic  = '/monstar/image_depth'
            points_topic = '/monstar/points'
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages():
                percent_done = (t.to_sec() - start_time)/total_time * 100
                if (percent_done - last_percent > 5.0):
                    last_percent = percent_done
                    t1 = time.time()
                    time_left = (100 - percent_done) * (t1-t0) / percent_done
                    print "done: %5.0f%%, expected time remaining: %5.0fs" % (
                        percent_done, time_left)
                #
                # remap topics
                #
                if topic not in mapped_topics:
                    continue
                t_mapped = topic_map[topic]['name']
                #
                # remap frame ids
                #
                if hasattr(msg, 'header'):
                    if msg.header.frame_id in frame_id_map:
                        msg.header.frame_id = frame_id_map[msg.header.frame_id]
                    else:
                        print "UNKNOWN FRAME ID:"
                        print msg
                #
                # replace camera_info
                #
                if t_mapped in camera_infos:
                    msg = replace_camera_info(t_mapped, msg, camera_infos)
                #
                # write to bag
                #
                if topic == depth_topic:
                    time_to_data[msg.header.stamp][t_mapped] = msg
                    outbag.write(t_mapped, msg, t) # can write immediately
                elif topic == points_topic:
                    time_to_data[msg.header.stamp][t_mapped] = msg
                    # don't write, need to wait for depth image and point cloud
                    #outbag.write(t_mapped, msg, t)
                else:
                    outbag.write(t_mapped, msg, t)
                #
                # write adjusted point cloud to bag
                #
                if hasattr(msg, 'header') and len(
                        time_to_data[msg.header.stamp]) == 2:
                    msg = adjuster.adjust(
                        time_to_data[msg.header.stamp][depth_topic],
                        time_to_data[msg.header.stamp][points_topic])
                    # write adjusted points
                    outbag.write(points_topic, msg, t)
                    time_to_data.pop(msg.header.stamp)
                if rospy.is_shutdown():
                    break

        outbag.close()
                    
