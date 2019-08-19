#!/usr/bin/env python
#------------------------------------------------------------------------------
# publish static transforms
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
from tf2_msgs.msg import TFMessage
import time
import make_caminfo_msg

import read_calib

from rosbag import Bag

def modify_time_stamp(t, tfm):
    for tf in tfm.transforms:
        tf.header.stamp = t
        tf.header.seq = 0
    return (tfm)

def filter_transforms(tfm, keep_topics):
    tff = copy.copy(tfm)
    tff.transforms = []
    print keep_topics
    for tf in tfm.transforms:
        if tf.child_frame_id in keep_topics:
            print 'publishing tf: %s -> %s' % (tf.header.frame_id, tf.child_frame_id)
            tff.transforms.append(tf)
    return (tff)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='publish calibration as transform')
    parser.add_argument(
        '--calib',  action='store', default=None, required=True,
        help='name of calibration file')
    parser.add_argument(
        '--id_map',  action='store', default=None, required=True,
        help='name of topic_to_id yaml file')
    parser.add_argument(
        '--rate',  action='store', default=200.0, required=False, type=float,
        help='rate [in Hz] at which to publish')
    parser.add_argument(
        '--frame_ids', '-f',  nargs='+', action='store', default=None, required=True,
        help='publish only these child ids (list without separator)')

    args = parser.parse_args()

    topic_to_id_map = read_calib.read_yaml(args.id_map)
    static_transforms, camera_infos = read_calib.read_calib(
        args.calib, topic_to_id_map)
    tfs = filter_transforms(static_transforms, args.frame_ids)
    
    rospy.init_node('publish_calibration_tf')
    pub  = rospy.Publisher('/tf', TFMessage, queue_size=10)
    rate = rospy.Rate(args.rate)
    while not rospy.is_shutdown():
        tf_msg = modify_time_stamp(rospy.get_rostime(), tfs)
        pub.publish(tf_msg)
        try:
            rate.sleep()
        except rospy.exceptions.ROSTimeMovedBackwardsException as e:
            rospy.logwarn('time moved backwards, restarting')
            rate = rospy.Rate(args.rate)
