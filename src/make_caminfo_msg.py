#!/usr/bin/env python
#
# compute point cloud from depth image for monstar images
#
#

import rospy
import sensor_msgs.msg

def from_ros(c):
    m = sensor_msgs.msg.CameraInfo()
    m.height = c['image_height']
    m.width = c['image_width']
    m.distortion_model = c['distortion_model']
    m.D = c['distortion_coefficients']['data']
    m.K = c['camera_matrix']['data']
    m.R = c['rectification_matrix']['data']
    m.P = c['projection_matrix']['data']
    return m

def from_kalibr(c):
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
