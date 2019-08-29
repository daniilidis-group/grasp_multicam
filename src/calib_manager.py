#!/usr/bin/python2
#------------------------------------------------------------------------------
#
# 2019 Bernd Pfrommer
#
# Calibration manager
#
# If the multicam_calibration node runs under the name 'multicam_calibration',
# and you have 4 cameras to calibrate, run it like this:
# 
#     rosrun grasp_multicam calib_manager.py -n multicam_calibration -c 4
#
# Then you can trigger intrinsic calibration of cam3 this way:
#
#    calibrate rosservice call /intrinsic_calibration "camera: 'cam3'"
#


import rospy
import roslib
import argparse
import std_srvs.srv
from grasp_multicam.srv import *
from multicam_calibration.srv import *

FIX_INTRINSICS = 0
FIX_EXTRINSICS = 1
SET_ACTIVE     = 2

param_text = ["FIX_INTRINSICS", "FIX_EXTRINSICS", "SET_ACTIVE"]
all_cameras = None

def do_intrinsics(cam_intrinsic, cams_fixed) :
    set_p(FIX_INTRINSICS, cam_intrinsic, False)
    set_p(FIX_EXTRINSICS, cam_intrinsic, True)
    set_p(SET_ACTIVE,     cam_intrinsic, True)
    for cf in cams_fixed:
        set_p(FIX_INTRINSICS, cf, True)
        set_p(FIX_EXTRINSICS, cf, True)
        set_p(SET_ACTIVE,     cf, False)
    run_cal()

def intrinsic_calibration(req):
    print "--------- doing intrinsic calibration for ", req.camera
    try:
        do_intrinsics(req.camera, list(set(all_cameras) - set([req.camera])))
    except (RuntimeError, Exception),e:
        print "exception: " + str(e)
        return False, str(e)
    return True, "intrinsic calibration finished!"

def extrinsic_calibration(req):
    print "--------- doing extrinsic calibration!"
    try:
        # fix all intrinsics and extrinsics
        for cam in all_cameras:
            set_p(FIX_INTRINSICS, cam, True)
            set_p(FIX_EXTRINSICS, cam, True)
            set_p(SET_ACTIVE, cam, True)
        # now only enable extrinsics for selected camera
        set_p(FIX_EXTRINSICS, req.camera, False)

        # deactivate higher rank cameras
        for idx in range(0, len(all_cameras)):
            if all_cameras[idx] == req.camera:
                for i in range(idx + 1, len(all_cameras)):
                    set_p(SET_ACTIVE,     all_cameras[i], False)
                break
        
        run_cal()

    except (RuntimeError, Exception),e:
        print "exception: " + str(e)
        return False, str(e)
    return True, "extrinsic calibration finished!"


set_calib_param = None
run_calib = None

def set_p(param, cam, val):
    print "setting %-14s for %s to %s" % (param_text[param], cam, "TRUE" if val else "FALSE")
    resp = set_calib_param(param, cam, val)
    if not resp.success:
        raise RuntimeError('cannot set param: %s' % resp.msg)

def run_cal():
    print "running calibration!"
    resp = run_calib()
    if not resp.success:
        raise RuntimeError('calib failed: %s' % resp.message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--node", required=True, help="name of calibration node")
    parser.add_argument("-c", "--num_cameras", type=int, required=True,
                        help="number of cameras")
    args = parser.parse_args()

    all_cameras = ["cam"+str(x) for x in range(args.num_cameras)]
    rospy.init_node('calib_manager')
    print "waiting for calibration service..."
    rospy.wait_for_service(args.node + '/calibration')
    print "waiting for calibration parameter service..."
    rospy.wait_for_service(args.node + '/set_parameter')
    run_calib = rospy.ServiceProxy(args.node + '/calibration',
                                   std_srvs.srv.Trigger)
    set_calib_param = rospy.ServiceProxy(args.node + '/set_parameter',
                                         ParameterCmd)
    print "found calibration services!"

    i = rospy.Service('intrinsic_calibration',
                      Calibrate, intrinsic_calibration)
    e = rospy.Service('extrinsic_calibration',
                      Calibrate, extrinsic_calibration)
    print "calibration manager running ..."
    rospy.spin()
