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

from tf.transformations import *
from fnmatch import fnmatchcase
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

topic_to_frame_id = {
    '/rig/left/image_mono': 'falcam/cam_0',
    '/rig/right/image_mono': 'falcam/cam_1',
    '/rig/right/image_mono': 'falcam/cam_1',
    '/rig/pg_color/image_raw': 'color_camera',
    '/rig/monstar/image_mono8': 'monstar',
    '/rig/imu':                 'falcam/imu'
}

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
    
def build_frame_id_map(c):
    m = {}
    for i in c.items():
        name, cam = i[0], i[1]
        if name == 'T_imu_body':
            continue
        m[name] = topic_to_frame_id[cam['rostopic']]
    # special entry for camera 0
    m['cam-1'] = topic_to_frame_id['/rig/imu']
    return m

def prev_cam_name(name):
    match = re.match(r"([a-z]+)([0-9]+)", name, re.I)
    if match:
        items = match.groups()
    return ("%s%d" % (items[0], int(items[1]) - 1))

def make_caminfo_msg(c):
    m = sensor_msgs.msg.CameraInfo()
    m.height = c['resolution'][1]
    m.width  = c['resolution'][0]
    m.distortion_model = c['distortion_model']
    m.D = c['distortion_coeffs']
    K   = c['intrinsics']
    m.K = [K[0], 0.0,  K[2], 0.0,  K[1], K[3], 0.0,  0.0, 1.0]
    m.R = [1.000000, 0.000000, 0.000000,
           0.000000, 1.000000, 0.000000,
           0.000000, 0.000000, 1.000000]
    m.P = m.K[0:3] + [0.0] + m.K[3:6] + [0.0] + m.K[6:9] + [0.0]
    return m

def img_to_caminfo_topic(img_topic):
    r1 = img_topic.replace('/image_mono8','/camera_info')
    r2 = r1.replace('/image_raw','/camera_info')
    r3 = r2.replace('/image_mono','/camera_info')
    return r3
    

def read_calib(fname, point_cloud_camera_topic):
    c = read_yaml(fname)
    static_transforms = []
    msg = tf2_msgs.msg.TFMessage()
    frame_id_map = build_frame_id_map(c)
    caminfos = {}
    adj = None
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
        ci = make_caminfo_msg(cam)
        caminfos[img_to_caminfo_topic(cam['rostopic'])] = ci
        if cam['rostopic'] == point_cloud_camera_topic:
            adj = PointCloudAdjuster(ci)
    if adj == None:
        print 'WARNING: no camera_info topic found for ', point_cloud_camera_topic
    return msg, caminfos, adj

def make_static_tf_msg(t, tfm):
    for tf in tfm.transforms:
        tf.header.stamp = t
        tf.header.seq = 0
    return (tfm)

def replace_camera_info(topic, msg, camera_infos):
    mmsg = camera_infos[topic]
    mmsg.header = msg.header
    return mmsg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Turn bag into standard form.')
    parser.add_argument(
        '--start', '-s', action='store', default=0.0, type=float,
        help='Rostime (bag time, large number!) representing start time.')
    parser.add_argument(
        '--end', '-e', action='store', default=1e60, type=float,
        help='Rostime (bag time, large number!) representing stop time.')
    parser.add_argument(
        '--chunk_threshold', '-c', action='store', default=None, type=int,
        help='chunk threshold in bytes.')
    parser.add_argument(
        '--calib',  action='store', default=None, required=True,
        help='name of calibration file')
    parser.add_argument(
        '--depth_sensor',  action='store', default='/rig/monstar',
        help='ros name of depth sensor, e.g. /rig/monstar')
    parser.add_argument(
        '--outbag', '-o', action='store', default=None, required=True,
        help='name of output bag.')
    parser.add_argument('bagfile')

    args = parser.parse_args()

    points_cinfo_topic = args.depth_sensor + '/image_mono8'
    static_transforms, camera_infos, adjuster = read_calib(
        args.calib, points_cinfo_topic)
    
    rospy.init_node('standardize_bag')
    with Bag(args.bagfile, 'r') as inbag:
        cthresh = args.chunk_threshold if args.chunk_threshold else inbag.chunk_threshold
        print "using chunk threshold: ", cthresh
        with Bag(args.outbag, mode='w', chunk_threshold=cthresh) as outbag:
            time_to_data = defaultdict(dict)
            last_percent = 0
            t0 = time.time()
            start_time = max([inbag.get_start_time(), args.start])
            end_time   = min([inbag.get_end_time(), args.end])
            total_time = end_time - start_time
            first_time = True
            depth_topic  = args.depth_sensor + '/image_depth'
            points_topic = args.depth_sensor + '/points'
            print "total time span to be processed: %.2fs" % total_time
            for topic, msg, t in inbag.read_messages(
                    start_time=rospy.Time(args.start),
                    end_time=rospy.Time(args.end)):
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
                if topic in camera_infos:
                    msg = replace_camera_info(topic, msg, camera_infos)
                #
                # write to bag
                #
                if topic == depth_topic:
                    time_to_data[msg.header.stamp][topic] = msg
                    outbag.write(t_mapped, msg, t) # can write immediately
                elif topic == points_topic:
                    time_to_data[msg.header.stamp][topic] = msg
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
                    outbag.write(topic_map[points_topic]['name'], msg, t)
                    time_to_data.pop(msg.header.stamp)
                #
                # add static tf
                #
                if first_time:
                    first_time = False
                    static_tf_msg = make_static_tf_msg(t, static_transforms)
                    outbag.write('/tf_static', static_tf_msg, t)

        outbag.close()
                    
