#!/usr/bin/env python
#------------------------------------------------------------------------------
# read calibration files
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

from tf.transformations import *
from fnmatch import fnmatchcase

def read_yaml(filename):
    with open(filename, 'r') as y:
        try:
            return yaml.load(y)
        except yaml.YAMLError as e:
            print(e)

def matrix_to_tf(T):
    q  = quaternion_from_matrix(T)
    tf = geometry_msgs.msg.Transform()
    tf.translation.x = T[0,3]
    tf.translation.y = T[1,3]
    tf.translation.z = T[2,3]
    tf.rotation.x = q[0]
    tf.rotation.y = q[1]
    tf.rotation.z = q[2]
    tf.rotation.w = q[3]
    return tf
    
def prev_cam_name(name):
    match = re.match(r"([a-z]+)([0-9]+)", name, re.I)
    if match:
        items = match.groups()
    return ("%s%d" % (items[0], int(items[1]) - 1))

def img_to_caminfo_topic(img_topic):
    r1 = img_topic.replace('/image_mono8','/camera_info')
    r2 = r1.replace('/image_raw','/camera_info')
    r3 = r2.replace('/image_mono','/camera_info')
    return r3

def build_frame_id_map(c, topic_to_frame_id):
    m = {}
    for i in c.items():
        name, cam = i[0], i[1]
        if name == 'T_imu_body':
            continue
        print cam
        m[name] = topic_to_frame_id[cam['rostopic']]
    # special entry for camera 0
    m['cam-1'] = topic_to_frame_id['IMU_FRAME']
    return m

def read_calib(fname, topic_to_frame_id):
    c = read_yaml(fname)
    static_transforms = []
    msg = tf2_msgs.msg.TFMessage()
    frame_id_map = build_frame_id_map(c, topic_to_frame_id)
    caminfos = {}
    for i in c.items():
        name, cam = i[0], i[1]
        if name == 'T_imu_body':
            continue
        tf = cam['T_cam_imu'] if name == 'cam0' else cam['T_cn_cnm1']
        T = np.linalg.inv(np.asarray(tf))
        tfm = geometry_msgs.msg.TransformStamped()
        tfm.header.frame_id = frame_id_map[prev_cam_name(name)]
        tfm.child_frame_id  = frame_id_map[name]
        tfm.transform = matrix_to_tf(T)
        msg.transforms.append(tfm)
        ci = make_caminfo_msg.from_kalibr(cam)
        caminfos[img_to_caminfo_topic(cam['rostopic'])] = ci
    return msg, caminfos
