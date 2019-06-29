# Notes

How to standardize a ovc bag:

    rosrun grasp_multicam standardize_bag_ovc.py -c 10000000 --outbag dupont_2018-11-09-11-00-28_short_corridor_1m_drift_standardized.bag dupont_2018-11-09-11-00-28_short_corridor_1m_drift.bag

How to standardize a falcam bag:

    ./standardize_bag_falcam.py --calib ../current/calibration/falcam_rig.yaml -o ../current/foo.bag ../current/2018-01-16-14-41-13_levine_bumpspace.ba

How to play bag fast:

    rosrun flow_controlled_player player.py --ack_subject /vio/odom --ack_type nav_msgs.msg.Odometry --buffer_time 0.5 --timeout 2.0  ../data/falcam/2018-01-16/levine_bumpspace/2018-01-16-14-41-13_levine_bumpspace.bag 

How to record odom:

    rosbag record -O ../data/falcam/2018-01-16/levine_bumpspace/2018-01-16-14-41-13_levine_bumpspace-odom-slow.bag -e "/vio/odom|/tf|/vio/left|/vio/feature_point_cloud"


How to run calibration:

    [play cam0 intrinsic bag]
    rosservice call /intrinsic_calibration "camera: 'cam0'"
    [play cam1 intrinsic bag]
    rosservice call /intrinsic_calibration "camera: 'cam1'"
    [play cam2 intrinsic bag]
    rosservice call /intrinsic_calibration "camera: 'cam2'"
    [play cam3 intrinsic bag]
    rosservice call /intrinsic_calibration "camera: 'cam3'"
	[play extrinsic calibration bag]
    rosservice call /extrinsic_calibration "camera: 'cam1'"
    rosservice call /extrinsic_calibration "camera: 'cam2'"
    rosservice call /extrinsic_calibration "camera: 'cam3'"
