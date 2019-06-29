#!/usr/bin/env python
#------------------------------------------------------------------------------
# adjust point cloud according to new camerainfo
#
# 2019 Bernd Pfrommer
#

import rospy
import cv2
import copy
import struct
import math
from math import isnan
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import sensor_msgs.msg
from image_geometry import PinholeCameraModel


class PointCloudAdjuster:
    def __init__(self, camera_info_msg):
        self.camera_info = camera_info_msg
        self.make_pixel_to_3d()
        self.bridge = CvBridge()
        
    def make_pixel_to_3d(self):
        cm = PinholeCameraModel()
        cm.fromCameraInfo(self.camera_info)
        self.p3d = np.zeros([self.camera_info.height,
                             self.camera_info.width, 3])
        for v in range(0, self.camera_info.height):
            for u in range(0, self.camera_info.width):
                uv_rect    = cm.rectifyPoint((u, v))
                p = cm.projectPixelTo3dRay(uv_rect)
                self.p3d[v,u,:] = (p[0]/p[2],p[1]/p[2], 1.0) # make homogeneous

    def adjust(self, depth_image, orig_points):
        pointMsg = copy.copy(orig_points)
        data = bytearray(pointMsg.data)
        try:
            d = self.bridge.imgmsg_to_cv2(depth_image,
                                          desired_encoding="passthrough")
            de = np.expand_dims(d, axis=2)
            # multiply depth with homogeneous vector to get 3d point
            dm = (de * self.p3d).astype('float32')
            for v in range(0, dm.shape[0]):
                for u in range(0, dm.shape[1]):
                    p = dm[v,u,:]
                    idx = v * pointMsg.row_step + u * pointMsg.point_step
                    x = struct.unpack_from('fff', data, idx)
                    if not (isnan(x[0]) or isnan(x[1]) or isnan(x[2])):
                        struct.pack_into('fff', data, idx, p[0], p[1], p[2])
            pointMsg.data = str(data)
        except CvBridgeError as e:
            print e
        return pointMsg

