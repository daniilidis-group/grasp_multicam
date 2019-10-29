# Notes

## OVC bags
How to standardize:

    bag=dupont_2018-11-09-11-34-55
    rosrun grasp_multicam standardize_bag_ovc.py -c 10000000 --outbag ${bag}_normed.bag ${bag}.bag

For some older bags, you need to fix the header time stamp or the time, and specify astra as the depth sensor:

    rosrun grasp_multicam standardize_bag_ovc.py -c 10000000 -m True -d astra --outbag ${bag}_normed.bag ${bag}.bag

How to compute odometry and record it:

    bag=dupont_2018-11-09-11-34-55
	roslaunch grasp_multicam vio_ovc.launch
    rosbag record -O ./${bag}_odom.bag -e "/vio/odom|/tf"

How to play bag fast

    rosrun flow_controlled_player player.py --ack_subject /vio/odom --ack_type nav_msgs.msg.Odometry --buffer_time 0.5 --timeout 2.0  `pwd`/${bag}_normed.bag

How to extract tags:

    roslaunch grasp_multicam sync_and_detect_ovc.launch bag:=`pwd`/${bag}_normed.bag
	mv ${bag}_normed.bag_output.bag ${bag}_tags.bag
	
Merge bags:

    rosrun grasp_multicam merge_bags.py ${bag}_odom.bag ${bag}_tags.bag --outbag ${bag}_tags_and_odom.bag
	ln -s ${bag}_tags_and_odom.bag tag_detections.bag

How to get camera poses from calibration:

    rosrun tagslam kalibr_to_camera_poses.py --calib calib.yaml 

How to run tagslam:

    roslaunch grasp_multicam tagslam.launch > out.txt


Static transform for generating image:

    rosrun tf static_transform_publisher 25 -1.1566 -0.8389 -1.570796327 0 0 vision map 1000

Second run, for aligining vio

    rosrun tf static_transform_publisher -1.12625 0.4480 0.832 1.605 0 0 map vision 1000
	
For aligning orbslam

    rosrun tf static_transform_publisher -1.12625 0.4480 0.832 0.072 -0.25 0 map orbslam2_world 1000

How to create video:

In rviz, load ``ovc_map_pointcloud.rviz``, then:

    rosrun grasp_multicam  publish_calibration_tf.py --calib `rospack find grasp_multicam`/current/calib.yaml --id_map `rospack find grasp_multicam`/current/topic_to_frame_id.yaml --frame_ids monstar
    roslaunch grasp_multicam undistort_left_ovc.launch
	roslaunch grasp_multicam transform_point_cloud.launch

If only odom is available, use this:

	rosrun grasp_multicam  publish_calibration_tf.py --calib `rospack find grasp_multicam`/current/calib.yaml --id_map `rospack find grasp_multicam`/current/topic_to_frame_id.yaml --frame_ids monstar ovc/cam_0 ovc/cam_1
	
How the calibration was adusted for 2018-11-08: Run on the
sequence with standard camera_poses.yaml, but R = 1000, and set in tagslam.yaml:

     odom_acceleration_noise_min: 50.0
     odom_acceleration_noise_max: 70.0
     odom_angular_acceleration_noise_min: 50.0
     odom_angular_acceleration_noise_max: 70.0

This will put very little weight on the odometry. Then change R back
to 1e6, and run full tagslam. Also transfer camera calibration (it's
actually already under ~/.ros/) to adjusted camera calibration.
Then re-run the odom with the adjusted camera calibration, and re-run
tagslam with the adjusted odom!



How to adjust camerainfo on ovc or falcam bags:

    rosrun grasp_multicam add_camerainfo.py --calib `pwd`/calib.yaml --id_map `pwd`/topic_to_frame_id.yaml --outbag ${bag}_good_camerainfo.bag ${bag}_normed.bag

How to adjust pointcloud on ovc or falcam bags:

    rosrun grasp_multicam adjust_pointcloud.py --calib `pwd`/calib.yaml --id_map `pwd`/topic_to_frame_id.yaml --outbag ${bag}_adjusted_pc.bag ${bag}_good_camerainfo.bag




## Falcam bags

How to standardize a falcam bag:

    ./standardize_bag_falcam.py --calib ../current/calibration/falcam_rig.yaml -o ../current/foo.bag ../current/2018-01-16-14-41-13_levine_bumpspace.bag

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


